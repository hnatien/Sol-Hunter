import time
import random
import threading
import pyautogui
import logging
import platform

# Disable fail-safe to prevent accidental stops in background
pyautogui.FAILSAFE = False

class AntiAFK:
    def __init__(self, logCallback=None):
        self.logCallback = logCallback
        self.isRunning = False
        self.thread = None

    def log(self, message):
        if self.logCallback:
            self.logCallback(f"[Anti-AFK] {message}")
        else:
            logging.info(f"[Anti-AFK] {message}")

    def start(self):
        if self.isRunning:
            return
        self.isRunning = True
        self.thread = threading.Thread(target=self.runLoop, daemon=True)
        self.thread.start()
        self.log("Smart Anti-AFK Engaged")

    def stop(self):
        self.isRunning = False
        if self.thread:
            self.thread.join(timeout=1)
        self.log("Anti-AFK Disengaged")

    def runLoop(self):
        while self.isRunning:
            try:
                # Random interval between 2 to 4 minutes to prevent detection
                waitTime = random.uniform(120, 240)
                
                if platform.system() == "Windows":
                    import psutil
                    robloxRunning = False
                    for proc in psutil.process_iter(['name']):
                        if proc.info['name'] == "RobloxPlayerBeta.exe":
                            robloxRunning = True
                            break
                    
                    if not robloxRunning:
                        time.sleep(10)
                        continue
                
                pyautogui.press('space')
                self.log("Simulated activity (Jump)")
                time.sleep(waitTime)
                
            except Exception as e:
                self.log(f"Error: {e}")
                time.sleep(5)
