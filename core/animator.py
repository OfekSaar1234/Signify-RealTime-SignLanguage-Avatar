import os
import json
import queue
import threading
import time
from functools import lru_cache
from utils.logger import logger

class Animator:
    """
    Consumes ASL glosses from a queue, loads the corresponding 3D JSON animation files,
    interpolates between frames for smooth transitions, and outputs discrete frame data
    into a frame queue to be consumed by renderers or streamers.
    """
    def __init__(self, gloss_queue: queue.Queue, frame_queue: queue.Queue, is_running_callback, app_settings: dict):
        self.gloss_queue = gloss_queue
        self.frame_queue = frame_queue
        self.is_running_callback = is_running_callback
        
        playback_settings = app_settings.get("playback", {"speed_ms": 33, "transition_frames": 5, "interpolation_frames": 2})
        self.playback_speed_ms = playback_settings.get("speed_ms", 33)
        self.transition_frames = playback_settings.get("transition_frames", 5)
        self.interpolation_frames = playback_settings.get("interpolation_frames", 2)
        
        self.last_frame_data = None
        self.idle_sequence = self.load_json_sequence("idle")
        self.idle_frame_idx = 0
        self.is_idle = False
        self.warm_up_cache()

    def start(self):
        threading.Thread(target=self._animation_loop, daemon=True).start()

    @lru_cache(maxsize=128)
    def load_json_sequence(self, word: str) -> list:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        word_lower = word.lower()
        prefix = word_lower[:2] if len(word_lower) >= 2 else word_lower
        first_letter = word_lower[0] if len(word_lower) > 0 else ""
        file_path = os.path.join(base_dir, "assets", "jsons", first_letter, prefix, f"{word_lower}.json")
        
        # Fallback to old path just in case
        old_file_path = os.path.join(base_dir, "assets", "jsons", f"{word_lower}.json")
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        elif os.path.exists(old_file_path):
            with open(old_file_path, 'r') as f:
                return json.load(f)
        return None

    def warm_up_cache(self):
        """Pre-loads common ASL words into RAM."""
        common_words = [
            "hello", "goodbye", "yes", "no", "please", "thank", "you", "sorry", "excuse", "me",
            "help", "who", "what", "where", "when", "why", "how", "stop", "go", "come",
            "more", "finish", "eat", "drink", "sleep", "want", "need", "like", "love", "hate",
            "happy", "sad", "angry", "tired", "good", "bad", "beautiful", "ugly", "big", "small",
            "hot", "cold", "day", "night", "morning", "afternoon", "evening", "today", "tomorrow", "yesterday",
            "now", "later", "time", "home", "work", "school", "friend", "family", "mother", "father",
            "brother", "sister", "son", "daughter", "man", "woman", "boy", "girl", "name", "age",
            "color", "red", "blue", "green", "yellow", "black", "white", "number", "one", "two",
            "three", "four", "five", "six", "seven", "eight", "nine", "ten", "money", "buy",
            "sell", "pay", "cost", "cheap", "expensive", "food", "water", "apple", "book", "car"
        ]
        for word in common_words:
            self.load_json_sequence(word)
        logger.info("Animator cache warmed up with top 100 ASL words.")

    def _calculate_smooth_frame(self, start_frame: dict, end_frame: dict, interpolation_factor: float) -> dict:
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

    def _push_frame(self, frame_data: dict, label: str, wait_ms: int):
        # We push a dict containing the raw data, UI label, and intended wait time
        # This decouples the animator's logic from the actual OpenCV window rendering
        frame_payload = {
            "data": frame_data,
            "label": label,
            "wait_ms": wait_ms
        }
        # Push to queue; will block if queue is full (backpressure)
        self.frame_queue.put(frame_payload)
        self.last_frame_data = frame_data

    def _play_single_word(self, word: str):
        animation_sequence = self.load_json_sequence(word)
        if not animation_sequence:
            logger.warning(f"Missing animation file for: {word}. Skipping.")
            return

        if self.last_frame_data is not None:
            first_frame_of_new_word = animation_sequence[0]
            for i in range(1, self.transition_frames + 1):
                blend_factor = i / float(self.transition_frames)
                blend_frame = self._calculate_smooth_frame(self.last_frame_data, first_frame_of_new_word, blend_factor)
                self._push_frame(blend_frame, "Transitioning...", 1)
                if not self.is_running_callback(): return

        for i in range(len(animation_sequence)):
            current_frame = animation_sequence[i]
            wait_time = max(1, self.playback_speed_ms // (self.interpolation_frames + 1))
            
            self._push_frame(current_frame, f"Signing: {word.upper()}", wait_time)
            if not self.is_running_callback(): return
                
            if i < len(animation_sequence) - 1 and self.interpolation_frames > 0:
                next_frame = animation_sequence[i + 1]
                for j in range(1, self.interpolation_frames + 1):
                    blend_factor = j / float(self.interpolation_frames + 1)
                    blend_frame = self._calculate_smooth_frame(current_frame, next_frame, blend_factor)
                    self._push_frame(blend_frame, f"Signing: {word.upper()}", wait_time)
                    if not self.is_running_callback(): return

    def _animation_loop(self):
        logger.info("Avatar Animation Engine running. Waiting for incoming speech...")
        while self.is_running_callback():
            try:
                # Try to get a gloss sequence
                sentence_glosses = self.gloss_queue.get_nowait()
                self.is_idle = False
                logger.info(f"Animating sequence: {sentence_glosses}")
                for word in sentence_glosses:
                    self._play_single_word(word)
                    if not self.is_running_callback(): break
            except queue.Empty:
                # Handle Idle state
                if self.idle_sequence:
                    if not self.is_idle and self.last_frame_data:
                        # Smooth transition from the last sign down to the Idle state
                        for i in range(1, self.transition_frames + 1):
                            blend_factor = i / float(self.transition_frames)
                            blend_frame = self._calculate_smooth_frame(self.last_frame_data, self.idle_sequence[0], blend_factor)
                            self._push_frame(blend_frame, "Transitioning to Idle...", 1)
                            if not self.is_running_callback(): break
                        self.is_idle = True
                        
                    if self.is_running_callback():
                        current_frame = self.idle_sequence[self.idle_frame_idx]
                        self._push_frame(current_frame, "Waiting for speech...", self.playback_speed_ms)
                        
                        # Loop the idle animation
                        self.idle_frame_idx = (self.idle_frame_idx + 1) % len(self.idle_sequence)
                else:
                    # Fallback if the user hasn't created an idle.json yet
                    if self.last_frame_data:
                        self._push_frame(self.last_frame_data, "Waiting... (Missing idle.json)", 33)
                    else:
                        # Send an empty frame to keep renderer alive
                        self._push_frame({}, "Waiting for speech...", 33)
                        
                # Small sleep to prevent CPU spinning when idle queue is filling up renderer
                time.sleep(0.01)
