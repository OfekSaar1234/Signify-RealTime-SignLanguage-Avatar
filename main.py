"""
==============================================================================
PROJECT: Signify - Sign Language Translation Avatar
MODULE:  main.py
PURPOSE: The Continuous Application Controller.
         Uses Multithreading and a Queue to run the Avatar smoothly while 
         simultaneously receiving and translating text from the user live.
==============================================================================
"""

"""simulated_speech = [
        "The sea is beautiful today",
        "I am going to the sea tomorrow",
        "Yesterday I saw a beautiful bird",
        "Are you going to work now",
        "The morning is cold",
        "I will sleep at night",
        "See you later",
        "The bird will fly to the tree",
        "I am happy today",
        "He is going home soon"
    ]"""

import cv2
import json
import os
import threading
import queue

# Import our newly modularized components
from player import SignLanguagePlayer
from inputs import live_typing_stream, live_audio_stream
from websocket_server import start_websocket_server

# --- GLOBAL CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "app_settings.json")

try:
    with open(CONFIG_PATH, "r") as f:
        APP_SETTINGS = json.load(f)
except FileNotFoundError:
    print(f"[ERROR] Configuration file missing at {CONFIG_PATH}. Using empty defaults.")
    APP_SETTINGS = {}

# =======================================================================
# APPLICATION ENTRY POINT
# =======================================================================
if __name__ == "__main__":
    print("[SYSTEM] Booting up Signify Architecture...")
    print("[SYSTEM] Press 'q' on the video window to quit.")
    
    # 1. Setup shared communication queue
    phrase_queue = queue.Queue()
    
    # 2. Conditionally start the WebSocket server
    network_cfg = APP_SETTINGS.get("network", {})
    if network_cfg.get("enable_websocket", False):
        host = network_cfg.get("ws_host", "localhost")
        port = network_cfg.get("ws_port", 8765)
        ws_thread = threading.Thread(target=start_websocket_server, args=(host, port), daemon=True)
        ws_thread.start()
        
    # 3. Initialize the visual Player
    player = SignLanguagePlayer(APP_SETTINGS, phrase_queue)
    
    # 4. Start the Input Stream (Keyboard or Microphone)
    input_mode = APP_SETTINGS.get("input_mode", "typing")
    is_running_callback = lambda: player.is_running
    
    if input_mode == "audio_loopback":
        api_thread = threading.Thread(target=live_audio_stream, args=(phrase_queue, is_running_callback), daemon=True)
    else:
        api_thread = threading.Thread(target=live_typing_stream, args=(phrase_queue, is_running_callback), daemon=True)
        
    api_thread.start()
    
    # 5. Start the main renderer loop (blocks the thread until user hits 'q')
    player.continuous_play_loop()
    
    # 6. Clean exit
    cv2.destroyAllWindows()
    print("[SYSTEM] Application closed cleanly.")