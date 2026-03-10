"""
==============================================================================
PROJECT: Signify - Sign Language Translation Avatar
MODULE:  main.py
PURPOSE: The Continuous Application Controller.
         Uses Multithreading and a Queue to run the Avatar smoothly while 
         simultaneously receiving and translating text from the user live.
         *SPEED UPGRADED FOR REAL-TIME ASL FLUENCY*
=============================================================================
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

# Import our custom modules
from avatar_drawer import AvatarDrawer
from asl_translator import ASLTranslator

# --- THE SHARED QUEUE ---
phrase_queue = queue.Queue()

class SignLanguagePlayer:
    def __init__(self):
        self.avatar_renderer = AvatarDrawer()
        self.display_canvas = np.zeros((720, 1280, 3), dtype=np.uint8)
        self.last_frame_data = None
        self.is_running = True
        
        # --- SPEED CONTROLS ---
        # 33 = ~30 FPS (Normal/Slow)
        # 16 = ~60 FPS (Fast/Smooth)
        # 10 = ~100 FPS (Lightning fast)
        self.playback_speed_ms = 15 
        
        # How many frames to use for the "bridge" between words. 
        # Lower = snappier/faster. Higher = smoother but slower.
        self.transition_frames = 4 

    def calculate_smooth_frame(self, start_frame: dict, end_frame: dict, interpolation_factor: float) -> dict:
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
        file_path = f"assets/{word.lower()}.json"
        
        if not os.path.exists(file_path):
            print(f"[PLAYER WARNING] Missing animation file for: {word}. Skipping.")
            return

        with open(file_path, 'r') as f:
            animation_sequence = json.load(f)
        
        # --- PHASE 1: TRANSITION (Faster & Snappier) ---
        if self.last_frame_data is not None:
            first_frame_of_new_word = animation_sequence[0]
            for i in range(1, self.transition_frames + 1):
                # Calculate the percentage of the transition (e.g., 1/4, 2/4, 3/4)
                blend_factor = i / float(self.transition_frames)
                blend_frame = self.calculate_smooth_frame(self.last_frame_data, first_frame_of_new_word, blend_factor)
                self.render_to_screen(blend_frame, f"Transitioning...")

        # --- PHASE 2: PLAYBACK (High Speed) ---
        for frame_data in animation_sequence:
            self.render_to_screen(frame_data, f"Signing: {word.upper()}")
            self.last_frame_data = frame_data 
            
            if cv2.waitKey(self.playback_speed_ms) & 0xFF == ord('q'): 
                self.is_running = False
                return

    def continuous_play_loop(self):
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
                    self.render_to_screen(self.last_frame_data, "Waiting for speech...")
                else:
                    self.display_canvas.fill(0)
                    cv2.putText(self.display_canvas, "Waiting for speech...", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.imshow("Signify - Continuous Player", self.display_canvas)
                    
                    if cv2.waitKey(33) & 0xFF == ord('q'):
                        self.is_running = False

    def render_to_screen(self, frame_data: dict, ui_label: str) -> None:
        self.display_canvas.fill(0)
        self.avatar_renderer.draw_frame(self.display_canvas, frame_data)
        cv2.putText(self.display_canvas, ui_label, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Signify - Continuous Player", self.display_canvas)
        
        # We wait 1ms here so OpenCV draws, but the REAL delay is controlled in play_single_word
        cv2.waitKey(1)

# =======================================================================
# BACKGROUND THREAD: THE LIVE INPUT SIMULATOR
# =======================================================================
def live_typing_stream():
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
# APPLICATION ENTRY POINT
# =======================================================================
if __name__ == "__main__":
    player = SignLanguagePlayer()
    
    print("[SYSTEM] Booting up Signify Architecture...")
    print("[SYSTEM] Press 'q' on the video window to quit.")
    
    api_thread = threading.Thread(target=live_typing_stream, daemon=True)
    api_thread.start()
    
    player.continuous_play_loop()
    
    cv2.destroyAllWindows()
    print("[SYSTEM] Application closed cleanly.")