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
import numpy as np
import threading
import queue
import time
import asyncio
import websockets

# Import our custom modules
from avatar_drawer import AvatarDrawer
from asl_translator import ASLTranslator

# --- THE SHARED QUEUE ---
phrase_queue = queue.Queue()

# --- WEBSOCKET SERVER CONFIG ---
connected_ws_clients = set()
ws_loop = None

async def ws_connection_handler(websocket, *args, **kwargs):
    """Handles new WebSocket connections from Unity/JS Frontend."""
    connected_ws_clients.add(websocket)
    print(f"\n[NETWORK] 3D Avatar connected! Total clients: {len(connected_ws_clients)}")
    try:
        # Keep the connection open to continuously send data
        async for message in websocket:
            pass 
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_ws_clients.remove(websocket)
        print(f"\n[NETWORK] 3D Avatar disconnected. Total clients: {len(connected_ws_clients)}")

class SignLanguagePlayer:
    def __init__(self):
        """
        Initializes the Sign Language Player. 
        Sets up the drawing canvas, rendering engine, and controls playback speeds.
        """
        # --- LOAD CONFIGURATION ---
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config", "app_settings.json")
        
        with open(config_path, "r") as f:
            settings = json.load(f)
            
        self.avatar_renderer = AvatarDrawer()
        
        height = settings["display"]["height"]
        width = settings["display"]["width"]
        self.display_canvas = np.zeros((height, width, 3), dtype=np.uint8)
        self.last_frame_data = None
        self.is_running = True
        
        # --- SPEED CONTROLS ---
        self.playback_speed_ms = settings["playback"]["speed_ms"]
        self.transition_frames = settings["playback"]["transition_frames"]

    def calculate_smooth_frame(self, start_frame: dict, end_frame: dict, interpolation_factor: float) -> dict:
        """
        Calculates an intermediate frame between two given frames to create a smooth visual transition.
        
        :param start_frame: The data of the ending frame of the previous word.
        :param end_frame: The data of the starting frame of the new word.
        :param interpolation_factor: A float between 0.0 and 1.0 indicating the transition progress.
        :return: A dictionary representing the interpolated frame data.
        """
        interpolated_result = {}
        for key in ["f", "p", "l", "r"]:
            points_a = start_frame.get(key, [])
            points_b = end_frame.get(key, [])
            
            if not points_a or not points_b: 
                interpolated_result[key] = points_b if points_b else points_a
                continue
            
            smoothed_points = []
            for point_a, point_b in zip(points_a, points_b):
                new_coords = [point_a[i] + (point_b[i] - point_a[i]) * interpolation_factor for i in range(3)]
                smoothed_points.append(new_coords)
                
            interpolated_result[key] = smoothed_points
        return interpolated_result

    def play_single_word(self, word: str) -> None:
        """
        Loads the JSON animation file for a single word and plays it on the canvas, 
        including generating the smooth transition frames if necessary.
        
        :param word: The ASL gloss word to be animated.
        """
        # UPDATED PATH: Looking inside the new jsons folder
        file_path = f"assets/jsons/{word.lower()}.json"
        
        if not os.path.exists(file_path):
            print(f"[PLAYER WARNING] Missing animation file for: {word}. Skipping.")
            return

        with open(file_path, 'r') as f:
            animation_sequence = json.load(f)
        
        # --- PHASE 1: TRANSITION ---
        if self.last_frame_data is not None:
            first_frame_of_new_word = animation_sequence[0]
            for i in range(1, self.transition_frames + 1):
                blend_factor = i / float(self.transition_frames)
                blend_frame = self.calculate_smooth_frame(self.last_frame_data, first_frame_of_new_word, blend_factor)
                key = self.render_to_screen(blend_frame, f"Transitioning...", wait_ms=1)
                if key == ord('q'):
                    self.is_running = False
                    return

        # --- PHASE 2: PLAYBACK ---
        for frame_data in animation_sequence:
            key = self.render_to_screen(frame_data, f"Signing: {word.upper()}", wait_ms=self.playback_speed_ms)
            self.last_frame_data = frame_data 
            
            if key == ord('q'): 
                self.is_running = False
                return

    def continuous_play_loop(self):
        """
        The main rendering loop that runs continuously. It checks the queue for new
        ASL sequences and plays them. If the queue is empty, it maintains the idle state.
        """
        print("[PLAYER] Avatar Engine running. Waiting for incoming speech...")
        
        while self.is_running:
            if not phrase_queue.empty():
                sentence_glosses = phrase_queue.get() 
                
                print(f"\n[PLAYER] Received new ASL sequence: {sentence_glosses}")
                for word in sentence_glosses:
                    self.play_single_word(word)
                    if not self.is_running: break
            else:
                if self.last_frame_data:
                    key = self.render_to_screen(self.last_frame_data, "Waiting for speech...", wait_ms=33)
                    if key == ord('q'):
                        self.is_running = False
                else:
                    self.display_canvas.fill(0)
                    cv2.putText(self.display_canvas, "Waiting for speech...", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.imshow("Signify - Continuous Player", self.display_canvas)
                    
                    if cv2.waitKey(33) & 0xFF == ord('q'):
                        self.is_running = False

    def render_to_screen(self, frame_data: dict, ui_label: str, wait_ms: int = 1) -> int:
        """
        Clears the canvas, commands the renderer to draw the frame data, adds UI text,
        and updates the OpenCV display window.
        
        :param frame_data: The specific points data for the current frame.
        :param ui_label: The text to display on the top-left corner of the screen.
        :param wait_ms: The amount of milliseconds OpenCV should wait on this frame.
        :return: The ASCII code of the key pressed during the wait (if any).
        """
        # --- BROADCAST KEY POSES TO UNITY ---
        # Send the extracted Key Poses over the WebSocket so Unity can Lerp them!
        if connected_ws_clients and ws_loop:
            json_string = json.dumps(frame_data, separators=(',', ':'))
            for client in list(connected_ws_clients):
                asyncio.run_coroutine_threadsafe(client.send(json_string), ws_loop)

        # --- DRAW TO LOCAL 2D CANVAS ---
        self.display_canvas.fill(0)
        self.avatar_renderer.draw_frame(self.display_canvas, frame_data)
        cv2.putText(self.display_canvas, ui_label, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Signify - Continuous Player", self.display_canvas)
        return cv2.waitKey(wait_ms) & 0xFF

# =======================================================================
# BACKGROUND THREAD: THE LIVE INPUT SIMULATOR
# =======================================================================
def live_typing_stream():
    """
    Runs in a separate thread. Acts as a simulator for the microphone API.
    Translates typed English into ASL glosses and pushes them to the shared queue.
    """
    translator = ASLTranslator()
    time.sleep(2) 
    
    print("\n" + "="*50)
    print("🎙️ LIVE INPUT MODE ACTIVATED 🎙️")
    print("Type an English sentence in the terminal and press ENTER.")
    print("To quit, click the video window and press 'q'.")
    print("="*50 + "\n")
    
    while player.is_running:
        try:
            user_text = input("Type a sentence: ")
            
            if not user_text.strip():
                continue
                
            print(f"\n[MIC] You typed: '{user_text}'")
            
            asl_glosses = translator.text_to_gloss(user_text)
            print(f"[BRAIN] Translated to ASL: {asl_glosses}")
            
            phrase_queue.put(asl_glosses)
            
        except EOFError:
            break

# =======================================================================
# BACKGROUND THREAD: WEBSOCKET SERVER
# =======================================================================
def start_websocket_server():
    global ws_loop
    ws_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(ws_loop)
    start_server = websockets.serve(ws_connection_handler, "localhost", 8765)
    ws_loop.run_until_complete(start_server)
    print("[NETWORK] WebSocket Server started on ws://localhost:8765")
    ws_loop.run_forever()

# =======================================================================
# APPLICATION ENTRY POINT
# =======================================================================
if __name__ == "__main__":
    player = SignLanguagePlayer()
    
    print("[SYSTEM] Booting up Signify Architecture...")
    print("[SYSTEM] Press 'q' on the video window to quit.")
    
    # Start the WebSocket server to stream to Unity
    ws_thread = threading.Thread(target=start_websocket_server, daemon=True)
    ws_thread.start()
    
    api_thread = threading.Thread(target=live_typing_stream, daemon=True)
    api_thread.start()
    
    player.continuous_play_loop()
    
    cv2.destroyAllWindows()
    print("[SYSTEM] Application closed cleanly.")