import re
import logging

class MessageParser:
    """
    Parses Discord message content to detect Biomes and extract Roblox connection details.
    """
    
    PS_LINK_PATTERN = re.compile(r"roblox\.com/games/(\d+)[^?]*\?.*privateServerLinkCode=([\w-]+)")
    SHARE_CODE_PATTERN = re.compile(r"(?:roblox\.com|ro\.blox\.com)/share\?code=([a-f0-9]+)&type=Server")
    DEEPLINK_PATTERN = re.compile(r"(?:roblox\.com|ro\.blox\.com)/games/start\?placeId=(\d+)(?:&launchData=([^&]+))?")
    ROPRO_PATTERN = re.compile(r"https?://(?:www\.)?(?:ro\.pro|ropro\.io)/(?:join/)?([a-zA-Z0-9]+)")
    REDIRECT_GAME_PATTERN = re.compile(r"launchData=(?:(\d+)/)?([a-f0-9\-]+)")

    @staticmethod
    def extract_link_data(content: str) -> dict | None:
        """
        Scans a string for various Roblox server links using robust extraction.
        """
        # 1. Standard Private Server Link & Deep Links (Improved Regex)
        # Matches both roblox.com and ro.blox.com, finds placeId and linkCode regardless of order
        ps_pattern = re.compile(r"(?:roblox\.com|ro\.blox\.com)/(?:games|games/start)\?.*?placeId=(\d+)", re.I)
        code_pattern = re.compile(r"privateServerLinkCode=([^&\s?]+)", re.I)
        
        # Matches URL with path: /games/12345/name?privateServerLinkCode=...
        path_pattern = re.compile(r"roblox\.com/games/(\d+)/[^?]*\?.*?privateServerLinkCode=([^&\s?]+)", re.I)

        # Check path format first (most common on Discord)
        path_match = path_pattern.search(content)
        if path_match:
            return {
                "place_id": path_match.group(1),
                "link_code": path_match.group(2),
                "type": "private_server"
            }

        # Check Query format (placeId=...)
        ps_match = ps_pattern.search(content)
        if ps_match:
            place_id = ps_match.group(1)
            code_match = code_pattern.search(content)
            if code_match:
                return {
                    "place_id": place_id,
                    "link_code": code_match.group(1),
                    "type": "private_server"
                }

        # 2. Share Code Link (New feature) - Ensures full code extraction
        share_match = re.search(r"(?:roblox\.com|ro\.blox\.com)/share\?code=([^&\s?]+)", content, re.I)
        if share_match:
            return {
                "place_id": "15532592330", # Sol's RNG default
                "link_code": share_match.group(1),
                "type": "share_code"
            }

        return None

    # Biome Keyword Mapping (Expanded based on user request)
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

    # Merchant Keyword Mapping
    MERCHANT_KEYWORDS = {
        "Jester": ["jester", "jes", "jesster"],
        "Mari": ["mari", "marii", "lucky", "penny", "pennies"]
    }

    BLACKLIST_KEYWORDS = {"bait", "fake", "aura", "chill", "stigma", "sol", "zero", "day", "dimension"}

    @staticmethod
    def check_biomes(content: str, active_biomes: list[str]) -> str | None:
        """Checks for active biomes in content, returning None if blacklisted."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in MessageParser.BLACKLIST_KEYWORDS):
            return None
        
        for biome in active_biomes:
            keywords = MessageParser.BIOME_KEYWORDS.get(biome, [biome.lower()])
            if any(kw in content_lower for kw in keywords):
                return biome
                
        return None

    @staticmethod
    def check_merchants(content: str, active_merchants: list[str]) -> str | None:
        """Checks for active merchants in content, returning None if blacklisted."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in MessageParser.BLACKLIST_KEYWORDS):
            return None
        
        for merchant in active_merchants:
            keywords = MessageParser.MERCHANT_KEYWORDS.get(merchant, [merchant.lower()])
            if any(kw in content_lower for kw in keywords):
                return merchant
                
        return None
