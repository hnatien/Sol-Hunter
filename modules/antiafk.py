import time
import random
import threading
import pyautogui
import logging
import platform

# Disable fail-safe to prevent accidental stops in background
pyautogui.FAILSAFE = False

class AntiAFK:
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.is_running = False
        self.thread = None

    def log(self, message):
        if self.log_callback:
            self.log_callback(f"[Anti-AFK] {message}")
        else:
            logging.info(f"[Anti-AFK] {message}")

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        self.log("Smart Anti-AFK Engaged")

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1)
        self.log("Anti-AFK Disengaged")

    def _loop(self):
        while self.is_running:
            try:
                # Random interval between 2 to 4 minutes to prevent detection
                wait_time = random.uniform(120, 240)
                
                # Check if we are on Windows and if Roblox is running
                if platform.system() == "Windows":
                    import psutil
                    roblox_running = False
                    for proc in psutil.process_iter(['name']):
                        if proc.info['name'] == "RobloxPlayerBeta.exe":
                            roblox_running = True
                            break
                    
                    if not roblox_running:
                        time.sleep(10)
                        continue

                # Simulate a small movement or jump
                # We use a simple 'jump' (spacebar)
                # To be 'smart', we don't force focus, we just send the key
                # Note: Roblox usually requires the window to be active for pyautogui.press
                # But sometimes background keys work depending on the method.
                # For 100% reliability we assume the user leaves it open.
                
                pyautogui.press('space')
                self.log("Simulated activity (Jump)")
                
                # Small wait before checking again
                time.sleep(wait_time)
                
            except Exception as e:
                self.log(f"Error: {e}")
                time.sleep(5)
