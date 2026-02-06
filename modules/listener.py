import discord
import threading
import asyncio
import logging
from typing import Callable, Optional
from .parser import MessageParser
from .launcher import launch_roblox

class DiscordListener(discord.Client):
    """
    Optimized Discord Client (Self-bot) following sniper-v3 patterns.
    """
    def __init__(self, token: str, target_channels: list[int], active_biomes: list[str], active_merchants: list[str] = [], webhook_url: str = "", auto_kill: bool = False, log_callback: Optional[Callable[[str], None]] = None):
        # Sniper-v3 uses these specific flags for optimization and stealth
        super().__init__(
            chunk_guilds_at_startup=False,
            member_cache_flags=discord.MemberCacheFlags.none()
        )
        self.token = token.strip()
        self.target_channels = set(target_channels)
        self.active_biomes = active_biomes
        self.active_merchants = active_merchants
        self.webhook_url = webhook_url
        self.auto_kill = auto_kill
        self.log_callback = log_callback
        self.thread = threading.Thread(target=self._run_client, daemon=True, name="DiscordListenerThread")
        self.is_processing = False

    def send_webhook_notification(self, target_name: str, link: str, keyword: str, message: discord.Message, is_merchant: bool = False):
        """Sends a premium notification to the Discord Webhook (Matching user reference)."""
        if not self.webhook_url:
            return
            
        import requests
        from datetime import datetime
        
        color = 7101671 # Default Purple
        icon = ""
        if "Glitched" in target_name:
            color = 0xa349a4
        elif "Cyber" in target_name:
            color = 0x00a2ed
        elif is_merchant:
            color = 0xff4757

        now = datetime.now()
        timestamp_str = now.strftime("%I:%M %p")
        
        # Build the premium embed payload
        data = {
            "username": "SolHunter",
            "embeds": [{
                "author": {
                    "name": f"{message.author.name} ({message.author.display_name})",
                    "icon_url": str(message.author.avatar.url) if message.author.avatar else None
                },
                "title": f"{target_name.upper()} Detected — Today at {timestamp_str}",
                "description": f"### [ [Click to Join Server]( {link} ) ]",
                "color": color,
                "fields": [
                    {
                        "name": "Keyword",
                        "value": f"`{keyword}`",
                        "inline": True
                    },
                    {
                        "name": "Owns Roblox Account?",
                        "value": "Yes",
                        "inline": True
                    },
                    {
                        "name": "Original Message Link",
                        "value": f"[Sol's RNG › 💬]({message.jump_url})",
                        "inline": False
                    },
                    {
                        "name": "Original Message",
                        "value": f"```\n{message.content[:500] if message.content else 'Embed Content Only'}\n```",
                        "inline": False
                    }
                ],
                "footer": {
                    "text": f"ID: {message.id} • Today at {timestamp_str}"
                }
            }]
        }
        
        try:
            requests.post(self.webhook_url, json=data, timeout=5)
        except Exception as e:
            self.log(f"Webhook Error: {e}")


    def log(self, message: str):
        """Emits a log message."""
        logging.info(message)
        if self.log_callback:
            self.log_callback(message)

    def _run_client(self):
        """
        Entry point for the thread, using the exact logic from sniper-v3.
        Instead of self.run(), we use a manual event loop and self.start().
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # sniper-v3 calls start() directly on the client
            loop.run_until_complete(self.start(self.token))
        except Exception as e:
            self.log(f"Listener Error: {e}")
            if "Improper token has been passed" in str(e):
                self.log("CRITICAL: Improper token. Ensure you are using discord.py-self and NOT the official discord.py.")
        finally:
            if not loop.is_closed():
                loop.close()

    def start_listening(self):
        """Starts the client thread."""
        if not self.thread.is_alive():
            self.thread.start()
            self.log("Listener thread started...")

    def stop_listening(self):
        """Stops the client safely."""
        try:
            loop = getattr(self, 'loop', None)
            if loop and loop.is_running():
                asyncio.run_coroutine_threadsafe(self.close(), loop)
                self.log("Stopping listener...")
        except:
            pass
        self.log("Sniper Stopped.")

    async def on_ready(self):
        self.log(f"Logged in as {self.user} (ID: {self.user.id})")
        self.log(f"Monitoring {len(self.target_channels)} channels.")
        self.sendStartWebhook()

    def sendStartWebhook(self):
        """Sends a premium 'Tool Started' notification."""
        if not self.webhook_url:
            return
            
        import requests
        from datetime import datetime
        now = datetime.now()
        timestamp_str = now.strftime("%I:%M %p") # Changed to 12-hour format
        
        data = {
            "username": "SolHunter",
            "embeds": [{
                "title": "SolHunter STARTED",
                "description": "Tool is now online!",
                "color": 0x10b981, # Success Green
                "fields": [
                    {
                        "name": "Status", 
                        "value": "`GLOBAL ONLINE`", 
                        "inline": True
                    },
                    {
                        "name": "Monitoring", 
                        "value": f"`{len(self.target_channels)} Channels`", 
                        "inline": True
                    },
                    {
                        "name": "Authenticated As",
                        "value": f"`{self.user.name}`",
                        "inline": False
                    }
                ],
                "footer": {
                    "text": f"SolHunter v1.0 • Today at {timestamp_str}"
                }
            }]
        }
        
        try:
            requests.post(self.webhook_url, json=data, timeout=5)
        except:
            pass

    async def on_message(self, message: discord.Message):
        if message.channel.id not in self.target_channels:
            return

        # sniper-v3 checks embeds too. Many bots send biome updates in embeds.
        content_to_check = message.content or ""
        
        # Collect all text from embeds
        for embed in message.embeds:
            if embed.title: content_to_check += " " + embed.title
            if embed.description: content_to_check += " " + embed.description
            if embed.fields:
                for field in embed.fields:
                    content_to_check += f" {field.name} {field.value}"

        if not content_to_check.strip():
            return

        detected_biome = MessageParser.check_biomes(content_to_check, self.active_biomes)
        detected_merchant = MessageParser.check_merchants(content_to_check, self.active_merchants)
        
        target_name = detected_biome or detected_merchant
        if not target_name:
            return

        # Extract link from content or embeds
        link_data = MessageParser.extract_link_data(content_to_check)
        if not link_data:
            # If no link in content, check each embed field/description specifically
            for embed in message.embeds:
                link_data = MessageParser.extract_link_data(embed.description or "")
                if link_data: break
                for field in embed.fields:
                    link_data = MessageParser.extract_link_data(field.value or "")
                    if link_data: break
                if link_data: break

        if not link_data:
            self.log(f"[{target_name}] Detected (No Link found in content/embeds)")
            return

        # Found target and link!
        asyncio.create_task(self._process_snipe(target_name, link_data, detected_merchant is not None, message, detected_biome or detected_merchant))


    async def _process_snipe(self, target_name: str, link_data: dict, is_merchant: bool, message: discord.Message, keyword: str):
        """Processes the actual snipe logic asynchronously."""
        if self.is_processing:
            return
            
        self.is_processing = True
        try:
            place_id = link_data['place_id']
            link_code = link_data['link_code']
            link_type = link_data.get('type', 'private_server')
            
            if link_type == "share_code":
                full_link = f"https://www.roblox.com/share?code={link_code}&type=Server"
            else:
                full_link = f"https://www.roblox.com/games/{place_id}?privateServerLinkCode={link_code}"

            self.log(f"SNIPED [{target_name}]! Launching ({link_type})...")
            
            # Use threading for blocking call
            await asyncio.to_thread(
                launch_roblox,
                place_id=place_id,
                link_code=link_code,
                auto_kill=self.auto_kill,
                link_type=link_type
            )
            
            self.send_webhook_notification(target_name, full_link, keyword, message, is_merchant=is_merchant)

        except Exception as e:
            self.log(f"Snipe Error: {e}")
        finally:
            self.is_processing = False

