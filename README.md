# SOLS HUNTER v1.0

SOLS HUNTER is a high-speed automation tool designed for Sol's RNG. It monitors Discord channels for specific biome announcements and automatically launches the Roblox client using deep linking protocols to minimize latency.

## Key Features

* Discord Message Listener: Real-time monitoring of specific channel IDs using Discord user tokens.
* Biome Filtering: User-defined selection of target biomes (Glitched, Corruption, Hell, etc.).
* Instant Launch: Utilizes the roblox:// protocol to bypass web browsers and join servers directly.
* Process Management: Optional auto-kill feature to terminate existing Roblox instances before joining a new server.
* Modern Interface: Built with CustomTkinter for a clean, dark-themed user experience.

## Installation

1. Ensure Python 3.10 or higher is installed on your system.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Discord Token: Provide your Discord user token (instructions available in the Guide tab within the app).
2. Channel IDs: Enter the specific Discord channel IDs you wish to monitor (comma-separated).
3. Targeted Biomes: Toggle the desired biomes in the dashboard.
4. Auto-Kill: Enable this to automatically close running Roblox clients when a target biome is found.

## Usage

1. Run the application:
   ```bash
   python main.py
   ```
2. Configure your credentials and settings in the Dashboard.
3. Click "SAVE SETTINGS" to persist your configuration.
4. Click "START SNIPER" to begin monitoring.

## Safety Warning

Do not share your Discord User Token with anyone. This token provides full access to your Discord account.
