import customtkinter as ctk
import json
import os
import threading
from modules.listener import DiscordListener
from typing import Dict, Optional

# Configuration Constants
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Configuration Path Setup
def get_config_path():
    appdata = os.getenv('APPDATA')
    local_config = "config.json"
    if not appdata: return local_config
    config_dir = os.path.join(appdata, "SolsHunter")
    target_config = os.path.join(config_dir, "config.json")
    if not os.path.exists(config_dir): os.makedirs(config_dir)
    return target_config

CONFIG_FILE = get_config_path()

# Theme Colors
COLOR_BG = "#1a1a1a"
COLOR_SIDEBAR = "#141414"
COLOR_ACCENT = "#6c5ce7"
COLOR_TEXT_MAIN = "#ffffff"
COLOR_TEXT_SUB = "#b2bec3"
COLOR_CONSOLE_BG = "#000000"

class SolHunterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SOLS HUNTER v1.0")
        self.geometry("800x600")
        self.resizable(False, False)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.config = self.load_config()
        self.listener: DiscordListener | None = None
        self.is_running = False
        self.biome_vars: Dict[str, ctk.StringVar] = {}

        self.setup_sidebar()
        self.setup_pages()
        self.select_page("Dashboard")
        self.load_gui_from_config()

    def load_config(self) -> dict:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f: return json.load(f)
            except: pass
        return {"discord_token": "", "target_channels": [], "biomes": {}, "webhook_url": "", "auto_kill_roblox": False}

    def save_config(self):
        self.config["discord_token"] = self.token_entry.get()
        self.config["webhook_url"] = self.webhook_entry.get()
        self.config["auto_kill_roblox"] = (self.auto_kill_var.get() == "on")
        channels_str = self.channel_entry.get().strip()
        try:
            self.config["target_channels"] = [int(x.strip()) for x in channels_str.split(",") if x.strip().isdigit()]
        except: pass
        for biome, var in self.biome_vars.items():
            self.config["biomes"][biome] = (var.get() == "on")
        with open(CONFIG_FILE, "w") as f: json.dump(self.config, f, indent=4)
        self.log_message("Configuration saved.")

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=COLOR_SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(self.sidebar, text="SOLS HUNTER v1.0", font=ctk.CTkFont(size=20, weight="bold"), text_color=COLOR_ACCENT).grid(row=0, column=0, padx=20, pady=(30, 10))
        
        self.status_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.status_frame.grid(row=1, column=0, padx=20, pady=0, sticky="w")
        self.status_dot = ctk.CTkLabel(self.status_frame, text="●", text_color="#ff5555", font=("Arial", 16))
        self.status_dot.pack(side="left")
        self.status_text = ctk.CTkLabel(self.status_frame, text="Status: IDLE", text_color=COLOR_TEXT_SUB, font=("Arial", 12))
        self.status_text.pack(side="left", padx=(5, 0))

        self.btn_dash = ctk.CTkButton(self.sidebar, text="Dashboard", fg_color="transparent", text_color=COLOR_TEXT_MAIN, hover_color="#2b2b2b", anchor="w", command=lambda: self.select_page("Dashboard"))
        self.btn_dash.grid(row=2, column=0, padx=20, pady=(40, 5), sticky="ew")
        self.btn_logs = ctk.CTkButton(self.sidebar, text="Live Logs", fg_color="transparent", text_color=COLOR_TEXT_MAIN, hover_color="#2b2b2b", anchor="w", command=lambda: self.select_page("Logs"))
        self.btn_logs.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        self.btn_guide = ctk.CTkButton(self.sidebar, text="Guide", fg_color="transparent", text_color=COLOR_TEXT_MAIN, hover_color="#2b2b2b", anchor="w", command=lambda: self.select_page("Guide"))
        self.btn_guide.grid(row=4, column=0, padx=20, pady=5, sticky="ew")

        ctk.CTkLabel(self.sidebar, text="Created by Night0wl", font=("Arial", 10), text_color="#444").grid(row=6, column=0, padx=20, pady=(5, 20), sticky="ew")

    def setup_pages(self):
        self.container = ctk.CTkFrame(self, fg_color=COLOR_BG, corner_radius=0)
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self.dash_page = ctk.CTkScrollableFrame(self.container, fg_color="transparent", corner_radius=0)
        cred_group = ctk.CTkFrame(self.dash_page, fg_color="#232323", corner_radius=10)
        cred_group.pack(fill="x", padx=30, pady=(30, 15))
        ctk.CTkLabel(cred_group, text="CONNECTION SETTINGS", font=("Arial", 12, "bold"), text_color=COLOR_ACCENT).pack(anchor="w", padx=20, pady=(15, 5))
        ctk.CTkLabel(cred_group, text="Discord User Token:", font=("Arial", 11), text_color=COLOR_TEXT_SUB).pack(anchor="w", padx=20)
        self.token_entry = ctk.CTkEntry(cred_group, placeholder_text="Token...", show="*", height=35, fg_color="#1a1a1a", border_color="#333")
        self.token_entry.pack(fill="x", padx=20, pady=(2, 10))
        ctk.CTkLabel(cred_group, text="Target Channel ID:", font=("Arial", 11), text_color=COLOR_TEXT_SUB).pack(anchor="w", padx=20)
        self.channel_entry = ctk.CTkEntry(cred_group, placeholder_text="ID...", height=35, fg_color="#1a1a1a", border_color="#333")
        self.channel_entry.pack(fill="x", padx=20, pady=(2, 10))
        ctk.CTkLabel(cred_group, text="Webhook URL:", font=("Arial", 11), text_color=COLOR_TEXT_SUB).pack(anchor="w", padx=20)
        self.webhook_entry = ctk.CTkEntry(cred_group, placeholder_text="URL...", height=35, fg_color="#1a1a1a", border_color="#333")
        self.webhook_entry.pack(fill="x", padx=20, pady=(2, 15))

        biome_group = ctk.CTkFrame(self.dash_page, fg_color="#232323", corner_radius=10)
        biome_group.pack(fill="both", expand=True, padx=30, pady=15)
        ctk.CTkLabel(biome_group, text="TARGET BIOMES SELECTION", font=("Arial", 12, "bold"), text_color=COLOR_ACCENT).pack(anchor="w", padx=20, pady=(15, 10))
        biomes_container = ctk.CTkFrame(biome_group, fg_color="transparent")
        biomes_container.pack(fill="both", expand=True, padx=20, pady=5)
        biomes_list = ["Glitched", "Cyberspace", "Dreamspace", "Null", "Starfall", "Hell", "Corruption", "Heaven"]
        for i, biome in enumerate(biomes_list):
            var = ctk.StringVar(value="off")
            self.biome_vars[biome] = var
            ctk.CTkSwitch(biomes_container, text=biome, variable=var, onvalue="on", offvalue="off", progress_color=COLOR_ACCENT).grid(row=i // 3, column=i % 3, padx=15, pady=12, sticky="w")

        ctrl_frame = ctk.CTkFrame(self.dash_page, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=30, pady=5)
        self.auto_kill_var = ctk.StringVar(value="off")
        ctk.CTkSwitch(ctrl_frame, text="Auto-Kill Roblox", variable=self.auto_kill_var, onvalue="on", offvalue="off", progress_color=COLOR_ACCENT).pack(side="left")

        ctk.CTkButton(self.dash_page, text="SAVE SETTINGS", command=self.save_config, fg_color="#444", height=40).pack(fill="x", padx=30, pady=(15, 5))
        self.start_btn = ctk.CTkButton(self.dash_page, text="START SNIPER", command=self.toggle_sniper, fg_color=COLOR_ACCENT, height=45, font=("Arial", 15, "bold"))
        self.start_btn.pack(fill="x", padx=30, pady=(5, 30))

        self.logs_page = ctk.CTkFrame(self.container, fg_color="transparent")
        self.console = ctk.CTkTextbox(self.logs_page, fg_color=COLOR_CONSOLE_BG, text_color="#00ff00", font=("Consolas", 12), corner_radius=10)
        self.console.pack(fill="both", expand=True, padx=30, pady=30)

        self.guide_page = ctk.CTkFrame(self.container, fg_color="transparent")
        self.guide_box = ctk.CTkTextbox(self.guide_page, fg_color="#232323", text_color=COLOR_TEXT_MAIN, font=("Consolas", 13), corner_radius=10)
        self.guide_box.pack(fill="both", expand=True, padx=30, pady=30)
        self.guide_box.insert("1.0", "HOW TO GET YOUR DISCORD USER TOKEN:\n1. Open Discord in Browse\n2. F12 -> Network\n3. Filter: /api/v9/users/@me\n4. Copy 'authorization' header.")
        self.guide_box.configure(state="disabled")

    def select_page(self, name):
        self.btn_dash.configure(fg_color=COLOR_ACCENT if name == "Dashboard" else "transparent")
        self.btn_logs.configure(fg_color=COLOR_ACCENT if name == "Logs" else "transparent")
        self.btn_guide.configure(fg_color=COLOR_ACCENT if name == "Guide" else "transparent")
        for page in [self.dash_page, self.logs_page, self.guide_page]: page.grid_forget()
        if name == "Dashboard": self.dash_page.grid(row=0, column=0, sticky="nsew")
        elif name == "Logs": self.logs_page.grid(row=0, column=0, sticky="nsew")
        elif name == "Guide": self.guide_page.grid(row=0, column=0, sticky="nsew")

    def load_gui_from_config(self):
        self.token_entry.insert(0, self.config.get("discord_token", ""))
        self.webhook_entry.insert(0, self.config.get("webhook_url", ""))
        self.auto_kill_var.set("on" if self.config.get("auto_kill_roblox", False) else "off")
        channels = self.config.get("target_channels", [])
        if channels: self.channel_entry.insert(0, ", ".join(map(str, channels)))
        saved_biomes = self.config.get("biomes", {})
        for biome, var in self.biome_vars.items():
            if saved_biomes.get(biome, False): var.set("on")

    def log_message(self, message: str):
        self.after(0, lambda: [self.console.configure(state="normal"), self.console.insert("end", f"> {message}\n"), self.console.see("end"), self.console.configure(state="disabled")])

    def toggle_sniper(self):
        if self.is_running: self.stop_sniper()
        else: self.start_sniper()

    def stop_sniper(self):
        if self.listener: self.listener.stop_listening(); self.listener = None
        self.is_running = False
        self.start_btn.configure(text="START SNIPER", fg_color=COLOR_ACCENT)
        self.status_dot.configure(text_color="#ff5555")
        self.status_text.configure(text="Status: IDLE")
        self.log_message("Sniper Stopped.")

    def start_sniper(self):
        token, channel_ids = self.token_entry.get().strip(), self.channel_entry.get().strip()
        if not token or not channel_ids: self.log_message("Error: Token and Channel ID required."); return
        try:
            channels = [int(x.strip()) for x in channel_ids.split(",") if x.strip().isdigit()]
            active_biomes = [b for b, v in self.biome_vars.items() if v.get() == "on"]
            self.listener = DiscordListener(token=token, target_channels=channels, active_biomes=active_biomes, webhook_url=self.webhook_entry.get().strip(), auto_kill=(self.auto_kill_var.get() == "on"), log_callback=self.log_message)
            self.listener.start_listening()
            self.is_running = True
            self.start_btn.configure(text="STOP SNIPER", fg_color="#ff5555")
            self.status_dot.configure(text_color="#55ff55")
            self.status_text.configure(text="Status: SCANNING")
            self.save_config()
        except Exception as e: self.log_message(f"Error: {e}")

if __name__ == "__main__":
    app = SolHunterApp()
    app.mainloop()
