import pyautogui
import time
import threading
from pynput import mouse, keyboard
import requests
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AntiIdleEngine:
    def __init__(self, config_manager):
        self.config = config_manager
        self.is_running = self.config.get("is_running", False)
        self.is_paused = self.config.get("is_paused", False)
        self.last_activity_time = time.time()
        
        self.mouse_listener = mouse.Listener(on_move=self._on_activity, on_click=self._on_activity, on_scroll=self._on_activity)
        self.key_listener = keyboard.Listener(on_press=self._on_activity)
        
        self.mouse_listener.start()
        self.key_listener.start()

    def _on_activity(self, *args):
        self.last_activity_time = time.time()

    def send_notification(self, message, embed_data=None):
        webhook_url = self.config.get("webhook_url")
        if not webhook_url:
            return
            
        try:
            payload = {}
            if embed_data:
                payload["embeds"] = [embed_data]
            else:
                payload["content"] = f"🚀 **Anti-Idle Server Update**: {message}"
            
            requests.post(webhook_url, json=payload, timeout=5, verify=False)
        except Exception as e:
            logging.error(f"Failed to send Discord notification: {e}")

    def toggle_running(self, state: bool, trigger="User"):
        self.is_running = state
        self.config.set("is_running", state)
        status = "started" if state else "stopped"
        logging.info(f"Anti-Idle engine {status} by {trigger}")
        self.send_notification(f"Engine has been {status} by {trigger}.")

    def toggle_paused(self, state: bool, trigger="User"):
        self.is_paused = state
        self.config.set("is_paused", state)
        status = "paused" if state else "resumed"
        logging.info(f"Anti-Idle engine {status} by {trigger}")
        self.send_notification(f"Engine has been {status} by {trigger}.")

    def _is_in_schedule(self):
        mode = self.config.get("run_mode", "infinite") # infinite, schedule, onetime
        
        if mode == "infinite":
            return True, "Infinite Mode"
            
        now = datetime.now()
        current_day = now.strftime("%A")
        current_time = now.strftime("%H:%M")
        
        if mode == "schedule":
            weekly = self.config.get("weekly_schedule", {})
            day_sched = weekly.get(current_day, {"start": "off", "end": "off"})
            start = day_sched.get("start")
            end = day_sched.get("end")
            if start != "off" and end != "off" and start <= current_time <= end:
                return True, "Weekly Schedule"
        
        elif mode == "onetime":
            one_time = self.config.get("one_time_window", {})
            ot_start = one_time.get("start")
            ot_end = one_time.get("end")
            if ot_start and ot_end:
                try:
                    now_ts = datetime.now()
                    start_ts = datetime.strptime(ot_start, "%Y-%m-%d %H:%M")
                    end_ts = datetime.strptime(ot_end, "%Y-%m-%d %H:%M")
                    if start_ts <= now_ts <= end_ts:
                        return True, "One-Time Window"
                except ValueError:
                    pass
        
        return False, None

    def run_loop(self):
        while True:
            allowed, trigger = self._is_in_schedule()
            
            if allowed and not self.is_running:
                self.toggle_running(True, trigger=trigger)
            elif not allowed and self.is_running:
                self.toggle_running(False, trigger="Schedule End")

            if self.is_running:
                if time.time() - self.last_activity_time < 20:
                    if not self.is_paused:
                        logging.info("User activity detected. Pausing anti-idle.")
                        self.is_paused = True
                        # Not notifying every pause to avoid spam, but we update config
                        self.config.set("is_paused", True)
                else:
                    if self.is_paused:
                        logging.info("User inactive. Resuming anti-idle.")
                        self.is_paused = False
                        self.config.set("is_paused", False)

                if not self.is_paused:
                    try:
                        self._do_anti_idle_move()
                    except Exception as e:
                        logging.error(f"Error during anti-idle move: {e}")
                        self.send_notification(f"⚠️ Error occurred: {e}")
            
            time.sleep(60)

    def _do_anti_idle_move(self):
        def_position = pyautogui.position()
        pyautogui.moveTo(def_position[0] + 1, def_position[1] + 1, duration=0.1)
        pyautogui.moveTo(def_position[0] - 1, def_position[1] - 1, duration=0.1)
        logging.info("Anti-idle movement performed.")

    def start(self):
        self.thread = threading.Thread(target=self.run_loop, daemon=True)
        self.thread.start()
