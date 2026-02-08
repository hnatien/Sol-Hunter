import customtkinter as ctk
import json
import os
import sys
import threading
import time
from typing import Dict, Optional, Callable

from modules.listener import DiscordListener
from modules.logger import LoggerDetector
from modules.launcher import launchRoblox, killRoblox
from modules.antiafk import AntiAFK
from modules.theme import Theme

Theme.applyAppearance()

CONFIG_FILE = os.path.join(os.getenv('APPDATA'), "SolHunter", "config.json")
if not os.path.exists(os.path.dirname(CONFIG_FILE)):
    try: 
        os.makedirs(os.path.dirname(CONFIG_FILE))
    except: 
        CONFIG_FILE = "config.json"

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, navigateCallback: Callable[[str], None]):
        super().__init__(master, width=220, corner_radius=0, fg_color=Theme.SIDEBAR)
        self.navigateCallback = navigateCallback
        self.grid_rowconfigure(6, weight=1)
        
        self.setupHeader()
        self.setupStatus()
        self.setupNavButtons()
        self.setupFooter()

    def setupHeader(self):
        ctk.CTkLabel(self, text="SolHunter", font=("Arial", 22, "bold"), text_color=Theme.ACCENT).grid(row=0, column=0, padx=20, pady=(40, 30), sticky="w")

    def setupStatus(self):
        self.statusFrame = ctk.CTkFrame(self, fg_color="transparent")
        self.statusFrame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="w")
        
        self.statusDot = ctk.CTkLabel(self.statusFrame, text="●", text_color=Theme.ERROR, font=("Arial", 16))
        self.statusDot.pack(side="left")
        
        self.statusText = ctk.CTkLabel(self.statusFrame, text="Status: IDLE", text_color=Theme.TEXT_SUB, font=Theme.FONT_SUBHEADER)
        self.statusText.pack(side="left", padx=(8, 0))

    def setupNavButtons(self):
        self.buttons = {}
        pages = [("Sniper", ""), ("AFK Mode", ""), ("Live Logs", ""), ("User Guide", "")]
        
        for i, (name, icon) in enumerate(pages):
            btn = ctk.CTkButton(
                self, 
                text=f"  {icon}  {name}", 
                height=45, 
                font=Theme.FONT_ICON,
                fg_color="transparent", 
                text_color=Theme.TEXT_MAIN, 
                hover_color=Theme.HOVER, 
                anchor="w", 
                command=lambda n=name: self.navigateCallback(n)
            )
            btn.grid(row=3+i, column=0, padx=15, pady=4, sticky="ew")
            self.buttons[name] = btn

    def setupFooter(self):
        ctk.CTkLabel(self, text="Created by Night0wl", font=Theme.FONT_SMALL, text_color="#444").grid(row=7, column=0, padx=20, pady=(0, 20), sticky="ew")

    def setActive(self, pageName: str):
        for name, btn in self.buttons.items():
            isActive = (name == pageName) or (name == "User Guide" and pageName == "Guide") or (name == "Live Logs" and pageName == "Logs") or (name == "AFK Mode" and pageName == "AFK") or (name == "Sniper" and pageName == "Sniper")
            
            btn.configure(
                fg_color=Theme.HOVER if isActive else "transparent",
                text_color=Theme.ACCENT if isActive else Theme.TEXT_MAIN,
                border_width=0
            )

    def updateStatus(self, isActive: bool, text: str = ""):
        color = Theme.SUCCESS if isActive else Theme.ERROR
        self.statusDot.configure(text_color=color)
        self.statusText.configure(text=f"Status: {text}", text_color=color if isActive else Theme.TEXT_SUB)


