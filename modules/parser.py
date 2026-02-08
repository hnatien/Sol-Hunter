import re
import logging

class MessageParser:
    PS_LINK_PATTERN = re.compile(r"roblox\.com/games/(\d+)[^?]*\?.*?(?:privateServerLinkCode|linkCode|code)=([\w-]+)", re.I)
    SHARE_CODE_PATTERN = re.compile(r"(?:roblox\.com|ro\.blox\.com)/share\?code=([a-f0-9]+)", re.I)
    DEEPLINK_PATTERN = re.compile(r"(?:roblox\.com|ro\.blox\.com)/games/start\?placeId=(\d+)(?:&launchData=([^&]+))?", re.I)
    ROPRO_PATTERN = re.compile(r"https?://(?:www\.)?(?:ro\.pro|ropro\.io)/(?:join/)?([a-zA-Z0-9]+)", re.I)
    REDIRECT_PATTERN = re.compile(r"launchData=(\d+)/([a-f0-9\-]+)", re.I)
    DIRECT_ROBLOX_PATTERN = re.compile(r"roblox://placeId=(\d+)(?:&linkCode=([\w-]+))?", re.I)

    @staticmethod
    def extractLinkData(content: str) -> dict | None:
        # 1. Direct roblox:// links
        directMatch = MessageParser.DIRECT_ROBLOX_PATTERN.search(content)
        if directMatch:
            return {
                "placeId": directMatch.group(1),
                "linkCode": directMatch.group(2) if directMatch.group(2) else None,
                "type": "private_server"
            }

        # 2. Private Server Links (standard format)
        psMatch = MessageParser.PS_LINK_PATTERN.search(content)
        if psMatch:
            return {
                "placeId": psMatch.group(1),
                "linkCode": psMatch.group(2),
                "type": "private_server"
            }

        # 3. Share Codes
        shareMatch = MessageParser.SHARE_CODE_PATTERN.search(content)
        if shareMatch:
            return {
                "placeId": "15532592330", # Default to Sol's RNG
                "linkCode": shareMatch.group(1),
                "type": "share_code"
            }

        # 4. Deeplinks / LaunchData
        deepMatch = MessageParser.DEEPLINK_PATTERN.search(content)
        if deepMatch:
            placeId = deepMatch.group(1)
            launchData = deepMatch.group(2)
            
            # Check if launchData contains a redirect (PlaceID/JobID)
            if launchData:
                redirMatch = MessageParser.REDIRECT_PATTERN.search(f"launchData={launchData}")
                if redirMatch:
                    return {
                        "placeId": redirMatch.group(1),
                        "jobId": redirMatch.group(2),
                        "type": "job_id"
                    }
                return {
                    "placeId": placeId,
                    "launchData": launchData,
                    "type": "launch_data"
                }
            return {
                "placeId": placeId,
                "type": "public_server"
            }

        # 5. RoPro Links
        roproMatch = MessageParser.ROPRO_PATTERN.search(content)
        if roproMatch:
            return {
                "placeId": "15532592330", # Default to Sol's RNG
                "linkCode": roproMatch.group(1),
                "type": "ropro"
            }

        return None

    BIOME_KEYWORDS = {
        "Glitched": ["glitched", "glitch", "glig", "404", "4o4", "gl!tch"],
        "Cyberspace": ["cyberspace", "cyber", "ciber"],
        "Dreamspace": ["dreamspace", "dream", "driem"],
        "Null": ["null", "nul"],
        "Starfall": ["starfall", "star"],
        "Corruption": ["corruption", "corrupt"],
        "Hell": ["hell"],
        "Heaven": ["heaven"]
    }

    MERCHANT_KEYWORDS = {
        "Jester": ["jester", "jes", "jesster"],
        "Mari": ["mari", "marii", "lucky", "penny", "pennies"]
    }

    BLACKLIST_KEYWORDS = {"bait", "fake", "aura", "chill", "stigma", "sol", "zero", "day", "dimension"}

    @staticmethod
    def checkBiomes(content: str, activeBiomes: list[str]) -> str | None:
        contentLower = content.lower()
        
        if any(word in contentLower for word in MessageParser.BLACKLIST_KEYWORDS):
            return None
        
        # Remove URLs before checking keywords to avoid false positives in hex codes
        cleanContent = re.sub(r'https?://\S+', '', contentLower)
        
        for biome in activeBiomes:
            keywords = MessageParser.BIOME_KEYWORDS.get(biome, [biome.lower()])
            for kw in keywords:
                # Use word boundaries to match exact keywords only (e.g., "404" but not "0404" in hex)
                if re.search(rf"\b{re.escape(kw)}\b", cleanContent):
                    return biome
                
        return None

    @staticmethod
    def checkMerchants(content: str, activeMerchants: list[str]) -> str | None:
        contentLower = content.lower()
        
        if any(word in contentLower for word in MessageParser.BLACKLIST_KEYWORDS):
            return None

        cleanContent = re.sub(r'https?://\S+', '', contentLower)
        
        for merchant in activeMerchants:
            keywords = MessageParser.MERCHANT_KEYWORDS.get(merchant, [merchant.lower()])
            for kw in keywords:
                if re.search(rf"\b{re.escape(kw)}\b", cleanContent):
                    return merchant
                
        return None
