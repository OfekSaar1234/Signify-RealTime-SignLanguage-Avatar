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
import requests
from bs4 import BeautifulSoup
import boto3
from botocore.exceptions import ClientError
import concurrent.futures

# --- CONFIGURATION ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(PROJECT_ROOT, "assets", "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

S3_BUCKET = "signify-asl-dictionary-v1"

WORDS = [
    "hello", "goodbye", "yes", "no"
]

class CloudPipeline:
    def __init__(self):
        self.mp_holistic = mp.solutions.holistic
        self.ai_model = self.mp_holistic.Holistic(
            min_detection_confidence=0.5, 
            model_complexity=1
        )
        self.s3_client = boto3.client('s3')

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
            return None
            
        url = f"https://www.signasl.org/sign/{word}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.signasl.org/'
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"[-] No page found for: {word}")
                return None
            soup = BeautifulSoup(response.text, 'html.parser')
            video_tag = soup.find('video')
            if not video_tag:
                return None
                
            source_tag = video_tag.find('source')
            video_url = source_tag['src'] if source_tag and source_tag.has_attr('src') else video_tag.get('src')
            if not video_url:
                return None

            if video_url.startswith('/'):
                video_url = f"https://www.signasl.org{video_url}"

            # Pass the headers to the video download request to bypass the 403 Forbidden block!
            vid_response = requests.get(video_url, headers=headers, stream=True, timeout=15)
            vid_response.raise_for_status()
            
            file_path = os.path.join(TEMP_DIR, f"{word}.mp4")
            with open(file_path, "wb") as f:
                for chunk in vid_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return file_path
        except Exception as e:
            print(f"[!] Error downloading '{word}': {e}")
            return None

    def process_and_upload(self, word: str, video_path: str, num_keyframes: int = 30) -> bool:
        """Processes the MP4 to JSON, uploads to S3, and returns True if successful."""
        json_output_path = os.path.join(TEMP_DIR, f"{word}.json")
        video_capture = cv2.VideoCapture(video_path)
        
        if not video_capture.isOpened():
            print(f"[ERROR] Could not open video: {video_path}")
            return False
            
        total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames > num_keyframes:
            target_indices = [int(i * (total_frames - 1) / (num_keyframes - 1)) for i in range(num_keyframes)]
        else:
            target_indices = list(range(total_frames))
            
        full_animation_data = []
        current_frame_idx = 0

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
            print(f"[!] No valid frames processed for {word}")
            return False

        # Save JSON temporarily
        with open(json_output_path, 'w') as json_file:
            json.dump(full_animation_data, json_file, separators=(',', ':'))
            
        # Upload to S3 directly
        s3_key = f"dictionary/{word}.json"
        try:
            self.s3_client.upload_file(
                json_output_path, 
                S3_BUCKET, 
                s3_key,
                ExtraArgs={'ContentType': 'application/json'}
            )
            print(f"[S3 UPLOAD] Successfully uploaded {s3_key}")
        except ClientError as e:
            print(f"[!] Error uploading to S3: {e}")
            return False
            
        # Delete local JSON
        if os.path.exists(json_output_path):
            os.remove(json_output_path)
            
        return True

    def execute_word(self, word: str):
        print(f"\n[PIPELINE] Starting: {word}")
        video_path = self.download_video(word)
        if not video_path or not os.path.exists(video_path):
            print(f"[-] Skipping {word}: Download failed.")
            return

        success = self.process_and_upload(word, video_path)
        
        # Cleanup MP4 from EC2
        if os.path.exists(video_path):
            os.remove(video_path)
            
        if success:
            print(f"[PIPELINE] Finished & Cleaned: {word}")
        else:
            print(f"[PIPELINE] Failed processing: {word}")

# =======================================================================
# EXECUTION
# =======================================================================
if __name__ == "__main__":
    print(f"Starting ephemeral EC2 pipeline for {len(WORDS)} ASL words...")
    pipeline = CloudPipeline()
    
    # We shouldn't use multiple threads for mediapipe processing as it's very CPU intensive,
    # but since downloading is IO bound, we can do sequential to be safe with memory
    for w in WORDS:
        pipeline.execute_word(w)
        
    print("\n[SUCCESS] Pipeline completed.")
