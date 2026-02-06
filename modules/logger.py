import os
import re
import json
import time
import glob
import requests
from datetime import datetime
from threading import Thread

class LoggerDetector:
    """
    Detects game events by reading Roblox local logs.
    """
    
    def __init__(self, logCallback=None):
        self.logCallback = logCallback
        self.isRunning = False
        self.lastPosition = 0
        self.logsDir = os.path.join(os.getenv('LOCALAPPDATA', ''), 'Roblox', 'logs')
        self.currentLogFile = None
        
        # Webhook Settings
        self.webhookUrl = ""
        self.accountName = "Unknown"
        self.startTime = None
        self.currentBiome = "NORMAL"
        self.biomeStartTime = None
        
        # Detection regex patterns
        self.BIOME_PATTERN = re.compile(r"\[BloxstrapRPC\].*?(NORMAL|WINDY|RAINY|SNOWY|SAND STORM|HELL|STARFALL|CORRUPTION|NULL|GLITCHED|DREAMSPACE|CYBERSPACE)")
        self.MERCHANT_PATTERN = re.compile(r"\[Merchant\]: (Mari|Jester) has arrived on the island")
        self.AURA_PATTERN = re.compile(r'"state":"Equipped \\"(.*?)\\"')

    def log(self, message: str):
        if self.logCallback:
            self.logCallback(f"[Logger] {message}")

    def applyFastFlags(self):
        try:
            localApp = os.getenv('LOCALAPPDATA', '')
            flags = {
                "DFFlagDebugPerfMode": "True",
                "FFlagHandleAltEnterFullscreenManually": "False",
                "FStringDebugLuaLogPattern": "ExpChat/mountClientApp",
                "FStringDebugLuaLogLevel": "trace"
            }
            applied = False

            # Case 1: Bloxstrap (Preferred if exists)
            bloxstrapDir = os.path.join(localApp, 'Bloxstrap')
            if os.path.exists(bloxstrapDir):
                modDir = os.path.join(bloxstrapDir, 'Modifications', 'ClientSettings')
                os.makedirs(modDir, exist_ok=True)
                settingsPath = os.path.join(modDir, "ClientAppSettings.json")
                
                existingData = {}
                if os.path.exists(settingsPath):
                    try:
                        with open(settingsPath, "r") as f:
                            existingData = json.load(f)
                    except: pass
                
                existingData.update(flags)
                with open(settingsPath, "w") as f:
                    json.dump(existingData, f, indent=4)
                self.log("FastFlags applied via Bloxstrap (Modifications).")
                applied = True

            # Case 2: Standard Roblox
            robloxVersions = os.path.join(localApp, 'Roblox', 'Versions')
            if os.path.exists(robloxVersions):
                for folder in os.listdir(robloxVersions):
                    if folder.startswith("version-"):
                        settingsDir = os.path.join(robloxVersions, folder, "ClientSettings")
                        os.makedirs(settingsDir, exist_ok=True)
                        settingsPath = os.path.join(settingsDir, "ClientAppSettings.json")
                        
                        existingData = {}
                        if os.path.exists(settingsPath):
                            try:
                                with open(settingsPath, "r") as f:
                                    existingData = json.load(f)
                            except: pass
                        
                        existingData.update(flags)
                        with open(settingsPath, "w") as f:
                            json.dump(existingData, f, indent=4)
                        applied = True
                if applied and not os.path.exists(bloxstrapDir):
                    self.log("FastFlags applied via standard Roblox.")

            if applied:
                self.log("FastFlags applied successfully. Please restart Roblox/Bloxstrap.")
            return applied
        except Exception as e:
            self.log(f"Error applying FastFlags: {e}")
            return False

    def getLatestLogFile(self) -> str | None:
        try:
            if not os.path.exists(self.logsDir): return None
            files = glob.glob(os.path.join(self.logsDir, "*.log"))
            if not files: return None
            return max(files, key=os.path.getmtime)
        except: return None

    def startDetection(self, webhookUrl="", accountName="Unknown"):
        if self.isRunning: return
        self.webhookUrl = webhookUrl
        self.accountName = accountName
        self.startTime = datetime.now()
        self.isRunning = True
        self.detectionThread = Thread(target=self.detectionLoop, daemon=True)
        self.detectionThread.start()
        self.log(f"Log detection started for account: {accountName}")
        self.sendStartWebhook()

    def sendStartWebhook(self):
        """Sends a 'Tool Started' notification matching the user's requested UI."""
        if not self.webhookUrl: return
        now = datetime.now()
        embed = {
            "title": "SOLS HUNTER Started",
            "color": 0x55ff55, # Green accent sidebar
            "fields": [
                {"name": "SOLS HUNTER", "value": "‎", "inline": False}, # Blank char for spacing
                {"name": "Accounts Configured", "value": "1", "inline": True},
                {"name": "Webhooks Configured", "value": "1", "inline": True}
            ],
            "footer": {"text": "SOLS HUNTER v1.0 • Hôm nay lúc " + now.strftime("%H:%M %p")},
        }
        try:
            requests.post(self.webhookUrl, json={"embeds": [embed]}, timeout=5)
        except: pass

    def stopDetection(self):
        self.isRunning = False
        self.log("Log detection stopped.")

    def detectionLoop(self):
        self.currentLogFile = self.getLatestLogFile()
        if self.currentLogFile:
            self.lastPosition = os.path.getsize(self.currentLogFile)

        while self.isRunning:
            latestFile = self.getLatestLogFile()
            if not latestFile:
                time.sleep(2)
                continue

            if latestFile != self.currentLogFile:
                self.currentLogFile = latestFile
                self.lastPosition = 0
                self.log(f"New log file: {os.path.basename(latestFile)}")

            try:
                with open(self.currentLogFile, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(self.lastPosition)
                    lines = f.readlines()
                    self.lastPosition = f.tell()
                    for line in lines:
                        self.processLine(line)
            except Exception as e:
                self.log(f"Read error: {e}")
            time.sleep(1)

    def sendWebhook(self, eventType, biomeName, status="Started"):
        if not self.webhookUrl: return
        
        # Calculate Uptime
        now = datetime.now()
        uptimeSeconds = int((now - self.startTime).total_seconds())
        uptimeStr = f"{uptimeSeconds // 60}m {uptimeSeconds % 60}s"
        
        # Relative time for "Started"
        if status == "Started":
            startedStr = "Vừa mới đây"
        else:
            startedStr = "Đã kết thúc"

        color = 0x6c5ce7 if status == "Started" else 0x3d3d3d # Purple for start, Dark for end
        
        embed = {
            "title": f"Biome {status} - {biomeName}",
            "color": color,
            "fields": [
                {"name": "Account", "value": self.accountName, "inline": False},
                {"name": "Uptime", "value": uptimeStr, "inline": True}
            ],
            "footer": {"text": "SolHunter v1.0 • Hôm nay lúc " + now.strftime("%H:%M %p")},
            "timestamp": now.isoformat()
        }
        
        if status == "Started":
            embed["fields"].append({"name": "Started", "value": startedStr, "inline": True})

        try:
            requests.post(self.webhookUrl, json={"embeds": [embed]}, timeout=5)
        except Exception as e:
            self.log(f"Webhook error: {e}")

    def processLine(self, line: str):
        biomeMatch = self.BIOME_PATTERN.search(line)
        if biomeMatch:
            newBiome = biomeMatch.group(1)
            if newBiome != self.currentBiome:
                # End previous biome if it wasn't NORMAL
                if self.currentBiome != "NORMAL":
                    self.sendWebhook("Biome", self.currentBiome, status="Ended")
                
                # Start new biome
                self.currentBiome = newBiome
                self.biomeStartTime = datetime.now()
                self.log(f"Biome Changed: {newBiome}")
                
                if newBiome != "NORMAL":
                    self.sendWebhook("Biome", newBiome, status="Started")

        merchantMatch = self.MERCHANT_PATTERN.search(line)
        if merchantMatch:
            merchantName = merchantMatch.group(1)
            self.log(f"Merchant Detected: {merchantName}")
            self.sendMerchantWebhook(merchantName)

    def sendMerchantWebhook(self, merchantName):
        if not self.webhookUrl: return
        embed = {
            "title": f"Merchant Arrived - {merchantName}",
            "color": 0xffcc00, # Yellow for merchant
            "fields": [
                {"name": "Account", "value": self.accountName, "inline": False}
            ],
            "footer": {"text": "SolHunter v1.0"},
            "timestamp": datetime.now().isoformat()
        }
        try: requests.post(self.webhookUrl, json={"embeds": [embed]}, timeout=5)
        except: pass
