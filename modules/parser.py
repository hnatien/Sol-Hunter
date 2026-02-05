import re
import logging

class MessageParser:
    """
    Parses Discord message content to detect Biomes and extract Roblox connection details.
    """
    
    PS_LINK_PATTERN = re.compile(r"roblox\.com/games/(\d+)(?:/[\w-]+)?\?.*privateServerLinkCode=(\w+)")
    
    @staticmethod
    def extract_link_data(content: str) -> dict | None:
        """
        Scans a string for a Roblox Private Server link.
        
        Returns:
            dict containing 'place_id' and 'link_code' if found, else None.
        """
        match = MessageParser.PS_LINK_PATTERN.search(content)
        if match:
            return {
                "place_id": match.group(1),
                "link_code": match.group(2)
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
