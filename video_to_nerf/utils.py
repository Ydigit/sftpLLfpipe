# video_to_nerf/utils.py
import os
import logging
from datetime import datetime

def setup_logger():
    import sys

    logs_dir = os.path.join(os.path.expanduser("~"), ".video_to_nerf", "logs")
    os.makedirs(logs_dir, exist_ok=True)

    log_filename = os.path.join(logs_dir, "video_to_nerf.log")

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def is_ffmpeg_installed():
    """
    Check if FFmpeg is installed
    
    Returns:
        bool: True if FFmpeg is installed, False otherwise
    """
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
        return result.returncode == 0
    except:
        return False