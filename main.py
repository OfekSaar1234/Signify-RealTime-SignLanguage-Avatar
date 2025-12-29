"""
==============================================================================
PROJECT: Signify - Sign Language Translation Avatar
MODULE:  main.py
PURPOSE: The Application Controller (The Player).
         This script manages the runtime execution:
         1. Loads the lightweight JSON data.
         2. Smooths transitions between frames using Linear Interpolation (Lerp).
         3. Sends data to the AvatarDrawer for rendering.
         4. Handles user input (Quit).
==============================================================================
"""
import cv2
import json
import os
import numpy as np
from avatar_drawer import AvatarDrawer

class SignLanguagePlayer:
    def __init__(self):
        """
        Initializes the player, the renderer, and the memory buffer for the screen.
        """
        # Instance of our drawing engine (from avatar_drawer.py)
        self.avatar_renderer = AvatarDrawer()
        
        # Pre-allocate a black blank image (HD Resolution: 1280x720)
        # We use uint8 because images are 8-bit (0-255) integers.
        self.display_canvas = np.zeros((720, 1280, 3), dtype=np.uint8)

    def calculate_smooth_frame(self, start_frame: dict, end_frame: dict, interpolation_factor: float) -> dict:
        """
        Mathematically calculates an "in-between" frame to smooth movement.
        Formula: Result = Start + (End - Start) * Factor

        :param start_frame: The data of the starting pose (dict).
        :param end_frame: The data of the target pose (dict).
        :param interpolation_factor: A float between 0.0 and 1.0 (0% to 100% progress).
        :return: A new dictionary containing the calculated coordinates.
        """
        interpolated_result = {}
        
        # Loop through all body parts: f (Face), p (Pose), l (Left), r (Right)
        for key in ["f", "p", "l", "r"]:
            # Get points from both frames (handle cases where a hand might be missing in one)
            points_a = start_frame.get(key, [])
            points_b = end_frame.get(key, [])
            
            # If one frame is missing data, we cannot smooth it, so we just snap to the target.
            if not points_a or not points_b: 
                interpolated_result[key] = points_b if points_b else points_a
                continue
            
            # The Math: Iterate through every point (x, y, z) and calculate the weighted average.
            # zip(points_a, points_b) pairs the points together (Point 1 with Point 1, etc.)
            smoothed_points = []
            for point_a, point_b in zip(points_a, points_b):
                # Apply Lerp formula to X, Y, and Z
                new_coords = [
                    point_a[i] + (point_b[i] - point_a[i]) * interpolation_factor 
                    for i in range(3)
                ]
                smoothed_points.append(new_coords)
                
            interpolated_result[key] = smoothed_points
            
        return interpolated_result

    def play_sentence(self, words_list: list) -> None:
        """
        Iterates through a list of words, loads their files, and plays them in sequence.

        :param words_list: A list of strings representing filenames (e.g., ["hello", "thank_you"]).
        """
        last_frame_data = None
        
        for word in words_list:
            file_path = f"assets/{word}.json"
            
            # Error Handling: Skip words that haven't been processed by the builder yet
            if not os.path.exists(file_path):
                print(f"[ERROR] File not found: {file_path}. Skipping.")
                continue

            # Load the JSON data
            with open(file_path, 'r') as f:
                animation_sequence = json.load(f)
            
            # --- PHASE 1: TRANSITION (The Bridge) ---
            # If we just finished a word, we need to smooth the jump to the new word.
            # We generate 10 artificial frames to blend the end of Word A to the start of Word B.
            if last_frame_data is not None:
                first_frame_of_new_word = animation_sequence[0]
                for i in range(1, 11):
                    # i / 10 gives us steps: 0.1, 0.2, ... 1.0
                    blend_frame = self.calculate_smooth_frame(
                        last_frame_data, first_frame_of_new_word, i / 10
                    )
                    self.render_to_screen(blend_frame, f"Transitioning...")

            # --- PHASE 2: PLAYBACK ---
            # Play the actual frames of the current word
            for frame_data in animation_sequence:
                self.render_to_screen(frame_data, f"Signing: {word.upper()}")
                last_frame_data = frame_data # Save this frame to start the next transition
                
                # Check for 'q' key to quit immediately
                if cv2.waitKey(33) & 0xFF == ord('q'): 
                    return

    def render_to_screen(self, frame_data: dict, ui_label: str) -> None:
        """
        Updates the canvas with the new frame and displays it.

        :param frame_data: The dictionary of coordinates to draw.
        :param ui_label: Text string to display on top of the screen (GUI).
        """
        # 1. Clear the screen (fill with black) to remove the previous frame
        self.display_canvas.fill(0)
        
        # 2. Ask the Renderer (AvatarDrawer) to draw the dots
        self.avatar_renderer.draw_frame(self.display_canvas, frame_data)
        
        # 3. Add the text label (Green text)
        cv2.putText(
            self.display_canvas, ui_label, (50, 50), 
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
        )
        
        # 4. Refresh the window
        cv2.imshow("Signify - Final Player", self.display_canvas)
        
        # Tiny pause (1ms) to allow the OS to draw the window
        cv2.waitKey(1)

if __name__ == "__main__":
    player = SignLanguagePlayer()
    
    print("[SYSTEM] Starting Signify Player...")
    print("[SYSTEM] Press 'q' at any time to quit.")
    
    # === PLAYLIST CONFIGURATION ===
    # Ensure these words exist in your assets folder as .json files!
    # If "word.json" is missing, remove it from this list.
    playlist = ["hello","sea"] 
    
    player.play_sentence(playlist)
    
    cv2.destroyAllWindows()