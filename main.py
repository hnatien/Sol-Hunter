import customtkinter as ctk
import json
import os
import sys
import threading
import time
from typing import Dict, Optional, Callable

from modules.listener import DiscordListener
from modules.logger import LoggerDetector
from modules.launcher import launch_roblox, kill_roblox
from modules.antiafk import AntiAFK
from modules.theme import Theme

# Apply Theme Settings
Theme.apply_appearance()

CONFIG_FILE = os.path.join(os.getenv('APPDATA'), "SolHunter", "config.json")
if not os.path.exists(os.path.dirname(CONFIG_FILE)):
    try: os.makedirs(os.path.dirname(CONFIG_FILE))
    except: CONFIG_FILE = "config.json" # Fallback to local

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, navigate_callback: Callable[[str], None]):
        super().__init__(master, width=220, corner_radius=0, fg_color=Theme.SIDEBAR)
        self.navigate_callback = navigate_callback
        self.grid_rowconfigure(6, weight=1) # Push bottom items down
        
        self.setup_header()
        self.setup_status()
        self.setup_nav_buttons()
        self.setup_footer()

    def setup_header(self):
        ctk.CTkLabel(self, text="SolHunter", font=("Arial", 22, "bold"), text_color=Theme.ACCENT).grid(row=0, column=0, padx=20, pady=(40, 30), sticky="w")


    def setup_status(self):
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="w")
        
        self.status_dot = ctk.CTkLabel(self.status_frame, text="●", text_color=Theme.ERROR, font=("Arial", 16))
        self.status_dot.pack(side="left")
        
        self.status_text = ctk.CTkLabel(self.status_frame, text="Status: IDLE", text_color=Theme.TEXT_SUB, font=Theme.FONT_SUBHEADER)
        self.status_text.pack(side="left", padx=(8, 0))

    def setup_nav_buttons(self):
        self.buttons = {}
        pages = [("Dashboard", ""), ("AFK Mode", ""), ("Live Logs", ""), ("User Guide", "")]
        
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
                command=lambda n=name: self.navigate_callback(n)
            )
            btn.grid(row=3+i, column=0, padx=15, pady=4, sticky="ew")
            self.buttons[name] = btn

    def setup_footer(self):
        ctk.CTkLabel(self, text="Created by Night0wl", font=Theme.FONT_SMALL, text_color="#444").grid(row=7, column=0, padx=20, pady=(0, 20), sticky="ew")

    def set_active(self, page_name: str):
        for name, btn in self.buttons.items():
            is_active = (name == page_name) or (name == "User Guide" and page_name == "Guide") or (name == "Live Logs" and page_name == "Logs") or (name == "AFK Mode" and page_name == "AFK")
            
            btn.configure(
                fg_color=Theme.HOVER if is_active else "transparent",
                text_color=Theme.ACCENT if is_active else Theme.TEXT_MAIN,
                border_width=0
            )
            # Add a left border indicator for active state using a frame? 
            # Simplified for now: just color change

    def update_status(self, is_active: bool, text: str = ""):
        color = Theme.SUCCESS if is_active else Theme.ERROR
        self.status_dot.configure(text_color=color)
        self.status_text.configure(text=f"Status: {text}", text_color=color if is_active else Theme.TEXT_SUB)


