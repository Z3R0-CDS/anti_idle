import json
import os
from pathlib import Path

class ConfigManager:
    def __init__(self):
        # Path: Documents/AntiIdle/settings.config
        self.config_dir = Path.home() / "Documents" / "AntiIdle"
        self.config_file = self.config_dir / "settings.config"
        self.defaults = {
            "webhook_url": "",
            "weekly_schedule": {
                "Monday": {"start": "08:00", "end": "17:00"},
                "Tuesday": {"start": "08:00", "end": "17:00"},
                "Wednesday": {"start": "08:00", "end": "17:00"},
                "Thursday": {"start": "08:00", "end": "17:00"},
                "Friday": {"start": "08:00", "end": "17:00"},
                "Saturday": {"start": "off", "end": "off"},
                "Sunday": {"start": "off", "end": "off"},
            },
            "one_time_window": {"start": None, "end": None},
            "is_running": False
        }
        self.settings = self.load()

    def load(self):
        if not self.config_file.exists():
            return self.defaults.copy()
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return self.defaults.copy()

    def save(self):
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except IOError as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save()