class SniperPage(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent", corner_radius=0)
        self.app = app
        self.setupUI()

    def setupUI(self):
        ctk.CTkLabel(self, text="SNIPER CONTROL CENTER", font=Theme.FONT_HEADER, text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=30, pady=(30, 5))
        ctk.CTkLabel(self, text="Configure your connection and target preferences below.", font=Theme.FONT_BODY, text_color=Theme.TEXT_SUB).pack(anchor="w", padx=30, pady=(0, 20))

        self.createAuthCard()
        self.createBiomesCard()
        self.createMerchantsCard()
        self.createControls()

    def createCard(self, title: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(self, fg_color=Theme.CARD, corner_radius=15, border_width=1, border_color=Theme.BORDER)
        card.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(card, text=title, font=Theme.FONT_SUBHEADER, text_color=Theme.ACCENT).pack(anchor="w", padx=20, pady=(15, 10))
        return card

    def createAuthCard(self):
        card = self.createCard("AUTHENTICATION")
        
        ctk.CTkLabel(card, text="Discord User Token:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_SUB).pack(anchor="w", padx=20)
        self.app.tokenEntry = ctk.CTkEntry(card, placeholder_text="Enter your Discord token here...", show="*", height=40, fg_color=Theme.INPUT_BG, border_color=Theme.BORDER)
        self.app.tokenEntry.pack(fill="x", padx=20, pady=(2, 10))

        ctk.CTkLabel(card, text="Webhook URL:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_SUB).pack(anchor="w", padx=20)
        self.app.webhookEntry = ctk.CTkEntry(card, placeholder_text="https://discord.com/api/webhooks/...", height=40, fg_color=Theme.INPUT_BG, border_color=Theme.BORDER)
        self.app.webhookEntry.pack(fill="x", padx=20, pady=(2, 15))

    def createBiomesCard(self):
        card = self.createCard("TARGET BIOMES")
        container = ctk.CTkFrame(card, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=5)
        
        biomesList = ["Glitched", "Cyberspace", "Dreamspace", "Null", "Starfall", "Hell", "Corruption", "Heaven"]
        for i, biome in enumerate(biomesList):
            var = ctk.StringVar(value="off")
            self.app.biomeVars[biome] = var
            ctk.CTkSwitch(container, text=biome, variable=var, onvalue="on", offvalue="off", progress_color=Theme.ACCENT, font=Theme.FONT_BODY).grid(row=i // 3, column=i % 3, padx=15, pady=12, sticky="w")

    def createMerchantsCard(self):
        card = self.createCard("TARGET MERCHANTS")
        container = ctk.CTkFrame(card, fg_color="transparent")
        container.pack(fill="x", padx=20, pady=5)
        
        merchantsList = ["Jester", "Mari"]
        for i, merchant in enumerate(merchantsList):
            var = ctk.StringVar(value="off")
            self.app.merchantVars[merchant] = var
            ctk.CTkSwitch(container, text=merchant, variable=var, onvalue="on", offvalue="off", progress_color=Theme.ACCENT, font=Theme.FONT_BODY).grid(row=0, column=i, padx=15, pady=10, sticky="w")

    def createControls(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=30, pady=10)
        
        self.app.autoKillVar = ctk.StringVar(value="off")
        ctk.CTkSwitch(frame, text="Auto-Kill Roblox Process", variable=self.app.autoKillVar, onvalue="on", offvalue="off", progress_color=Theme.ACCENT, font=Theme.FONT_BODY).pack(side="left")

        ctk.CTkButton(self, text="SAVE SETTINGS", command=self.app.saveConfig, fg_color=Theme.HOVER, height=40, font=Theme.FONT_SUBHEADER).pack(fill="x", padx=30, pady=(10, 5))
        self.app.startBtn = ctk.CTkButton(self, text="START SNIPER ENGINE", command=self.app.toggleSniper, fg_color=Theme.ACCENT, hover_color=Theme.ACCENT_HOVER, height=50, font=("Arial", 14, "bold"))
        self.app.startBtn.pack(fill="x", padx=30, pady=(5, 30))


class SolHunterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SolHunter v1.0")
        self.geometry("900x650")
        self.resizable(True, True)
        self.configure(fg_color=Theme.BG)
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.listener: DiscordListener | None = None
        self.loggerDetector = LoggerDetector(logCallback=self.logMessage)
        self.isRunning = False
        self.isAfkRunning = False
        self.antiAFK = AntiAFK(logCallback=self.logMessage)
        self.biomeVars: Dict[str, ctk.StringVar] = {}
        self.merchantVars: Dict[str, ctk.StringVar] = {}

        self.sidebar = Sidebar(self, self.selectPage)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.contentArea = ctk.CTkFrame(self, fg_color="transparent")
        self.contentArea.grid(row=0, column=1, sticky="nsew")
        self.contentArea.grid_columnconfigure(0, weight=1)
        self.contentArea.grid_rowconfigure(0, weight=1)

        self.pages = {}
        self.createPages()
        
        self.loadConfig()
        self.selectPage("Sniper")
        self.showToast("System Initialized", duration=2000, color=Theme.SUCCESS)

    def createPages(self):
        self.pages["Sniper"] = SniperPage(self.contentArea, self)
        self.pages["AFK Mode"] = self.createAfkPage()
        self.pages["Live Logs"] = self.createLogsPage()
        self.pages["User Guide"] = self.createGuidePage()

    def createAfkPage(self):
        page = ctk.CTkScrollableFrame(self.contentArea, fg_color="transparent", corner_radius=0)
        
        ctk.CTkLabel(page, text="AFK AUTOMATION", font=Theme.FONT_HEADER, text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=30, pady=(30, 5))
        ctk.CTkLabel(page, text="Automated background detection via logs.", font=Theme.FONT_BODY, text_color=Theme.TEXT_SUB).pack(anchor="w", padx=30, pady=(0, 20))
        
        settingCard = ctk.CTkFrame(page, fg_color=Theme.CARD, corner_radius=15, border_width=1, border_color=Theme.BORDER)
        settingCard.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(settingCard, text="DETECTION SETTINGS", font=Theme.FONT_SUBHEADER, text_color=Theme.ACCENT).pack(anchor="w", padx=20, pady=(15, 10))
        
        self.logDetectionVar = ctk.StringVar(value="off")
        ctk.CTkSwitch(settingCard, text="Enable Log Detection", variable=self.logDetectionVar, onvalue="on", offvalue="off", progress_color=Theme.ACCENT, font=Theme.FONT_BODY).pack(anchor="w", padx=20, pady=5)
        
        self.antiafkVar = ctk.StringVar(value="off")
        ctk.CTkSwitch(settingCard, text="Smart Anti-AFK (Jump)", variable=self.antiafkVar, onvalue="on", offvalue="off", progress_color=Theme.ACCENT, font=Theme.FONT_BODY).pack(anchor="w", padx=20, pady=5)
        
        ctk.CTkLabel(settingCard, text="Account Name:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_SUB).pack(anchor="w", padx=20)
        self.afkAccountEntry = ctk.CTkEntry(settingCard, placeholder_text="Username...", height=40, fg_color=Theme.INPUT_BG, border_color=Theme.BORDER)
        self.afkAccountEntry.pack(fill="x", padx=20, pady=(2, 10))
        
        ctk.CTkLabel(settingCard, text="AFK Webhook URL:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_SUB).pack(anchor="w", padx=20)
        self.afkWebhookEntry = ctk.CTkEntry(settingCard, placeholder_text="URL...", height=40, fg_color=Theme.INPUT_BG, border_color=Theme.BORDER)
        self.afkWebhookEntry.pack(fill="x", padx=20, pady=(2, 10))

        ctk.CTkLabel(settingCard, text="Min Roll Rarity (e.g. 1000000):", font=Theme.FONT_SMALL, text_color=Theme.TEXT_SUB).pack(anchor="w", padx=20)
        self.minRollEntry = ctk.CTkEntry(settingCard, placeholder_text="1000000", height=40, fg_color=Theme.INPUT_BG, border_color=Theme.BORDER)
        self.minRollEntry.pack(fill="x", padx=20, pady=(2, 15))

        toolCard = ctk.CTkFrame(page, fg_color=Theme.CARD, corner_radius=15, border_width=1, border_color=Theme.BORDER)
        toolCard.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(toolCard, text="OPTIMIZATION TOOLS", font=Theme.FONT_SUBHEADER, text_color=Theme.ACCENT).pack(anchor="w", padx=20, pady=(15, 10))
        
        ctk.CTkButton(toolCard, text="APPLY ROBLOX FASTFLAGS (LOWER CPU)", command=self.applyFastFlags, fg_color=Theme.HOVER, height=40).pack(fill="x", padx=20, pady=(5, 15))

        self.afkStartBtn = ctk.CTkButton(page, text="START AFK DETECTION", command=self.toggleAfkMode, fg_color=Theme.ACCENT, height=50, font=("Arial", 14, "bold"))
        self.afkStartBtn.pack(fill="x", padx=30, pady=(20, 30))
        return page

    def createLogsPage(self):
        page = ctk.CTkFrame(self.contentArea, fg_color="transparent")
        self.console = ctk.CTkTextbox(page, fg_color=Theme.CONSOLE_BG, text_color="#00ff00", font=("Consolas", 12), corner_radius=10, border_width=1, border_color=Theme.BORDER)
        self.console.pack(fill="both", expand=True, padx=30, pady=30)
        return page

    def createGuidePage(self):
        page = ctk.CTkFrame(self.contentArea, fg_color="transparent")
        self.guideBox = ctk.CTkTextbox(page, fg_color=Theme.CARD, text_color=Theme.TEXT_MAIN, font=("Consolas", 13), corner_radius=10, border_width=1, border_color=Theme.BORDER)
        self.guideBox.pack(fill="both", expand=True, padx=30, pady=30)
        self.guideBox.insert("1.0", """SOLHUNTER USER GUIDE

SECTION 1: DISCORD SNIPER SETUP
1. Get Discord Token: Open Discord in Browser.
2. Target Channels: The engine monitors pre-configured community channels.
3. Target Filters: Toggle specific Biomes or Merchants.
4. Auto-Kill: Closes active Roblox windows before launching.

SECTION 2: AFK MODE SETUP
1. Log Detection: Reads local Roblox logs for events.
2. Account Name: Set your Roblox username for reports.
3. Webhook: Input a Discord Webhook URL.
4. Smart Anti-AFK: Randomized jump simulation.
5. FastFlags: Applies low-resource settings.

SECTION 3: OPERATION
1. Sniper Engine: Controls the automated server joining logic.
2. AFK Engine: Controls local monitoring.
3. Live Logs: Displays real-time status.

WARNING
Keep your Discord Token private.""")
        self.guideBox.configure(state="disabled")
        return page

    def selectPage(self, name):
        self.sidebar.setActive(name)
        for page in self.pages.values():
            page.grid_forget()
        
        if name in self.pages:
            self.pages[name].grid(row=0, column=0, sticky="nsew")

    def logMessage(self, message: str):
        if not hasattr(self, 'console'): return
        self.after(0, lambda: [
            self.console.configure(state="normal"), 
            self.console.insert("end", f"> {message}\n"), 
            self.console.see("end"), 
            self.console.configure(state="disabled")
        ])

    def showToast(self, message: str, duration=2500, color=None):
        toast = ctk.CTkToplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True, "-alpha", 0.0)
        
        w, h = 360, 60
        x = self.winfo_x() + (self.winfo_width() // 2) - (w // 2)
        y = self.winfo_y() + self.winfo_height() - 100
        toast.geometry(f"{w}x{h}+{x}+{y}")
        
        frame = ctk.CTkFrame(toast, fg_color="#18181b", border_width=1, border_color=Theme.BORDER, corner_radius=12)
        frame.pack(fill="both", expand=True)
        
        accent = color if color else Theme.ACCENT
        ctk.CTkFrame(frame, width=4, fg_color=accent, corner_radius=10).pack(side="left", fill="y", padx=(15, 0), pady=12)
        ctk.CTkLabel(frame, text=message, font=("Arial", 14, "bold"), text_color="white").pack(side="left", padx=15)

        def fade(alpha, target):
            if (target == 1.0 and alpha < 1.0) or (target == 0.0 and alpha > 0.0):
                newAlpha = alpha + (0.1 if target == 1.0 else -0.1)
                toast.attributes("-alpha", max(0, min(1, newAlpha)))
                self.after(16, lambda: fade(newAlpha, target))
            elif target == 1.0:
                self.after(duration, lambda: fade(1.0, 0.0))
            else:
                toast.destroy()
        fade(0.0, 1.0)

    def loadConfig(self):
        defaults = {
            "discord_token": "", 
            "target_channels": [1282542323590496277, 1282543762425516083], 
            "biomes": {}, 
            "merchants": {}, 
            "webhook_url": "", 
            "auto_kill_roblox": False, 
            "log_detection": False, 
            "afk_webhook_url": "", 
            "afk_account_name": "hnatien",
            "min_roll_rarity": 1000000,
            "antiafk_enabled": False
        }
        loaded = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    loaded = json.load(f)
            except: pass
            
        config = {**defaults, **loaded}
        
        if self.tokenEntry: self.tokenEntry.insert(0, config.get("discord_token", ""))
        if self.webhookEntry: self.webhookEntry.insert(0, config.get("webhook_url", ""))
        if self.afkWebhookEntry: self.afkWebhookEntry.insert(0, config.get("afk_webhook_url", ""))
        if self.afkAccountEntry: self.afkAccountEntry.insert(0, config.get("afk_account_name", ""))
        if self.minRollEntry: self.minRollEntry.insert(0, str(config.get("min_roll_rarity", 1000000)))
        self.autoKillVar.set("on" if config.get("auto_kill_roblox", False) else "off")
        self.logDetectionVar.set("on" if config.get("log_detection", False) else "off")
        self.antiafkVar.set("on" if config.get("antiafk_enabled", False) else "off")
        
        savedBiomes = config.get("biomes", {})
        for biome, var in self.biomeVars.items():
            if savedBiomes.get(biome, False): var.set("on")
            
        savedMerchants = config.get("merchants", {})
        for merchant, var in self.merchantVars.items():
            if savedMerchants.get(merchant, False): var.set("on")

    def saveConfig(self):
        config = {
            "discord_token": self.tokenEntry.get(),
            "webhook_url": self.webhookEntry.get(),
            "auto_kill_roblox": (self.autoKillVar.get() == "on"),
            "log_detection": (self.logDetectionVar.get() == "on"),
            "afk_webhook_url": self.afkWebhookEntry.get().strip(),
            "afk_account_name": self.afkAccountEntry.get().strip(),
            "min_roll_rarity": int(self.minRollEntry.get() or 1000000),
            "antiafk_enabled": (self.antiafkVar.get() == "on"),
            "target_channels": [1282542323590496277, 1282543762425516083],
            "biomes": {b: (v.get() == "on") for b, v in self.biomeVars.items()},
            "merchants": {m: (v.get() == "on") for m, v in self.merchantVars.items()}
        }
        with open(CONFIG_FILE, "w") as f: json.dump(config, f, indent=4)
        self.showToast("Settings Saved", color=Theme.SUCCESS)
        self.logMessage("Configuration saved successfully.")

    def toggleSniper(self):
        if self.isRunning: self.stopSniper()
        else: self.startSniper()

    def startSniper(self):
        token = self.tokenEntry.get().strip()
        if not token: 
            self.logMessage("Error: Token required.")
            return

        try:
            self.saveConfig()
            channels = [1282542323590496277, 1282543762425516083]
            activeBiomes = [b for b, v in self.biomeVars.items() if v.get() == "on"]
            activeMerchants = [m for m, v in self.merchantVars.items() if v.get() == "on"]
            
            self.listener = DiscordListener(
                token=token, 
                targetChannels=channels, 
                activeBiomes=activeBiomes, 
                activeMerchants=activeMerchants, 
                webhookUrl=self.webhookEntry.get().strip(), 
                autoKill=(self.autoKillVar.get() == "on"), 
                logCallback=self.logMessage
            )
            self.listener.startListening()
            self.isRunning = True
            
            self.startBtn.configure(text="STOP SNIPER ENGINE", fg_color=Theme.ERROR, hover_color=Theme.ERROR_HOVER)
            self.sidebar.updateStatus(True, "SNIPING")
            self.showToast("Sniper Engine Engaged!", color=Theme.SUCCESS)
        except Exception as e: 
            self.logMessage(f"Error: {e}")

    def stopSniper(self):
        if self.listener: 
            self.listener.stopListening()
            self.listener = None
        self.isRunning = False
        self.startBtn.configure(text="START SNIPER ENGINE", fg_color=Theme.ACCENT, hover_color=Theme.ACCENT_HOVER)
        self.sidebar.updateStatus(False, "IDLE")
        self.showToast("Sniper Disengaged", color=Theme.ERROR)
        self.logMessage("Sniper Engine Stopped.")

    def toggleAfkMode(self):
        if self.isAfkRunning:
            if self.loggerDetector: self.loggerDetector.stopDetection()
            if self.antiAFK: self.antiAFK.stop()
            self.isAfkRunning = False
            self.afkStartBtn.configure(text="START AFK DETECTION", fg_color=Theme.ACCENT, hover_color=Theme.ACCENT_HOVER)
            self.sidebar.updateStatus(False, "IDLE")
            self.showToast("AFK Mode Stopped", color=Theme.ERROR)
            self.logMessage("AFK Mode Stopped.")
            return

        if self.logDetectionVar.get() != "on":
            self.logMessage("Enable 'Log Detection' first.")
            self.showToast("Enable Log Detection First", color=Theme.ERROR)
            return

        try:
            minRarity = int(self.minRollEntry.get() or 1000000)
        except:
            minRarity = 1000000
        
        self.loggerDetector.startDetection(
            webhookUrl=self.afkWebhookEntry.get().strip(), 
            accountName=self.afkAccountEntry.get().strip(),
            minRollRarity=minRarity
        )
        
        if self.antiafkVar.get() == "on":
            self.antiAFK.start()

        self.isAfkRunning = True
        self.afkStartBtn.configure(text="STOP AFK DETECTION", fg_color=Theme.ERROR, hover_color=Theme.ERROR_HOVER)
        self.sidebar.updateStatus(True, "AFK MONITORING")
        self.showToast("AFK Mode Active", color=Theme.SUCCESS)
        self.logMessage("AFK Mode Started.")

    def applyFastFlags(self):
        if not self.loggerDetector.applyFastFlags():
            self.showToast("Failed to apply Flags", color=Theme.ERROR)
            return

        self.showToast("Flags Applied - Restarting...", color=Theme.SUCCESS)
        killRoblox()
        self.after(2000, lambda: launchRoblox(placeId="15532592330"))
        self.logMessage("FastFlags applied. Relaunching...")

if __name__ == "__main__":
    app = SolHunterApp()
    app.mainloop()
