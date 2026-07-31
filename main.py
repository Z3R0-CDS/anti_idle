import customtkinter as ctk
import pystray
from PIL import Image, ImageDraw
import threading
import sys
from datetime import datetime
from tkcalendar import DateEntry
from engine import AntiIdleEngine
from config import ConfigManager

class AntiIdleApp(ctk.CTk):
    def __init__(self, engine, config):
        super().__init__()
        self.engine = engine
        self.config = config

        self.title("Anti-Idle Pro")
        self.geometry("650x750")
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Main Scrollable Container
        self.main_container = ctk.CTkScrollableFrame(self)
        self.main_container.pack(pady=10, padx=10, fill="both", expand=True)

        # --- Status Section ---
        self.status_frame = ctk.CTkFrame(self.main_container)
        self.status_frame.pack(pady=10, padx=10, fill="x")
        
        self.label = ctk.CTkLabel(self.status_frame, text="Anti-Idle Management", font=("Roboto", 22, "bold"))
        self.label.pack(pady=10)

        self.status_indicator = ctk.CTkLabel(self.status_frame, text="", font=("Roboto", 16))
        self.status_indicator.pack(pady=5)
        
        self.btn_frame = ctk.CTkFrame(self.status_frame, fg_color="transparent")
        self.btn_frame.pack(pady=10)
        
        self.toggle_btn = ctk.CTkButton(self.btn_frame, text="Toggle Run", command=self.toggle_engine, width=120)
        self.toggle_btn.grid(row=0, column=0, padx=5)
        
        self.pause_btn = ctk.CTkButton(self.btn_frame, text="Toggle Pause", command=self.toggle_pause, width=120)
        self.pause_btn.grid(row=0, column=1, padx=5)

        # --- Global Settings ---
        self.settings_frame = ctk.CTkFrame(self.main_container)
        self.settings_frame.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(self.settings_frame, text="Global Settings", font=("Roboto", 16, "bold")).pack(pady=5)
        
        self.webhook_entry = ctk.CTkEntry(self.settings_frame, placeholder_text="Discord Webhook URL", width=400)
        self.webhook_entry.pack(pady=10)
        self.webhook_entry.insert(0, self.config.get("webhook_url", ""))
        self.webhook_entry.bind("<FocusOut>", self.update_webhook)

        # --- Run Mode Selection ---
        self.mode_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        self.mode_frame.pack(pady=10)
        
        self.run_mode_var = ctk.StringVar(value=self.config.get("run_mode", "infinite"))
        modes = [("Infinite", "infinite"), ("Schedule", "schedule"), ("One-Time", "onetime")]
        for text, mode in modes:
            rb = ctk.CTkRadioButton(self.mode_frame, text=text, variable=self.run_mode_var, value=mode, command=self.update_run_mode)
            rb.pack(side="left", padx=10)

        # --- Weekly Schedule ---
        self.sched_frame = ctk.CTkFrame(self.main_container)
        self.sched_frame.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(self.sched_frame, text="Weekly Schedule (HH:MM)", font=("Roboto", 16, "bold")).pack(pady=5)
        
        self.day_grid = ctk.CTkFrame(self.sched_frame, fg_color="transparent")
        self.day_grid.pack(pady=5)
        
        self.day_entries = {}
        weekly_data = self.config.get("weekly_schedule", {})
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for i, day in enumerate(days):
            f = ctk.CTkFrame(self.day_grid, fg_color="transparent")
            f.pack(side="left", padx=5)
            ctk.CTkLabel(f, text=day[:3], font=("Roboto", 10)).pack()
            
            s_ent = ctk.CTkEntry(f, width=50)
            s_ent.insert(0, weekly_data.get(day, {}).get("start", "off"))
            s_ent.pack()
            
            e_ent = ctk.CTkEntry(f, width=50)
            e_ent.insert(0, weekly_data.get(day, {}).get("end", "off"))
            e_ent.pack()
            
            self.day_entries[day] = (s_ent, e_ent)

        self.save_sched_btn = ctk.CTkButton(self.sched_frame, text="Save Weekly Schedule & Notify", command=self.save_weekly_schedule)
        self.save_sched_btn.pack(pady=10)

        # --- One-Time Window ---
        self.ot_frame = ctk.CTkFrame(self.main_container)
        self.ot_frame.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(self.ot_frame, text="One-Time Window", font=("Roboto", 16, "bold")).pack(pady=5)
        
        self.ot_lock_var = ctk.BooleanVar(value=self.config.get("ot_locked", False))
        self.ot_lock_cb = ctk.CTkCheckBox(self.ot_frame, text="Lock Window (Prevent Auto-Update)", variable=self.ot_lock_var, command=self.update_ot_lock)
        self.ot_lock_cb.pack(pady=5)

        self.ot_inputs = ctk.CTkFrame(self.ot_frame, fg_color="transparent")
        self.ot_inputs.pack(pady=5)
        
        # Using tkcalendar DateEntry
        self.ot_start_date = DateEntry(self.ot_inputs, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.ot_start_date.grid(row=0, column=0, padx=5)
        
        self.ot_start_time = ctk.CTkEntry(self.ot_inputs, width=60)
        self.ot_start_time.insert(0, "00:00")
        self.ot_start_time.grid(row=0, column=1, padx=5)
        
        self.ot_end_date = DateEntry(self.ot_inputs, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.ot_end_date.grid(row=0, column=2, padx=5)
        
        self.ot_end_time = ctk.CTkEntry(self.ot_inputs, width=60)
        self.ot_end_time.insert(0, "23:59")
        self.ot_end_time.grid(row=0, column=3, padx=5)

        self.save_ot_btn = ctk.CTkButton(self.ot_frame, text="Save One-Time Window", command=self.save_one_time_window)
        self.save_ot_btn.pack(pady=10)

        self.protocol('WM_DELETE_WINDOW', self.hide_window)
        self.update_status_ui()

    def update_status_ui(self):
        # Update state visibility
        running = self.engine.is_running
        paused = self.engine.is_paused
        
        status_text = "Status: STOPPED"
        color = "red"
        
        if running:
            status_text = "Status: RUNNING"
            color = "green"
            if paused:
                status_text = "Status: PAUSED"
                color = "orange"
        
        self.status_indicator.configure(text=status_text, text_color=color)
        self.toggle_btn.configure(text="Stop" if running else "Start")
        self.pause_btn.configure(text="Resume" if paused else "Pause")
        
        # The UI needs to refresh this periodically as the engine changes state via schedule
        self.after(1000, self.update_status_ui)

    def update_webhook(self, event=None):
        url = self.webhook_entry.get()
        self.config.set("webhook_url", url)

    def update_run_mode(self):
        mode = self.run_mode_var.get()
        self.config.set("run_mode", mode)

    def update_ot_lock(self):
        self.config.set("ot_locked", self.ot_lock_var.get())

    def save_weekly_schedule(self):
        new_sched = {}
        for day, (s_ent, e_ent) in self.day_entries.items():
            new_sched[day] = {"start": s_ent.get(), "end": e_ent.get()}
        self.config.set("weekly_schedule", new_sched)
        
        # Create Rich Embed for Discord
        embed = {
            "title": "📅 Updated Weekly Schedule",
            "color": 3447003, # Blue
            "fields": []
        }
        for day, sched in new_sched.items():
            status = f"{sched['start']} - {sched['end']}" if sched['start'] != "off" else "Off"
            embed["fields"].append({"name": day, "value": status, "inline": True})
        
        self.engine.send_notification("Weekly schedule updated!", embed_data=embed)
        self.save_sched_btn.configure(text="Saved!", fg_color="green")
        self.after(2000, lambda: self.save_sched_btn.configure(text="Save Weekly Schedule & Notify", fg_color=["#3a7ebf", "#1f538d"]))

    def save_one_time_window(self):
        start_dt = f"{self.ot_start_date.get_date().strftime('%Y-%m-%d')} {self.ot_start_time.get()}"
        end_dt = f"{self.ot_end_date.get_date().strftime('%Y-%m-%d')} {self.ot_end_time.get()}"
        self.config.set("one_time_window", {"start": start_dt, "end": end_dt})
        self.save_ot_btn.configure(text="Saved!", fg_color="green")
        self.after(2000, lambda: self.save_ot_btn.configure(text="Save One-Time Window", fg_color=["#3a7ebf", "#1f538d"]))

    def toggle_engine(self):
        new_state = not self.engine.is_running
        self.engine.toggle_running(new_state, trigger="User")
        self.update_status_ui()

    def toggle_pause(self):
        new_state = not self.engine.is_paused
        self.engine.toggle_paused(new_state, trigger="User")
        self.update_status_ui()

    def hide_window(self):
        self.withdraw()

    def show_window(self):
        self.deiconify()

def create_tray_icon(app):
    width, height = 64, 64
    image = Image.new('RGB', (width, height), color=(30, 144, 255))
    dc = ImageDraw.Draw(image)
    dc.rectangle([16, 16, 48, 48], fill=(255, 255, 255))
    
    menu = pystray.Menu(
        pystray.MenuItem('Show Settings', lambda: app.show_window()),
        pystray.MenuItem('Exit', lambda: exit_app())
    )
    
    icon = pystray.Icon("anti_idle", image, "Anti-Idle Pro", "anti_idle", menu)
    icon.run()

def exit_app():
    sys.exit(0)

if __name__ == "__main__":
    config = ConfigManager()
    engine = AntiIdleEngine(config)
    engine.start()
    
    app = AntiIdleApp(engine, config)
    
    tray_thread = threading.Thread(target=create_tray_icon, args=(app,), daemon=True)
    tray_thread.start()
    
    app.mainloop()
