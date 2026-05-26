import os
import json
import queue
import threading
import time
import requests
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
        
        import boto3
        self.dynamodb = boto3.client('dynamodb', region_name='us-east-1')
        
        self.memory_cache = {}
        
        self.last_frame_data = None
        self.idle_sequence = self.load_json_sequence("idle")
        self.idle_frame_idx = 0
        self.is_idle = False
        self.warm_up_cache()

    def start(self):
        threading.Thread(target=self._animation_loop, daemon=True).start()
        threading.Thread(target=self._prefetch_loop, daemon=True).start()

    def load_json_sequence(self, word: str) -> list:
        word_lower = word.lower()
        if word_lower in self.memory_cache:
            return self.memory_cache[word_lower]
            
        sequence = None
        try:
            logger.info(f"[DYNAMO FETCH START] Requesting word '{word_lower}' from DynamoDB")
            t0 = time.time()
            response = self.dynamodb.get_item(
                TableName='SignifyDictionary',
                Key={'word': {'S': word_lower}}
            )
            elapsed_ms = (time.time() - t0) * 1000
            
            if 'Item' in response:
                logger.info(f"[DYNAMO FETCH TIMER] Successfully retrieved word '{word_lower}' in {elapsed_ms:.2f} ms")
                json_string = response['Item']['animation_data']['S']
                sequence = json.loads(json_string)
            else:
                logger.warning(f"[DYNAMO RESP] 404 Not Found for '{word_lower}' ({elapsed_ms:.2f} ms)")
        except Exception as e:
            logger.error(f"[DYNAMO ERROR] Network error fetching '{word_lower}': {e}")
                
        # Perform Missing Frame Imputation (Gap Filling)
        if sequence:
            for key in ["f", "fj", "fl", "fre", "fle", "l", "r"]:
                self._fill_missing_landmarks(sequence, key)
                
        self.memory_cache[word_lower] = sequence
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

    def _execute_batch_fetch(self, words_to_fetch: list):
        if not words_to_fetch:
            return
            
        logger.info(f"[PRE-FETCH] Batch downloading {len(words_to_fetch)} words for sentence...")
        
        # De-duplicate keys
        unique_keys = []
        seen = set()
        for w in words_to_fetch:
            if w not in seen:
                seen.add(w)
                unique_keys.append({'word': {'S': w}})
        
        # DynamoDB BatchGetItem strict limit: 100 items or 16MB per request
        chunk_size = 100
        fetched_words = set()
        
        t0 = time.time()
        for i in range(0, len(unique_keys), chunk_size):
            chunk = unique_keys[i:i + chunk_size]
            try:
                response = self.dynamodb.batch_get_item(
                    RequestItems={
                        'SignifyDictionary': {
                            'Keys': chunk
                        }
                    }
                )
                items = response.get('Responses', {}).get('SignifyDictionary', [])
                
                for item in items:
                    word_val = item['word']['S']
                    json_string = item['animation_data']['S']
                    sequence = json.loads(json_string)
                    for key in ["f", "fj", "fl", "fre", "fle", "l", "r"]:
                        self._fill_missing_landmarks(sequence, key)
                    self.memory_cache[word_val] = sequence
                    fetched_words.add(word_val)
            except Exception as e:
                logger.error(f"[DYNAMO BATCH ERROR]: {e}")
                
        elapsed_ms = (time.time() - t0) * 1000
        logger.info(f"[DYNAMO BATCH TIMER] Retrieved {len(fetched_words)} words simultaneously in {elapsed_ms:.2f} ms")
            
        # Mark 404s as None so we don't keep fetching them
        for k in unique_keys:
            word_val = k['word']['S']
            if word_val not in fetched_words:
                self.memory_cache[word_val] = None
                logger.warning(f"[DYNAMO RESP] 404 Not Found for '{word_val}' (Batch)")

    def _prefetch_loop(self):
        while self.is_running_callback():
            try:
                # Safely peek into the gloss_queue without removing items
                with self.gloss_queue.mutex:
                    queued_sentences = list(self.gloss_queue.queue)
                    
                if queued_sentences:
                    words_to_fetch = set()
                    for sentence in queued_sentences:
                        for word in sentence:
                            w_lower = word.lower()
                            if w_lower not in self.memory_cache:
                                words_to_fetch.add(w_lower)
                                
                    if words_to_fetch:
                        logger.info(f"[BACKGROUND PRE-FETCH] Discovered {len(words_to_fetch)} un-cached words waiting in queue!")
                        self._execute_batch_fetch(list(words_to_fetch))
                        
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"[PREFETCH LOOP ERROR]: {e}")
                time.sleep(1)

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
                words_to_fetch = [w.lower() for w in sentence_glosses if w.lower() not in self.memory_cache]
                
                if words_to_fetch:
                    self._execute_batch_fetch(words_to_fetch)
                    
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