class DashboardPage(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent", corner_radius=0)
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        # Header
        ctk.CTkLabel(self, text="SNIPER CONTROL CENTER", font=Theme.FONT_HEADER, text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=30, pady=(30, 5))
        ctk.CTkLabel(self, text="Configure your connection and target preferences below.", font=Theme.FONT_BODY, text_color=Theme.TEXT_SUB).pack(anchor="w", padx=30, pady=(0, 20))

        # Auth Card
        self.create_auth_card()
        
        # Biomes Card
        self.create_biomes_card()
        
        # Merchants Card
        self.create_merchants_card()
        
        # Controls
        self.create_controls()

    def create_card(self, title: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(self, fg_color=Theme.CARD, corner_radius=15, border_width=1, border_color=Theme.BORDER)
        card.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(card, text=title, font=Theme.FONT_SUBHEADER, text_color=Theme.ACCENT).pack(anchor="w", padx=20, pady=(15, 10))
        return card

    def create_auth_card(self):
        card = self.create_card("AUTHENTICATION")
        
        ctk.CTkLabel(card, text="Discord User Token:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_SUB).pack(anchor="w", padx=20)
        self.app.token_entry = ctk.CTkEntry(card, placeholder_text="Enter your Discord token here...", show="*", height=40, fg_color=Theme.INPUT_BG, border_color=Theme.BORDER)
        self.app.token_entry.pack(fill="x", padx=20, pady=(2, 10))

        ctk.CTkLabel(card, text="Webhook URL:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_SUB).pack(anchor="w", padx=20)
        self.app.webhook_entry = ctk.CTkEntry(card, placeholder_text="https://discord.com/api/webhooks/...", height=40, fg_color=Theme.INPUT_BG, border_color=Theme.BORDER)
        self.app.webhook_entry.pack(fill="x", padx=20, pady=(2, 15))

    def create_biomes_card(self):
        card = self.create_card("TARGET BIOMES")
        container = ctk.CTkFrame(card, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=5)
        
        biomes_list = ["Glitched", "Cyberspace", "Dreamspace", "Null", "Starfall", "Hell", "Corruption", "Heaven"]
        for i, biome in enumerate(biomes_list):
            var = ctk.StringVar(value="off")
            self.app.biome_vars[biome] = var
            ctk.CTkSwitch(container, text=biome, variable=var, onvalue="on", offvalue="off", progress_color=Theme.ACCENT, font=Theme.FONT_BODY).grid(row=i // 3, column=i % 3, padx=15, pady=12, sticky="w")

    def create_merchants_card(self):
        card = self.create_card("TARGET MERCHANTS")
        container = ctk.CTkFrame(card, fg_color="transparent")
        container.pack(fill="x", padx=20, pady=5)
        
        merchants_list = ["Jester", "Mari"]
        for i, merchant in enumerate(merchants_list):
            var = ctk.StringVar(value="off")
            self.app.merchant_vars[merchant] = var
            ctk.CTkSwitch(container, text=merchant, variable=var, onvalue="on", offvalue="off", progress_color=Theme.ACCENT, font=Theme.FONT_BODY).grid(row=0, column=i, padx=15, pady=10, sticky="w")

    def create_controls(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=30, pady=10)
        
        self.app.auto_kill_var = ctk.StringVar(value="off")
        ctk.CTkSwitch(frame, text="Auto-Kill Roblox Process", variable=self.app.auto_kill_var, onvalue="on", offvalue="off", progress_color=Theme.ACCENT, font=Theme.FONT_BODY).pack(side="left")

        ctk.CTkButton(self, text="SAVE SETTINGS", command=self.app.save_config, fg_color=Theme.HOVER, height=40, font=Theme.FONT_SUBHEADER).pack(fill="x", padx=30, pady=(10, 5))
        self.app.start_btn = ctk.CTkButton(self, text="START SNIPER ENGINE", command=self.app.toggle_sniper, fg_color=Theme.ACCENT, hover_color=Theme.ACCENT_HOVER, height=50, font=("Arial", 14, "bold"))
        self.app.start_btn.pack(fill="x", padx=30, pady=(5, 30))


class SolHunterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SolHunter v1.0")
        self.geometry("900x650")
        self.resizable(True, True)
        self.configure(fg_color=Theme.BG)
        
        # Grid Layout: Sidebar (0) | Content (1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # State & Logic
        self.listener: DiscordListener | None = None
        self.loggerDetector = LoggerDetector(logCallback=self.log_message)
        self.is_running = False
        self.is_afk_running = False
        self.antiAFK = AntiAFK(log_callback=self.log_message)
        self.biome_vars: Dict[str, ctk.StringVar] = {}
        self.merchant_vars: Dict[str, ctk.StringVar] = {}

        # Components
        self.sidebar = Sidebar(self, self.select_page)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.grid(row=0, column=1, sticky="nsew")
        self.content_area.grid_columnconfigure(0, weight=1)
        self.content_area.grid_rowconfigure(0, weight=1)

        # Pages
        self.pages = {}
        self.create_pages()
        
        # Init
        self.load_config()
        self.select_page("Dashboard")
        self.show_toast("System Initialized", duration=2000, color=Theme.SUCCESS)

    def create_pages(self):
        # Dashboard
        self.pages["Dashboard"] = DashboardPage(self.content_area, self)
        
        # AFK
        self.pages["AFK Mode"] = self.create_afk_page()
        
        # Logs
        self.pages["Live Logs"] = self.create_logs_page()
        
        # Guide
        self.pages["User Guide"] = self.create_guide_page()

    def create_afk_page(self):
        page = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent", corner_radius=0)
        
        ctk.CTkLabel(page, text="AFK AUTOMATION", font=Theme.FONT_HEADER, text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=30, pady=(30, 5))
        ctk.CTkLabel(page, text="Automated background detection via logs.", font=Theme.FONT_BODY, text_color=Theme.TEXT_SUB).pack(anchor="w", padx=30, pady=(0, 20))
        
        # Settings Card
        setting_card = ctk.CTkFrame(page, fg_color=Theme.CARD, corner_radius=15, border_width=1, border_color=Theme.BORDER)
        setting_card.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(setting_card, text="DETECTION SETTINGS", font=Theme.FONT_SUBHEADER, text_color=Theme.ACCENT).pack(anchor="w", padx=20, pady=(15, 10))
        
        self.log_detection_var = ctk.StringVar(value="off")
        ctk.CTkSwitch(setting_card, text="Enable Log Detection", variable=self.log_detection_var, onvalue="on", offvalue="off", progress_color=Theme.ACCENT, font=Theme.FONT_BODY).pack(anchor="w", padx=20, pady=5)
        
        self.antiafk_var = ctk.StringVar(value="off")
        ctk.CTkSwitch(setting_card, text="Smart Anti-AFK (Jump)", variable=self.antiafk_var, onvalue="on", offvalue="off", progress_color=Theme.ACCENT, font=Theme.FONT_BODY).pack(anchor="w", padx=20, pady=5)
        
        ctk.CTkLabel(setting_card, text="Account Name:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_SUB).pack(anchor="w", padx=20)
        self.afk_account_entry = ctk.CTkEntry(setting_card, placeholder_text="Username...", height=40, fg_color=Theme.INPUT_BG, border_color=Theme.BORDER)
        self.afk_account_entry.pack(fill="x", padx=20, pady=(2, 10))
        
        ctk.CTkLabel(setting_card, text="AFK Webhook URL:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_SUB).pack(anchor="w", padx=20)
        self.afk_webhook_entry = ctk.CTkEntry(setting_card, placeholder_text="URL...", height=40, fg_color=Theme.INPUT_BG, border_color=Theme.BORDER)
        self.afk_webhook_entry.pack(fill="x", padx=20, pady=(2, 10))

        ctk.CTkLabel(setting_card, text="Min Roll Rarity (e.g. 1000000):", font=Theme.FONT_SMALL, text_color=Theme.TEXT_SUB).pack(anchor="w", padx=20)
        self.min_roll_entry = ctk.CTkEntry(setting_card, placeholder_text="1000000", height=40, fg_color=Theme.INPUT_BG, border_color=Theme.BORDER)
        self.min_roll_entry.pack(fill="x", padx=20, pady=(2, 15))

        # Tools Card
        tool_card = ctk.CTkFrame(page, fg_color=Theme.CARD, corner_radius=15, border_width=1, border_color=Theme.BORDER)
        tool_card.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(tool_card, text="OPTIMIZATION TOOLS", font=Theme.FONT_SUBHEADER, text_color=Theme.ACCENT).pack(anchor="w", padx=20, pady=(15, 10))
        
        ctk.CTkButton(tool_card, text="APPLY ROBLOX FASTFLAGS (LOWER CPU)", command=self.applyFastFlags, fg_color=Theme.HOVER, height=40).pack(fill="x", padx=20, pady=(5, 15))

        self.afk_start_btn = ctk.CTkButton(page, text="START AFK DETECTION", command=self.toggle_afk_mode, fg_color=Theme.ACCENT, height=50, font=("Arial", 14, "bold"))
        self.afk_start_btn.pack(fill="x", padx=30, pady=(20, 30))
        return page

    def create_logs_page(self):
        page = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.console = ctk.CTkTextbox(page, fg_color=Theme.CONSOLE_BG, text_color="#00ff00", font=("Consolas", 12), corner_radius=10, border_width=1, border_color=Theme.BORDER)
        self.console.pack(fill="both", expand=True, padx=30, pady=30)
        return page

    def create_guide_page(self):
        page = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.guide_box = ctk.CTkTextbox(page, fg_color=Theme.CARD, text_color=Theme.TEXT_MAIN, font=("Consolas", 13), corner_radius=10, border_width=1, border_color=Theme.BORDER)
        self.guide_box.pack(fill="both", expand=True, padx=30, pady=30)
        self.guide_box.insert("1.0", """SOLHUNTER USER GUIDE

SECTION 1: DISCORD SNIPER SETUP
1. Get Discord Token: Open Discord in Browser, press F12, go to Network tab. Filter for '/api/v9/users/@me'. Copy the 'authorization' value from headers.
2. Target Channels: The engine monitors pre-configured community channels for server links.
3. Target Filters: Toggle specific Biomes or Merchants in the Dashboard to filter alerts.
4. Auto-Kill: Closes active Roblox windows before launching a new session.

SECTION 2: AFK MODE SETUP
1. Log Detection: Reads local Roblox logs for events like Biome changes or rare Aura rolls.
2. Account Name: Set your Roblox username for custom webhook reports.
3. Webhook: Input a Discord Webhook URL for remote notifications.
4. Smart Anti-AFK: Randomized jump simulation to bypass the 20-minute idle kick.
5. FastFlags: Applies low-resource settings to optimize game performance.

SECTION 3: OPERATION
1. Sniper Engine: Controls the automated server joining logic.
2. AFK Engine: Controls local monitoring and anti-timeout tasks.
3. Live Logs: Displays real-time status and error reporting.

WARNING
Keep your Discord Token private. Sharing it compromises your account security.""")
        self.guide_box.configure(state="disabled")
        return page

    def select_page(self, name):
        # Update Sidebar
        page_search_name = "Guide" if name == "User Guide" else ("Logs" if name == "Live Logs" else ("AFK" if name == "AFK Mode" else name))
        self.sidebar.set_active(name)
        
        # Show Page
        for page in self.pages.values():
            page.grid_forget()
        
        if name in self.pages:
            self.pages[name].grid(row=0, column=0, sticky="nsew")

    # --- LOGIC SECTIONS ---
    
    def log_message(self, message: str):
        if not hasattr(self, 'console'): return
        self.after(0, lambda: [self.console.configure(state="normal"), self.console.insert("end", f"> {message}\n"), self.console.see("end"), self.console.configure(state="disabled")])

    def show_toast(self, message: str, duration=2500, color=None):
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
                new_alpha = alpha + (0.1 if target == 1.0 else -0.1)
                toast.attributes("-alpha", max(0, min(1, new_alpha)))
                self.after(16, lambda: fade(new_alpha, target))
            elif target == 1.0:
                self.after(duration, lambda: fade(1.0, 0.0))
            else:
                toast.destroy()
        fade(0.0, 1.0)

    # --- CONFIGURATION & ACTIONS ---

    def load_config(self):
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
            
        config = {**defaults, **loaded} # Merge
        
        # Apply to GUI
        if self.token_entry: self.token_entry.insert(0, config.get("discord_token", ""))
        if self.webhook_entry: self.webhook_entry.insert(0, config.get("webhook_url", ""))
        if self.afk_webhook_entry: self.afk_webhook_entry.insert(0, config.get("afk_webhook_url", ""))
        if self.afk_account_entry: self.afk_account_entry.insert(0, config.get("afk_account_name", ""))
        if self.min_roll_entry: self.min_roll_entry.insert(0, str(config.get("min_roll_rarity", 1000000)))
        self.auto_kill_var.set("on" if config.get("auto_kill_roblox", False) else "off")
        self.log_detection_var.set("on" if config.get("log_detection", False) else "off")
        self.antiafk_var.set("on" if config.get("antiafk_enabled", False) else "off")
        
        saved_biomes = config.get("biomes", {})
        for biome, var in self.biome_vars.items():
            if saved_biomes.get(biome, False): var.set("on")
            
        saved_merchants = config.get("merchants", {})
        for merchant, var in self.merchant_vars.items():
            if saved_merchants.get(merchant, False): var.set("on")

    def save_config(self):
        config = {
            "discord_token": self.token_entry.get(),
            "webhook_url": self.webhook_entry.get(),
            "auto_kill_roblox": (self.auto_kill_var.get() == "on"),
            "log_detection": (self.log_detection_var.get() == "on"),
            "afk_webhook_url": self.afk_webhook_entry.get().strip(),
            "afk_account_name": self.afk_account_entry.get().strip(),
            "min_roll_rarity": int(self.min_roll_entry.get() or 1000000),
            "antiafk_enabled": (self.antiafk_var.get() == "on"),
            "target_channels": [1282542323590496277, 1282543762425516083],
            "biomes": {b: (v.get() == "on") for b, v in self.biome_vars.items()},
            "merchants": {m: (v.get() == "on") for m, v in self.merchant_vars.items()}
        }
        with open(CONFIG_FILE, "w") as f: json.dump(config, f, indent=4)
        self.show_toast("Settings Saved", color=Theme.SUCCESS)
        self.log_message("Configuration saved successfully.")

    def toggle_sniper(self):
        if self.is_running: self.stop_sniper()
        else: self.start_sniper()

    def start_sniper(self):
        token = self.token_entry.get().strip()
        if not token: self.log_message("Error: Token required."); return
        try:
            self.save_config() # Auto save
            channels = [1282542323590496277, 1282543762425516083]
            active_biomes = [b for b, v in self.biome_vars.items() if v.get() == "on"]
            active_merchants = [m for m, v in self.merchant_vars.items() if v.get() == "on"]
            
            self.listener = DiscordListener(
                token=token, 
                target_channels=channels, 
                active_biomes=active_biomes, 
                active_merchants=active_merchants, 
                webhook_url=self.webhook_entry.get().strip(), 
                auto_kill=(self.auto_kill_var.get() == "on"), 
                log_callback=self.log_message
            )
            self.listener.start_listening()
            self.is_running = True
            
            # UI Updates
            self.start_btn.configure(text="STOP SNIPER ENGINE", fg_color=Theme.ERROR, hover_color=Theme.ERROR_HOVER)
            self.sidebar.update_status(True, "SNIPING")
            self.show_toast("Sniper Engine Engaged!", color=Theme.SUCCESS)
        except Exception as e: self.log_message(f"Error: {e}")

    def stop_sniper(self):
        if self.listener: self.listener.stop_listening(); self.listener = None
        self.is_running = False
        self.start_btn.configure(text="START SNIPER ENGINE", fg_color=Theme.ACCENT, hover_color=Theme.ACCENT_HOVER)
        self.sidebar.update_status(False, "IDLE")
        self.show_toast("Sniper Disengaged", color=Theme.ERROR)
        self.log_message("Sniper Engine Stopped.")

    def toggle_afk_mode(self):
        if self.is_afk_running:
            if self.loggerDetector: self.loggerDetector.stopDetection()
            if self.antiAFK: self.antiAFK.stop()
            self.is_afk_running = False
            self.afk_start_btn.configure(text="START AFK DETECTION", fg_color=Theme.ACCENT, hover_color=Theme.ACCENT_HOVER)
            self.sidebar.update_status(False, "IDLE")
            self.show_toast("AFK Mode Stopped", color=Theme.ERROR)
            self.log_message("AFK Mode Stopped.")
        else:
            if self.log_detection_var.get() == "on":
                try:
                    min_rarity = int(self.min_roll_entry.get() or 1000000)
                except:
                    min_rarity = 1000000
                
                self.loggerDetector.startDetection(
                    webhookUrl=self.afk_webhook_entry.get().strip(), 
                    accountName=self.afk_account_entry.get().strip(),
                    minRollRarity=min_rarity
                )
                
                if self.antiafk_var.get() == "on":
                    self.antiAFK.start()

                self.is_afk_running = True
                self.afk_start_btn.configure(text="STOP AFK DETECTION", fg_color=Theme.ERROR, hover_color=Theme.ERROR_HOVER)
                self.sidebar.update_status(True, "AFK MONITORING")
                self.show_toast("AFK Mode Active", color=Theme.SUCCESS)
                self.log_message("AFK Mode Started.")
            else:
                self.log_message("Enable 'Log Detection' first.")
                self.show_toast("Enable Log Detection First", color=Theme.ERROR)

    def applyFastFlags(self):
        if self.loggerDetector.applyFastFlags():
            self.show_toast("Flags Applied - Restarting...", color=Theme.SUCCESS)
            kill_roblox()
            self.after(2000, lambda: launch_roblox(place_id="15532592330"))
            self.log_message("FastFlags applied. Relaunching...")
        else:
            self.show_toast("Failed to apply Flags", color=Theme.ERROR)

if __name__ == "__main__":
    app = SolHunterApp()
    app.mainloop()
