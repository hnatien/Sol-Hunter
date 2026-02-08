import os
import re
import json
import time
import glob
import requests
from datetime import datetime
from threading import Thread

class LoggerDetector:
    def __init__(self, logCallback=None):
        self.logCallback = logCallback
        self.isRunning = False
        self.lastPosition = 0
        self.logsDir = os.path.join(os.getenv('LOCALAPPDATA', ''), 'Roblox', 'logs')
        self.currentLogFile = None
        self.webhookUrl = ""
        self.accountName = "Unknown"
        self.minRollRarity = 1000000
        self.startTime = None
        self.currentBiome = "NORMAL"
        self.biomeStartTime = None
        self.currentAura = "None"
        self.lastSentMerchant = 0
        
        # Optimized patterns (Case Insensitive + Flexible)
        self.BIOME_PATTERN = re.compile(r"\[BloxstrapRPC\].*?(NORMAL|WINDY|RAINY|SNOWY|SAND STORM|HELL|STARFALL|CORRUPTION|NULL|GLITCHED|DREAMSPACE|CYBERSPACE)", re.I)
        self.MERCHANT_PATTERN = re.compile(r"\[Merchant\]: (Mari|Jester) has arrived", re.I)
        
        # Aura & Roll Detection Patterns
        self.AURA_PATTERN = re.compile(r'"(?:details|state)":"Equipped (?:: )?\\?"(.*?)\\?"', re.I)
        self.AURA_PATTERN_ALT = re.compile(r'"details":"Equipped: (.*?)"', re.I)
        
        # Roll Patterns: Catch local "You rolled" and global "[Server] Name rolled"
        self.ROLL_PATTERN = re.compile(r'You rolled: (.*?) \((.*?)\)', re.I)
        self.GLOBAL_ROLL_PATTERN = re.compile(r'\[Server\]:\s+(.*?)\s+has\s+rolled\s+(.*?)\s+\(1\s+in\s+(.*?)\)', re.I)
        
        # Special Event: Eden (The Devourer of the Void)
        self.EDEN_PATTERN = re.compile(r"The Devourer of the Void, (Eden|.+?)\s+has\s+appeared", re.I)

        # Rarity Multipliers (Noteab-style)
        self.MULTIPLIERS = {
            "GLITCHED": 100,
            "CORRUPTION": 55,
            "HELL": 35,
            "STARFALL": 25,
            "NULL": 20,
            "SAND STORM": 15,
            "SNOWY": 10,
            "RAINY": 8,
            "WINDY": 5
        }

    def log(self, message: str):
        if self.logCallback:
            self.logCallback(f"[Logger] {message}")

    def takeScreenshot(self, prefix="roll"):
        """Takes a screenshot of the game window (inspired by Noteab)."""
        try:
            import pyautogui
            import pygetwindow as gw
            
            # Try to find and activate Roblox window
            windows = gw.getWindowsWithTitle('Roblox')
            if windows:
                roblox = windows[0]
                if not roblox.isActive:
                    # Optional: roblox.activate() - might interrupt user
                    pass
                
                os.makedirs("screenshots", exist_ok=True)
                filename = f"screenshots/{prefix}_{int(time.time())}.png"
                
                # Take screenshot of the whole screen (or specific region if calibrated)
                pyautogui.screenshot(filename)
                self.log(f"Screenshot saved: {filename}")
                return filename
        except Exception as e:
            self.log(f"Screenshot failed: {e}")
        return None

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

            # Bloxstrap support
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
                self.log("FastFlags applied via Bloxstrap.")
                applied = True

            # Standard Roblox support
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
                self.log("FastFlags applied successfully. Please restart Roblox.")
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

    def syncInitialState(self):
        """Read the end of the log file to determine current Biome and Aura on startup."""
        self.currentLogFile = self.getLatestLogFile()
        if not self.currentLogFile:
            return

        self.log(f"Syncing initial state from: {os.path.basename(self.currentLogFile)}")
        try:
            with open(self.currentLogFile, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(0, os.SEEK_END)
                fileSize = f.tell()
                f.seek(max(0, fileSize - 100000))
                lines = f.readlines()
                
                for line in reversed(lines):
                    if self.currentBiome == "NORMAL":
                        match = self.BIOME_PATTERN.search(line)
                        if match:
                            self.currentBiome = match.group(1).upper()
                    
                    if self.currentAura == "None":
                        match = self.AURA_PATTERN.search(line) or self.AURA_PATTERN_ALT.search(line)
                        if match:
                            self.currentAura = match.group(1).replace("\\", "").strip()
                    
                    if self.currentBiome != "NORMAL" and self.currentAura != "None":
                        break
                self.log(f"Initial State: {self.currentBiome} | {self.currentAura}")
        except Exception as e: self.log(f"Sync error: {e}")

    def startDetection(self, webhookUrl="", accountName="Unknown", minRollRarity=1000000):
        if self.isRunning: return
        self.webhookUrl = webhookUrl
        self.accountName = accountName
        self.minRollRarity = minRollRarity
        self.startTime = datetime.now()
        
        self.syncInitialState()
        
        self.isRunning = True
        self.detectionThread = Thread(target=self.detectionLoop, daemon=True)
        self.detectionThread.start()
        self.log(f"Detection Active: {accountName}")
        self.sendStartWebhook()

    def sendStartWebhook(self):
        if not self.webhookUrl: return
        now = datetime.now()
        embed = {
            "title": "SolHunter Detection Engaged",
            "description": f"Monitoring logs for **{self.accountName}**",
            "color": 0x10b981,
            "fields": [
                {"name": "Biome", "value": f"`{self.currentBiome}`", "inline": True},
                {"name": "Aura", "value": f"`{self.currentAura}`", "inline": True}
            ],
            "footer": {"text": f"SolHunter v1.2 • {now.strftime('%I:%M %p')}"},
        }
        try: requests.post(self.webhookUrl, json={"embeds": [embed]}, timeout=5)
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

    def processLine(self, line: str):
        # 1. Biome Detection
        biomeMatch = self.BIOME_PATTERN.search(line)
        if biomeMatch:
            newBiome = biomeMatch.group(1).upper()
            if newBiome != self.currentBiome:
                if self.currentBiome != "NORMAL":
                    self.sendBiomeWebhook(self.currentBiome, status="Ended")
                
                self.currentBiome = newBiome
                self.log(f"Biome Event: {newBiome}")
                if newBiome != "NORMAL":
                    self.sendBiomeWebhook(newBiome, status="Active")

        # 2. Merchant Detection
        merchantMatch = self.MERCHANT_PATTERN.search(line)
        if merchantMatch:
            merchantName = merchantMatch.group(1)
            if time.time() - self.lastSentMerchant > 300: 
                self.log(f"Merchant Spawned: {merchantName}")
                self.sendMerchantWebhook(merchantName)
                self.lastSentMerchant = time.time()

        # 3. Eden Detection (Rare!)
        edenMatch = self.EDEN_PATTERN.search(line)
        if edenMatch:
            edenName = edenMatch.group(1)
            self.log(f"⚠️ EDEN DETECTED: {edenName}")
            self.sendEdenWebhook(edenName)

        # 4. Aura Detection (Equipping)
        auraMatch = self.AURA_PATTERN.search(line) or self.AURA_PATTERN_ALT.search(line)
        if auraMatch:
            newAura = auraMatch.group(1).replace("\\", "").strip()
            if newAura != self.currentAura and newAura != "" and "Equipped" not in newAura:
                self.currentAura = newAura
                self.log(f"Aura Update: {newAura}")
                self.sendAuraWebhook(newAura)

        # 5. Roll Detection (Local & Global)
        # Check Local Roll first
        localMatch = self.ROLL_PATTERN.search(line)
        if localMatch:
            self.handleRoll(localMatch.group(1), localMatch.group(2), isLocal=True)
            return

        # Check Global Roll
        globalMatch = self.GLOBAL_ROLL_PATTERN.search(line)
        if globalMatch:
            playerName = globalMatch.group(1).strip()
            auraName = globalMatch.group(2).strip()
            rarityStr = globalMatch.group(3).strip()
            # If the player name matches our account, it's a local roll reported globally
            isLocal = (playerName.lower() == self.accountName.lower())
            self.handleRoll(auraName, rarityStr, isLocal=isLocal, playerName=playerName)

    def handleRoll(self, auraName, rarityStr, isLocal=False, playerName=None):
        try:
            # Extract numeric rarity
            cleanRarity = re.sub(r'[^\d]', '', rarityStr.split('in')[-1])
            baseRarity = int(cleanRarity)
            
            # Multiplier logic
            multiplier = self.MULTIPLIERS.get(self.currentBiome, 1)
            finalRarity = baseRarity * multiplier
            rarityLabel = rarityStr if multiplier == 1 else f"{baseRarity:,} (x{multiplier} -> 1 in {finalRarity:,})"

            if baseRarity >= self.minRollRarity:
                self.log(f"{'LOCAL' if isLocal else 'GLOBAL'} ROLL: {auraName} [{rarityLabel}]")
                screenshot = None
                if isLocal:
                    screenshot = self.takeScreenshot(prefix=f"roll_{auraName[:10]}")
                
                self.sendRollWebhook(auraName, rarityLabel, finalRarity, isLocal, playerName, screenshot)
        except Exception as e: self.log(f"Roll Error: {e}")

    def sendBiomeWebhook(self, biomeName, status="Active"):
        if not self.webhookUrl: return
        now = datetime.now()
        color = 0x6c5ce7 if status == "Active" else 0x2f3542
        embed = {
            "title": f"Biome {status}: {biomeName}",
            "color": color,
            "fields": [
                {"name": "Account", "value": f"`{self.accountName}`", "inline": True},
                {"name": "Time", "value": f"`{now.strftime('%H:%M:%S')}`", "inline": True}
            ],
            "footer": {"text": f"SolHunter Analytics • {now.strftime('%I:%M %p')}"}
        }
        try: requests.post(self.webhookUrl, json={"embeds": [embed]}, timeout=5)
        except: pass

    def sendMerchantWebhook(self, merchantName):
        if not self.webhookUrl: return
        embed = {
            "title": f"⚠️ MERCHANT ARRIVED: {merchantName}",
            "description": f"Merchant spawned for **{self.accountName}**!",
            "color": 0xffa502,
            "footer": {"text": f"SolHunter Sniper • {datetime.now().strftime('%I:%M %p')}"}
        }
        try: requests.post(self.webhookUrl, json={"embeds": [embed]}, timeout=5)
        except: pass

    def sendEdenWebhook(self, edenName):
        if not self.webhookUrl: return
        embed = {
            "title": "🌌 EDEN DETECTED!",
            "description": f"**{edenName}** (The Devourer of the Void) has appeared in the server!",
            "color": 0x000000,
            "fields": [{"name": "Account", "value": f"`{self.accountName}`", "inline": False}],
            "footer": {"text": f"SolHunter Mythic • {datetime.now().strftime('%I:%M %p')}"}
        }
        try: requests.post(self.webhookUrl, json={"embeds": [embed]}, timeout=5)
        except: pass

    def sendAuraWebhook(self, auraName):
        if not self.webhookUrl: return
        embed = {
            "title": "Aura Status Changed",
            "description": f"**{self.accountName}** equipped ✨ `{auraName}`",
            "color": 0x747d8c,
            "footer": {"text": f"SolHunter v1.2 • {datetime.now().strftime('%I:%M %p')}"}
        }
        try: requests.post(self.webhookUrl, json={"embeds": [embed]}, timeout=5)
        except: pass

    def sendRollWebhook(self, auraName, rarityLabel, finalRarity, isLocal, playerName, screenshot=None):
        if not self.webhookUrl: return
        color = 0xff4757 if finalRarity >= 10000000 else 0xff7f50
        title = "🎰 INSANE ROLL PROTECTED!" if isLocal else "🌍 GLOBAL ANNOUNCEMENT"
        
        embed = {
            "title": title,
            "description": f"**{playerName if playerName else self.accountName}** achieved a rare aura!",
            "color": color,
            "fields": [
                {"name": "Aura", "value": f"**{auraName}**", "inline": True},
                {"name": "Rarity", "value": f"`{rarityLabel}`", "inline": True}
            ],
            "footer": {"text": f"SolHunter Stats • {datetime.now().strftime('%I:%M %p')}"}
        }
        if isLocal:
            embed["thumbnail"] = {"url": "https://raw.githubusercontent.com/vexsyx/sniper-v3/main/assets/snipercat.png"}
        
        try: requests.post(self.webhookUrl, json={"embeds": [embed]}, timeout=5)
        except: pass
