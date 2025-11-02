#!/usr/bin/env python3
"""
sound_wallpaper_random.py

🎧 Real-time sound level detector that randomly changes wallpaper
based on noise level (Quiet / Moderate / Loud / Very Loud).

Author: ChatGPT (as a senior Python + ML developer)
"""

import os
import sys
import math
import time
import queue
import random
import platform
import numpy as np
import sounddevice as sd
from colorama import Fore, Style, init as colorama_init
from ctypes import windll  # for Windows wallpaper change

colorama_init(autoreset=True)

# === Folder Paths ===
BASE_PATH = "wallpapers"
CATEGORIES = {
    "Quiet": os.path.join(BASE_PATH, "quiet"),
    "Moderate": os.path.join(BASE_PATH, "moderate"),
    "Loud": os.path.join(BASE_PATH, "loud"),
    "Very Loud": os.path.join(BASE_PATH, "very_loud"),
}

# === Sound Classification Thresholds (adjust if needed) ===
THRESHOLDS = {
    'quiet': -40.0,
    'moderate': -20.0,
    'loud': -8.0
}

# === Helper Functions ===
def rms_to_dbfs(rms, ref=1.0):
    if rms <= 0:
        return -math.inf
    return 20 * math.log10(rms / ref)


def classify_db(db_value):
    if db_value <= THRESHOLDS['quiet']:
        return "Quiet", Fore.GREEN
    elif db_value <= THRESHOLDS['moderate']:
        return "Moderate", Fore.YELLOW
    elif db_value <= THRESHOLDS['loud']:
        return "Loud", Fore.MAGENTA
    else:
        return "Very Loud", Fore.RED


def get_random_wallpaper(folder):
    """Pick a random image file from a folder."""
    if not os.path.exists(folder):
        print(Fore.RED + f"⚠️ Folder not found: {folder}")
        return None
    files = [f for f in os.listdir(folder)
             if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
    if not files:
        print(Fore.RED + f"⚠️ No images found in {folder}")
        return None
    choice = random.choice(files)
    return os.path.join(folder, choice)


def set_wallpaper(image_path):
    """Change wallpaper according to OS."""
    abs_path = os.path.abspath(image_path)
    system = platform.system()

    if not os.path.exists(abs_path):
        print(Fore.RED + f"⚠️ Wallpaper not found: {abs_path}")
        return

    try:
        if system == "Windows":
            windll.user32.SystemParametersInfoW(20, 0, abs_path, 3)
        elif system == "Darwin":  # macOS
            os.system(f"osascript -e 'tell application \"Finder\" to set desktop picture to POSIX file \"{abs_path}\"'")
        elif system == "Linux":
            os.system(f"gsettings set org.gnome.desktop.background picture-uri file://{abs_path}")
        else:
            print(Fore.RED + "❌ Unsupported OS for wallpaper change.")
    except Exception as e:
        print(Fore.RED + f"Error changing wallpaper: {e}")


def main():
    samplerate = 22050
    blockdur = 0.3
    blocksize = int(round(blockdur * samplerate))
    q = queue.Queue()

    def callback(indata, frames, time_info, status):
        if status:
            pass
        q.put(np.mean(indata, axis=1))

    print("🎤 Starting sound monitor (random wallpaper mode)...")
    print("Press Ctrl+C to stop.\n")

    current_label = None

    try:
        with sd.InputStream(channels=1, samplerate=samplerate,
                            blocksize=blocksize, callback=callback):
            while True:
                block = q.get()
                rms = np.sqrt(np.mean(block ** 2))
                db_value = rms_to_dbfs(rms)
                label, color = classify_db(db_value)

                if label != current_label:
                    current_label = label
                    print(color + f"🔊 {label} | {db_value:.2f} dBFS")
                    wallpaper_folder = CATEGORIES[label]
                    random_wall = get_random_wallpaper(wallpaper_folder)
                    if random_wall:
                        set_wallpaper(random_wall)

                time.sleep(blockdur)

    except KeyboardInterrupt:
        print(Fore.CYAN + "\n🛑 Stopped by user.")
    except Exception as e:
        print(Fore.RED + f"Error: {e}")


if __name__ == "__main__":
    main()
