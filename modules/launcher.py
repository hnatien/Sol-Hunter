import subprocess
import logging
import platform

def killRoblox() -> None:
    try:
        import psutil
        targetProcs = ["RobloxPlayerBeta.exe", "Bloxstrap.exe"]
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] in targetProcs:
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception as e:
        system = platform.system()
        if system == "Windows":
            subprocess.run(["taskkill", "/F", "/IM", "RobloxPlayerBeta.exe", "/T"], capture_output=True, shell=True)
            subprocess.run(["taskkill", "/F", "/IM", "Bloxstrap.exe", "/T"], capture_output=True, shell=True)
        elif system == "Darwin":
            subprocess.run(["killall", "-9", "RobloxPlayer"], capture_output=True)

def launchRoblox(placeId: int | str, jobId: str | None = None, linkCode: str | None = None, autoKill: bool = False, linkType: str = "private_server", launchData: str | None = None) -> None:
    if autoKill:
        killRoblox()
        
    if not placeId:
        logging.error("Launch aborted: No Place ID provided.")
        return

    # Construct the base command using the most reliable protocol (placeId= format)
    if linkType == "share_code" and linkCode:
        finalCmd = f"roblox://navigation/share_links?code={linkCode}&type=Server"
    elif linkType == "job_id" and jobId:
        finalCmd = f"roblox://experiences/start?placeId={placeId}&gameInstanceId={jobId}"
    elif linkCode:
        # V3 style: roblox://placeId=...&linkCode=...
        finalCmd = f"roblox://placeId={placeId}&linkCode={linkCode}"
    elif launchData:
        finalCmd = f"roblox://experiences/start?placeId={placeId}&launchData={launchData}"
    elif jobId:
        finalCmd = f"roblox://experiences/start?placeId={placeId}&gameInstanceId={jobId}"
    else:
        finalCmd = f"roblox://placeId={placeId}"

    try:
        system = platform.system()
        if system == "Windows":
            import os
            os.startfile(finalCmd)
        elif system == "Darwin":
            subprocess.Popen(["open", finalCmd])
        elif system == "Linux":
            subprocess.Popen(["xdg-open", finalCmd])
        else:
            logging.error(f"Unsupported OS: {system}")
            
        logging.info(f"Launched Roblox: {finalCmd}")
            
    except Exception as e:
        logging.error(f"Failed to launch Roblox: {e}")
