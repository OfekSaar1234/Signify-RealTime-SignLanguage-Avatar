import os
import json
import queue
import threading
import time
import requests
from functools import lru_cache
from utils.logger import logger

class Animator:
    """
    Consumes ASL glosses from a queue, loads the corresponding 2D JSON animation files,
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
        
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)
        
        self.last_frame_data = None
        self.idle_sequence = self.load_json_sequence("idle")
        self.idle_frame_idx = 0
        self.is_idle = False
        self.warm_up_cache()

    def start(self):
        threading.Thread(target=self._animation_loop, daemon=True).start()

    def load_json_sequence(self, word: str) -> list:
        return self._cached_load_json_sequence(word.lower())

    @lru_cache(maxsize=128)
    def _cached_load_json_sequence(self, word_lower: str) -> list:
        url = f"https://signify-asl-dictionary-v1.s3.amazonaws.com/dictionary/{word_lower}.json"
        
        sequence = None
        try:
            logger.info(f"[S3 FETCH START] Requesting word '{word_lower}' from URL: {url}")
            t0 = time.time()
            response = self.session.get(url, timeout=2)
            elapsed_ms = (time.time() - t0) * 1000
            
            if response.status_code == 200:
                logger.info(f"[S3 FETCH TIMER] Successfully retrieved word '{word_lower}' from bucket in {elapsed_ms:.2f} ms")
                sequence = response.json()
            elif response.status_code == 404:
                logger.warning(f"[S3 RESP] 404 Not Found for '{word_lower}' ({elapsed_ms:.2f} ms)")
                pass
            else:
                logger.warning(f"[S3 RESP] {response.status_code} Error for '{word_lower}' ({elapsed_ms:.0f}ms)")
        except requests.exceptions.RequestException as e:
            logger.error(f"[S3 ERROR] Network error fetching '{word_lower}': {e}")
                
        # Perform Missing Frame Imputation (Gap Filling)
        if sequence:
            for key in ["f", "fj", "fl", "fre", "fle", "l", "r"]:
                self._fill_missing_landmarks(sequence, key)
                
        return sequence

    def _fill_missing_landmarks(self, sequence: list, key: str):
        """Linearly interpolates any missing frames (tracking drops) in the sequence."""
        n = len(sequence)
        last_valid_idx = -1
        
        # 1. Interpolate intermediate gaps
        for i in range(n):
            if sequence[i].get(key):
                if last_valid_idx != -1 and i - last_valid_idx > 1:
                    start_pts = sequence[last_valid_idx][key]
                    end_pts = sequence[i][key]
                    gap_size = i - last_valid_idx
                    for j in range(last_valid_idx + 1, i):
                        factor = (j - last_valid_idx) / gap_size
                        smoothed = []
                        for pt_s, pt_e in zip(start_pts, end_pts):
                            smoothed.append([pt_s[k] + (pt_e[k] - pt_s[k]) * factor for k in range(3)])
                        sequence[j][key] = smoothed
                last_valid_idx = i

    def warm_up_cache(self):
        """Pre-loads common ASL words into RAM to establish the TLS connection and eliminate cold starts."""
        logger.info("[WARMUP] Warming up network connection and caching common words...")
        common_words = ["hello", "thank", "you", "how", "what", "is"]
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(common_words)) as executor:
            list(executor.map(self.load_json_sequence, common_words))
        logger.info("[WARMUP] Network connection established and cache warmed up.")
        logger.info("==================================================")
        logger.info("✅ AVATAR IS FULLY WARMED UP AND READY! ✅")
        logger.info("==================================================")

    def _calculate_smooth_frame(self, start_frame: dict, end_frame: dict, interpolation_factor: float) -> dict:
        interpolated_result = {}
        # Make sure to interpolate the new Face Contour keys as well!
        for key in ["f", "fj", "fl", "fre", "fle", "p", "l", "r"]:
            points_a = start_frame.get(key, [])
            points_b = end_frame.get(key, [])
            
            # If a feature is missing in either frame, let it vanish instead of freezing in place
            if not points_a or not points_b: 
                interpolated_result[key] = []
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
        
        import concurrent.futures
        
        while self.is_running_callback():
            try:
                # Try to get a gloss sequence
                sentence_glosses = self.gloss_queue.get_nowait()
                self.is_idle = False
                logger.info(f"Animating sequence: {sentence_glosses}")
                
                # Pre-fetch all words concurrently so we don't block on network per-word
                logger.info(f"[PRE-FETCH] Downloading all words for sentence concurrently...")
                with concurrent.futures.ThreadPoolExecutor(max_workers=min(10, len(sentence_glosses))) as executor:
                    list(executor.map(self.load_json_sequence, sentence_glosses))
                    
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
