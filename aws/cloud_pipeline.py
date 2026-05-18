"""
==============================================================================
PROJECT: Signify - Sign Language Translation Avatar
MODULE:  cloud_pipeline.py
PURPOSE: The "Cloud Data Factory" (EC2 Ephemeral Pipeline). 
         Downloads MP4 -> Extracts Landmarks -> Uploads JSON to S3 -> Deletes local files.
==============================================================================
"""

import cv2
import mediapipe as mp
import json
import os
import math
import time as time_module
import requests
from bs4 import BeautifulSoup
import boto3
from botocore.exceptions import ClientError
import concurrent.futures
import logging
import sys
from datetime import datetime

# --- LOGGING SETUP ---
log = logging.getLogger("CloudPipeline")
log.setLevel(logging.DEBUG)
_fmt = logging.Formatter('[%(asctime)s] [%(levelname)-8s] [%(threadName)-12s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
_ch = logging.StreamHandler(sys.stdout)
_ch.setLevel(logging.INFO)
_ch.setFormatter(_fmt)
log.addHandler(_ch)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_logs_dir = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(_logs_dir, exist_ok=True)
_fh = logging.FileHandler(os.path.join(_logs_dir, f"cloud_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"), encoding='utf-8')
_fh.setLevel(logging.DEBUG)
_fh.setFormatter(_fmt)
log.addHandler(_fh)

# --- CONFIGURATION ---
TEMP_DIR = os.path.join(PROJECT_ROOT, "assets", "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

S3_BUCKET = "signify-asl-dictionary-v1"

WORDS = [
    "halt"
]

import threading

class CloudPipeline:
    def __init__(self):
        log.info("Initializing CloudPipeline...")
        self.mp_holistic = mp.solutions.holistic
        self.ai_model = self.mp_holistic.Holistic(
            min_detection_confidence=0.5, 
            model_complexity=1
        )
        log.info("MediaPipe Holistic model loaded (complexity=1, confidence=0.5)")
        self.s3_client = boto3.client('s3')
        log.info(f"S3 client initialized. Target bucket: {S3_BUCKET}")
        self.ai_lock = threading.Lock()
        
        # Progress counters (thread-safe)
        import threading as _th
        self._stats_lock = _th.Lock()
        self.stats = {"success": 0, "skipped_exists": 0, "failed_download": 0, "failed_process": 0}
        self._start_time = time_module.time()

    def _increment_stat(self, key):
        with self._stats_lock:
            self.stats[key] += 1

    def _log_progress(self, word):
        with self._stats_lock:
            total = sum(self.stats.values())
            elapsed = time_module.time() - self._start_time
            rate = total / elapsed * 60 if elapsed > 0 else 0
            log.info(f"[PROGRESS] {total}/{len(WORDS)} words processed | "
                     f"OK={self.stats['success']} Skip={self.stats['skipped_exists']} "
                     f"DlFail={self.stats['failed_download']} ProcFail={self.stats['failed_process']} | "
                     f"{rate:.1f} words/min | Last: {word}")

    def s3_file_exists(self, word: str) -> bool:
        """Checks if the JSON file for the word already exists in S3."""
        s3_key = f"dictionary/{word}.json"
        log.debug(f"[S3 HEAD] Checking if {s3_key} exists in {S3_BUCKET}...")
        try:
            self.s3_client.head_object(Bucket=S3_BUCKET, Key=s3_key)
            log.debug(f"[S3 HEAD] {s3_key} EXISTS")
            return True
        except ClientError as e:
            # If a client error is thrown, then check that it was a 404 error.
            # If it was a 404 error, then the object does not exist.
            if e.response['Error']['Code'] == '404':
                log.debug(f"[S3 HEAD] {s3_key} NOT FOUND (404)")
                return False
            else:
                # Something else has gone wrong.
                log.error(f"[S3 HEAD] Error checking S3 for {word}: {e}")
                return False

    def get_anchor_point(self, pose_landmarks):
        if not pose_landmarks:
            return (0.5, 0.5, 0.0)
        left_shoulder = pose_landmarks.landmark[11]
        right_shoulder = pose_landmarks.landmark[12]
        avg_x = (left_shoulder.x + right_shoulder.x) / 2.0
        avg_y = (left_shoulder.y + right_shoulder.y) / 2.0
        avg_z = (left_shoulder.z + right_shoulder.z) / 2.0
        return (avg_x, avg_y, avg_z)

    def get_scale_factor(self, pose_landmarks):
        if not pose_landmarks:
            return 1.0
        left_shoulder = pose_landmarks.landmark[11]
        right_shoulder = pose_landmarks.landmark[12]
        shoulder_width = math.sqrt(
            (left_shoulder.x - right_shoulder.x)**2 + 
            (left_shoulder.y - right_shoulder.y)**2 + 
            (left_shoulder.z - right_shoulder.z)**2
        )
        if shoulder_width < 0.001: return 1.0
        return 0.5 / shoulder_width

    def convert_landmarks_to_list(self, landmarks_object, anchor=(0.0, 0.0, 0.0), scale=1.0, target_indices=None) -> list:
        if not landmarks_object: return []
        optimized_points = []
        anchor_x, anchor_y, anchor_z = anchor
        if target_indices is not None:
            for idx in target_indices:
                if idx < len(landmarks_object.landmark):
                    landmark = landmarks_object.landmark[idx]
                    x = round((landmark.x - anchor_x) * scale, 3)
                    y = round((landmark.y - anchor_y) * scale, 3)
                    z = round((landmark.z - anchor_z) * scale, 3)
                    optimized_points.append([x, y, z])
            return optimized_points
            
        for landmark in landmarks_object.landmark:
            x = round((landmark.x - anchor_x) * scale, 3)
            y = round((landmark.y - anchor_y) * scale, 3)
            z = round((landmark.z - anchor_z) * scale, 3)
            optimized_points.append([x, y, z])
        return optimized_points

    def download_video(self, word: str) -> str:
        """Downloads the video for a word and returns the local file path, or None if failed."""
        if word == "idle":
            log.debug(f"[DOWNLOAD] Skipping 'idle' — no video needed.")
            return None
            
        url = f"https://www.signasl.org/sign/{word}"
        
        import random, time
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0'
        ]
        
        # Polite Scraping: Random Sleep
        delay = random.uniform(1.5, 4.5)
        log.debug(f"[DOWNLOAD] Polite delay: {delay:.1f}s before fetching '{word}'")
        time.sleep(delay)
        
        max_retries = 3
        for attempt in range(max_retries):
            headers = {
                'User-Agent': random.choice(user_agents),
                'Referer': 'https://www.signasl.org/'
            }
            try:
                # --- HTTP GET: Page scrape ---
                log.debug(f"[HTTP GET] {url} (attempt {attempt+1}/{max_retries})")
                t0 = time_module.time()
                response = requests.get(url, headers=headers, timeout=10)
                elapsed_ms = (time_module.time() - t0) * 1000
                log.debug(f"[HTTP RESP] {url} -> {response.status_code} ({elapsed_ms:.0f}ms, {len(response.content)} bytes)")
                
                if response.status_code == 429:
                    log.warning(f"[HTTP 429] Rate limited on page for '{word}'. Backing off 30s...")
                    time.sleep(30)
                    continue
                if response.status_code != 200:
                    log.warning(f"[HTTP {response.status_code}] No page found for: '{word}'")
                    return None
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                video_tag = soup.find('video')
                if not video_tag:
                    log.warning(f"[SCRAPE] No <video> tag found on page for '{word}'")
                    return None
                    
                source_tag = video_tag.find('source')
                video_url = source_tag['src'] if source_tag and source_tag.has_attr('src') else video_tag.get('src')
                if not video_url:
                    log.warning(f"[SCRAPE] No video src attribute found for '{word}'")
                    return None

                if video_url.startswith('/'):
                    video_url = f"https://www.signasl.org{video_url}"

                # --- HTTP GET: Video download ---
                log.debug(f"[HTTP GET] Downloading video: {video_url}")
                t0 = time_module.time()
                vid_response = requests.get(video_url, headers=headers, stream=True, timeout=15)
                
                if vid_response.status_code == 429:
                    log.warning(f"[HTTP 429] Rate limited on video download for '{word}'. Backing off 30s...")
                    time.sleep(30)
                    continue
                    
                vid_response.raise_for_status()
                
                file_path = os.path.join(TEMP_DIR, f"{word}.mp4")
                total_bytes = 0
                with open(file_path, "wb") as f:
                    for chunk in vid_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        total_bytes += len(chunk)
                elapsed_ms = (time_module.time() - t0) * 1000
                log.info(f"[DOWNLOAD OK] '{word}' -> {total_bytes/1024:.1f}KB in {elapsed_ms:.0f}ms")
                return file_path
            except requests.exceptions.Timeout as e:
                log.warning(f"[HTTP TIMEOUT] '{word}' attempt {attempt+1}/{max_retries}: {e}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(5)
            except requests.exceptions.ConnectionError as e:
                log.warning(f"[HTTP CONN ERROR] '{word}' attempt {attempt+1}/{max_retries}: {e}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(5)
            except Exception as e:
                log.error(f"[DOWNLOAD ERROR] '{word}' attempt {attempt+1}/{max_retries}: {type(e).__name__}: {e}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(5)
                
        return None

    def process_and_upload(self, word: str, video_path: str, num_keyframes: int = 30) -> bool:
        """Processes the MP4 to JSON, uploads to S3, and returns True if successful."""
        json_output_path = os.path.join(TEMP_DIR, f"{word}.json")
        video_capture = cv2.VideoCapture(video_path)
        
        if not video_capture.isOpened():
            log.error(f"[PROCESS ERROR] Could not open video: {video_path}")
            return False
            
        total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames > num_keyframes:
            target_indices = [int(i * (total_frames - 1) / (num_keyframes - 1)) for i in range(num_keyframes)]
        else:
            target_indices = list(range(total_frames))
            
        full_animation_data = []
        current_frame_idx = 0

        # We lock the AI processing so only 1 thread uses the CPU at a time.
        # This prevents EGL Context crashes and Timestamp Mismatches!
        with self.ai_lock:
            while video_capture.isOpened():
                success, frame_image = video_capture.read()
                if not success: break 
                
                if current_frame_idx in target_indices:
                    image_rgb = cv2.cvtColor(frame_image, cv2.COLOR_BGR2RGB)
                    ai_results = self.ai_model.process(image_rgb)
                    
                    anchor = self.get_anchor_point(ai_results.pose_landmarks)
                    scale = self.get_scale_factor(ai_results.pose_landmarks)
                    
                    JAW_INDICES = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
                    LIP_INDICES = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 409, 270, 269, 267, 0, 37, 39, 40, 185]
                    REYE_INDICES = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
                    LEYE_INDICES = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
                    
                    current_frame_data = {
                        "fj": self.convert_landmarks_to_list(ai_results.face_landmarks, anchor, scale, target_indices=JAW_INDICES),
                        "fl": self.convert_landmarks_to_list(ai_results.face_landmarks, anchor, scale, target_indices=LIP_INDICES),
                        "fre": self.convert_landmarks_to_list(ai_results.face_landmarks, anchor, scale, target_indices=REYE_INDICES),
                        "fle": self.convert_landmarks_to_list(ai_results.face_landmarks, anchor, scale, target_indices=LEYE_INDICES),
                        "p": self.convert_landmarks_to_list(ai_results.pose_landmarks, anchor, scale),
                        "l": self.convert_landmarks_to_list(ai_results.left_hand_landmarks, anchor, scale),
                        "r": self.convert_landmarks_to_list(ai_results.right_hand_landmarks, anchor, scale)
                    }
                    full_animation_data.append(current_frame_data)
                    
                    if len(full_animation_data) == len(target_indices):
                        break
                        
                current_frame_idx += 1
        
        video_capture.release()
        
        if len(full_animation_data) == 0:
            log.error(f"[PROCESS ERROR] No valid frames processed for {word}")
            return False

        # Save JSON temporarily
        with open(json_output_path, 'w') as json_file:
            json.dump(full_animation_data, json_file, separators=(',', ':'))
            
        # Upload to S3 directly
        s3_key = f"dictionary/{word}.json"
        try:
            t0 = time_module.time()
            self.s3_client.upload_file(
                json_output_path, 
                S3_BUCKET, 
                s3_key,
                ExtraArgs={'ContentType': 'application/json'}
            )
            elapsed_ms = (time_module.time() - t0) * 1000
            log.info(f"[S3 UPLOAD] Successfully uploaded {s3_key} ({elapsed_ms:.0f}ms)")
        except ClientError as e:
            log.error(f"[S3 UPLOAD ERROR] Failed to upload {word} to S3: {e}")
            return False
            
        # Delete local JSON
        if os.path.exists(json_output_path):
            os.remove(json_output_path)
            
        return True

    def execute_word(self, word: str):
        log.info(f"[PIPELINE START] Processing word: '{word}'")
        
        # 1. Check if the word already exists in S3
        if self.s3_file_exists(word):
            log.info(f"[PIPELINE SKIP] '{word}' already exists in S3.")
            self._increment_stat("skipped_exists")
            self._log_progress(word)
            return
            
        video_path = self.download_video(word)
        if not video_path or not os.path.exists(video_path):
            log.warning(f"[PIPELINE FAIL] Skipping '{word}': Download failed or not found.")
            self._increment_stat("failed_download")
            self._log_progress(word)
            return

        success = self.process_and_upload(word, video_path)
        
        # Cleanup MP4 from EC2
        if os.path.exists(video_path):
            os.remove(video_path)
            log.debug(f"[CLEANUP] Deleted temporary video: {video_path}")
            
        if success:
            log.info(f"[PIPELINE OK] Finished word: '{word}'")
            self._increment_stat("success")
        else:
            log.error(f"[PIPELINE FAIL] Failed processing word: '{word}'")
            self._increment_stat("failed_process")
        
        self._log_progress(word)

# =======================================================================
# EXECUTION
# =======================================================================
if __name__ == "__main__":
    log.info("="*60)
    log.info(f"STARTING MULTI-THREADED CLOUD PIPELINE")
    log.info(f"Targeting {len(WORDS)} ASL words | Threads: 5")
    log.info("="*60)
    
    pipeline = CloudPipeline()
    
    try:
        # 5 concurrent threads to process multiple words at the exact same time
        max_workers = 5
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="Worker") as executor:
            executor.map(pipeline.execute_word, WORDS)
    except KeyboardInterrupt:
        log.warning("Pipeline interrupted by user.")
    except Exception as e:
        log.critical(f"FATAL ERROR in pipeline execution: {e}")
        
    log.info("="*60)
    log.info("PIPELINE SUMMARY")
    log.info(f"Total processed: {sum(pipeline.stats.values())}")
    for k, v in pipeline.stats.items():
        log.info(f" - {k}: {v}")
    
    elapsed = time_module.time() - pipeline._start_time
    log.info(f"Total time: {elapsed/60:.2f} minutes")
    log.info("="*60)
    log.info("Cloud Pipeline completed.")
