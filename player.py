import cv2
import json
import os
import numpy as np
import queue
from avatar_drawer import AvatarDrawer
from websocket_server import broadcast_frame

class SignLanguagePlayer:
    def __init__(self, app_settings: dict, phrase_queue: queue.Queue):
        """
        Initializes the Sign Language Player. 
        Sets up the drawing canvas, rendering engine, and controls playback speeds.
        """
        self.app_settings = app_settings
        self.phrase_queue = phrase_queue
        self.avatar_renderer = AvatarDrawer()
        
        display_settings = self.app_settings.get("display", {"height": 720, "width": 1280})
        height = display_settings.get("height", 720)
        width = display_settings.get("width", 1280)
        
        self.display_canvas = np.zeros((height, width, 3), dtype=np.uint8)
        self.last_frame_data = None
        self.is_running = True
        self.is_idle = False
        
        playback_settings = self.app_settings.get("playback", {"speed_ms": 33, "transition_frames": 5})
        self.playback_speed_ms = playback_settings.get("speed_ms", 33)
        self.transition_frames = playback_settings.get("transition_frames", 5)
        self.interpolation_frames = playback_settings.get("interpolation_frames", 2)

        self.idle_sequence = self.load_idle_animation()
        self.idle_frame_idx = 0

    def load_idle_animation(self) -> list:
        idle_path = "assets/jsons/idle.json"
        if os.path.exists(idle_path):
            with open(idle_path, 'r') as f:
                return json.load(f)
        return None

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
        file_path = f"assets/jsons/{word.lower()}.json"
        if not os.path.exists(file_path):
            print(f"[PLAYER WARNING] Missing animation file for: {word}. Skipping.")
            return

        with open(file_path, 'r') as f:
            animation_sequence = json.load(f)
        
        if self.last_frame_data is not None:
            first_frame_of_new_word = animation_sequence[0]
            for i in range(1, self.transition_frames + 1):
                blend_factor = i / float(self.transition_frames)
                blend_frame = self.calculate_smooth_frame(self.last_frame_data, first_frame_of_new_word, blend_factor)
                key = self.render_to_screen(blend_frame, f"Transitioning...", wait_ms=1)
                if key == ord('q'):
                    self.is_running = False
                    return

        for i in range(len(animation_sequence)):
            current_frame = animation_sequence[i]
            wait_time = max(1, self.playback_speed_ms // (self.interpolation_frames + 1))
            
            key = self.render_to_screen(current_frame, f"Signing: {word.upper()}", wait_ms=wait_time)
            self.last_frame_data = current_frame 
            if key == ord('q'):
                self.is_running = False
                return
                
            if i < len(animation_sequence) - 1 and self.interpolation_frames > 0:
                next_frame = animation_sequence[i + 1]
                for j in range(1, self.interpolation_frames + 1):
                    blend_factor = j / float(self.interpolation_frames + 1)
                    blend_frame = self.calculate_smooth_frame(current_frame, next_frame, blend_factor)
                    key = self.render_to_screen(blend_frame, f"Signing: {word.upper()}", wait_ms=wait_time)
                    if key == ord('q'):
                        self.is_running = False
                        return

    def continuous_play_loop(self):
        print("[PLAYER] Avatar Engine running. Waiting for incoming speech...")
        while self.is_running:
            if not self.phrase_queue.empty():
                sentence_glosses = self.phrase_queue.get() 
                self.is_idle = False
                print(f"\n[PLAYER] Received new ASL sequence: {sentence_glosses}")
                for word in sentence_glosses:
                    self.play_single_word(word)
                    if not self.is_running: break
            else:
                if self.idle_sequence:
                    if not self.is_idle and self.last_frame_data:
                        # Smooth transition from the last sign down to the Idle state
                        for i in range(1, self.transition_frames + 1):
                            blend_factor = i / float(self.transition_frames)
                            blend_frame = self.calculate_smooth_frame(self.last_frame_data, self.idle_sequence[0], blend_factor)
                            key = self.render_to_screen(blend_frame, "Transitioning to Idle...", wait_ms=1)
                            if key == ord('q'):
                                self.is_running = False
                                break
                        self.is_idle = True
                        
                    if self.is_running:
                        current_frame = self.idle_sequence[self.idle_frame_idx]
                        key = self.render_to_screen(current_frame, "Waiting for speech...", wait_ms=self.playback_speed_ms)
                        self.last_frame_data = current_frame
                        if key == ord('q'): self.is_running = False
                        
                        # Loop the idle animation
                        self.idle_frame_idx = (self.idle_frame_idx + 1) % len(self.idle_sequence)
                else:
                    # Fallback if the user hasn't created an idle.json yet
                    if self.last_frame_data:
                        key = self.render_to_screen(self.last_frame_data, "Waiting... (Missing idle.json)", wait_ms=33)
                        if key == ord('q'): self.is_running = False
                    else:
                        self.display_canvas.fill(0)
                        cv2.putText(self.display_canvas, "Waiting for speech...", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        cv2.imshow("Signify - Continuous Player", self.display_canvas)
                        if cv2.waitKey(33) & 0xFF == ord('q'):
                            self.is_running = False

    def render_to_screen(self, frame_data: dict, ui_label: str, wait_ms: int = 1) -> int:
        broadcast_frame(frame_data) # Send off to unity
        self.display_canvas.fill(0)
        self.avatar_renderer.draw_frame(self.display_canvas, frame_data)
        cv2.putText(self.display_canvas, ui_label, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Signify - Continuous Player", self.display_canvas)
        return cv2.waitKey(wait_ms) & 0xFF