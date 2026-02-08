import discord
import threading
import asyncio
import logging
from typing import Callable, Optional
from .parser import MessageParser
from .launcher import launchRoblox

class DiscordListener(discord.Client):
    def __init__(self, token: str, targetChannels: list[int], activeBiomes: list[str], activeMerchants: list[str] = [], webhookUrl: str = "", autoKill: bool = False, logCallback: Optional[Callable[[str], None]] = None):
        super().__init__(
            chunk_guilds_at_startup=False,
            member_cache_flags=discord.MemberCacheFlags.none()
        )
        self.token = token.strip()
        self.targetChannels = set(targetChannels)
        self.activeBiomes = activeBiomes
        self.activeMerchants = activeMerchants
        self.webhookUrl = webhookUrl
        self.autoKill = autoKill
        self.logCallback = logCallback
        self.thread = threading.Thread(target=self.runClient, daemon=True, name="DiscordListenerThread")
        self.isProcessing = False

    def sendWebhookNotification(self, targetName: str, link: str, keyword: str, message: discord.Message, isMerchant: bool = False):
        if not self.webhookUrl:
            return
            
        import requests
        from datetime import datetime
        
        color = 7101671
        if "Glitched" in targetName:
            color = 0xa349a4
        elif "Cyber" in targetName:
            color = 0x00a2ed
        elif isMerchant:
            color = 0xff4757

        now = datetime.now()
        timestampStr = now.strftime("%I:%M %p")
        
        data = {
            "username": "SolHunter",
            "embeds": [{
                "author": {
                    "name": f"{message.author.name} ({message.author.display_name})",
                    "icon_url": str(message.author.avatar.url) if message.author.avatar else None
                },
                "title": f"{targetName.upper()} Detected — Today at {timestampStr}",
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
                    "text": f"ID: {message.id} • Today at {timestampStr}"
                }
            }]
        }
        
        try:
            requests.post(self.webhookUrl, json=data, timeout=5)
        except Exception as e:
            self.log(f"Webhook Error: {e}")

    def log(self, message: str):
        logging.info(message)
        if self.logCallback:
            self.logCallback(message)

    def runClient(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self.start(self.token))
        except Exception as e:
            self.log(f"Listener Error: {e}")
        finally:
            if not loop.is_closed():
                loop.close()

    def startListening(self):
        if not self.thread.is_alive():
            self.thread.start()
            self.log("Listener thread started...")

    def stopListening(self):
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
        self.log(f"Monitoring {len(self.targetChannels)} channels.")
        self.sendStartWebhook()

    def sendStartWebhook(self):
        if not self.webhookUrl:
            return
            
        import requests
        from datetime import datetime
        now = datetime.now()
        timestampStr = now.strftime("%I:%M %p")
        
        data = {
            "username": "SolHunter",
            "embeds": [{
                "title": "SolHunter STARTED",
                "description": "Tool is now online!",
                "color": 0x10b981,
                "fields": [
                    {
                        "name": "Status", 
                        "value": "`GLOBAL ONLINE`", 
                        "inline": True
                    },
                    {
                        "name": "Monitoring", 
                        "value": f"`{len(self.targetChannels)} Channels`", 
                        "inline": True
                    },
                    {
                        "name": "Authenticated As",
                        "value": f"`{self.user.name}`",
                        "inline": False
                    }
                ],
                "footer": {
                    "text": f"SolHunter v1.0 • Today at {timestampStr}"
                }
            }]
        }
        
        try:
            requests.post(self.webhookUrl, json=data, timeout=5)
        except:
            pass

    async def on_message(self, message: discord.Message):
        if message.channel.id not in self.targetChannels:
            return

        contentToCheck = message.content or ""
        
        for embed in message.embeds:
            if embed.title: contentToCheck += " " + embed.title
            if embed.description: contentToCheck += " " + embed.description
            if embed.fields:
                for field in embed.fields:
                    contentToCheck += f" {field.name} {field.value}"

        if not contentToCheck.strip():
            return

        detectedBiome = MessageParser.checkBiomes(contentToCheck, self.activeBiomes)
        detectedMerchant = MessageParser.checkMerchants(contentToCheck, self.activeMerchants)
        
        targetName = detectedBiome or detectedMerchant
        if not targetName:
            return

        linkData = MessageParser.extractLinkData(contentToCheck)
        if not linkData:
            for embed in message.embeds:
                linkData = MessageParser.extractLinkData(embed.description or "")
                if linkData: break
                for field in embed.fields:
                    linkData = MessageParser.extractLinkData(field.value or "")
                    if linkData: break
                if linkData: break

        if not linkData:
            self.log(f"[{targetName}] Detected (No Link found)")
            return

        asyncio.create_task(self.processSnipe(targetName, linkData, detectedMerchant is not None, message, detectedBiome or detectedMerchant))

    async def processSnipe(self, targetName: str, linkData: dict, isMerchant: bool, message: discord.Message, keyword: str):
        if self.isProcessing:
            return
            
        self.isProcessing = True
        try:
            placeId = linkData.get('placeId')
            linkCode = linkData.get('linkCode')
            jobId = linkData.get('jobId')
            launchDataString = linkData.get('launchData')
            linkType = linkData.get('type', 'private_server')
            
            if linkType == "share_code":
                fullLink = f"https://www.roblox.com/share?code={linkCode}&type=Server"
            elif linkType == "job_id":
                fullLink = f"JobID: {jobId}"
            elif linkCode:
                fullLink = f"https://www.roblox.com/games/{placeId}?privateServerLinkCode={linkCode}"
            else:
                fullLink = f"Roblox Game ID: {placeId}"

            self.log(f"SNIPED [{targetName}]! Launching ({linkType})...")
            
            await asyncio.to_thread(
                launchRoblox,
                placeId=placeId,
                linkCode=linkCode,
                jobId=jobId,
                launchData=launchDataString,
                autoKill=self.autoKill,
                linkType=linkType
            )
            
            self.sendWebhookNotification(targetName, fullLink, keyword, message, isMerchant=isMerchant)

        except Exception as e:
            self.log(f"Snipe Error: {e}")
        finally:
            self.isProcessing = False
