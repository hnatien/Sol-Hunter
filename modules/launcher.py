import subprocess
import logging
import platform

def kill_roblox() -> None:
    """Forcefully terminates the Roblox process."""
    try:
        import psutil
        target_procs = ["RobloxPlayerBeta.exe", "Bloxstrap.exe", "EuroTrucks2.exe"]
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] in target_procs:
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception as e:
        import subprocess
        import platform
        system = platform.system()
        if system == "Windows":
            subprocess.run(["taskkill", "/F", "/IM", "RobloxPlayerBeta.exe", "/T"], capture_output=True, shell=True)
            subprocess.run(["taskkill", "/F", "/IM", "Bloxstrap.exe", "/T"], capture_output=True, shell=True)
        elif system == "Darwin":
            subprocess.run(["killall", "-9", "RobloxPlayer"], capture_output=True)

def launch_roblox(place_id: int | str, job_id: str | None = None, link_code: str | None = None, auto_kill: bool = False) -> None:
    """Launches Roblox via the roblox-player: protocol."""
    if auto_kill:
        kill_roblox()
        
    if not place_id:
        logging.error("Launch aborted: No Place ID provided.")
        return

    params = f"?placeId={place_id}"
    if link_code:
        params += f"&linkCode={link_code}"
    elif job_id:
        params += f"&gameInstanceId={job_id}"
    
    final_cmd = f"roblox://experiences/start{params}"

    try:
        system = platform.system()
        if system == "Windows":
            import os
            os.startfile(final_cmd)
        elif system == "Darwin":
            subprocess.Popen(["open", final_cmd])
        elif system == "Linux":
            subprocess.Popen(["xdg-open", final_cmd])
        else:
            logging.error(f"Unsupported OS: {system}")
            
        logging.info(f"Launched Roblox: {final_cmd}")
            
    except Exception as e:
        logging.error(f"Failed to launch Roblox: {e}")
