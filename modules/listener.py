import discord
import threading
import asyncio
import logging
from typing import Callable, Optional
from .parser import MessageParser
from .launcher import launch_roblox

class DiscordListener(discord.Client):
    """
    Discord Client (Self-bot) running in a separate thread.
    """
    def __init__(self, token: str, target_channels: list[int], active_biomes: list[str], webhook_url: str = "", auto_kill: bool = False, log_callback: Optional[Callable[[str], None]] = None):
        super().__init__()
        self.token = token
        self.target_channels = set(target_channels) # Optimize lookup
        self.active_biomes = active_biomes
        self.webhook_url = webhook_url
        self.auto_kill = auto_kill
        self.log_callback = log_callback
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_client, daemon=True, name="DiscordListenerThread")
        self._stop_event = asyncio.Event()

    def send_webhook_notification(self, biome: str, link: str):
        """Sends a notification to the Discord Webhook."""
        if not self.webhook_url:
            return
            
        import requests
        data = {
            "embeds": [{
                "title": "🎯 Biome Sniped!",
                "color": 7101671, # Purple
                "fields": [
                    {"name": "Biome", "value": biome, "inline": True},
                    {"name": "Link", "value": f"[Join Server]({link})", "inline": False}
                ],
                "footer": {"text": "SOLS HUNTER v1.0"}
            }]
        }
        try:
            requests.post(self.webhook_url, json=data, timeout=5)
        except Exception as e:
            self.log(f"Webhook Error: {e}")

    def log(self, message: str):
        """Emits a log message to the logger and the callback."""
        logging.info(message)
        if self.log_callback:
            self.log_callback(message)

    def _run_client(self):
        """Entry point for the thread."""
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.start(self.token))
        except Exception as e:
            self.log(f"Listener Error: {e}")
        finally:
            self.loop.close()

    def start_listening(self):
        """Starts the client thread."""
        if not self.thread.is_alive():
            self.thread.start()
            self.log("Listener thread started...")

    def stop_listening(self):
        """Stops the client."""
        # This is a bit tricky with asyncio in a thread. 
        # For a simple self-bot, logging out or closing the loop is needed.
        if self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self.close(), self.loop)
            self.log("Stopping listener...")

    async def on_ready(self):
        self.log(f"Logged in as {self.user} (ID: {self.user.id})")
        self.log(f"Monitoring {len(self.target_channels)} channels for {len(self.active_biomes)} biomes.")

    async def on_message(self, message: discord.Message):
        if message.channel.id not in self.target_channels:
            return

        detected_biome = MessageParser.check_biomes(message.content, self.active_biomes)
        if not detected_biome:
            return

        link_data = MessageParser.extract_link_data(message.content)
        if not link_data:
            self.log(f"[{detected_biome}] Detected (No Link)")
            return

        full_link = f"https://www.roblox.com/games/{link_data['place_id']}?privateServerLinkCode={link_data['link_code']}"
        
        launch_roblox(
            place_id=link_data['place_id'],
            link_code=link_data['link_code'],
            auto_kill=self.auto_kill
        )
        
        self.log(f"⚡ SNIPED [{detected_biome}]! Launching...")
        self.send_webhook_notification(detected_biome, full_link)
