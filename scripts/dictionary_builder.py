"""
==============================================================================
PROJECT: Signify - Sign Language Translation Avatar
MODULE:  dictionary_builder.py
PURPOSE: The "Data Factory" (HIGH DETAIL MODE). 
         Extracts every single detected landmark (Face, Pose, Hands).
         Includes SMART SKIP to prevent overwriting existing JSONs.
==============================================================================
"""

import cv2
import mediapipe as mp
import json
import os
import math

# --- ROBUST PATH SETUP ---
# Go up one level from 'scripts' to reach the main 'Signify' directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MP4_DIR = os.path.join(PROJECT_ROOT, "assets", "mp4")
JSON_DIR = os.path.join(PROJECT_ROOT, "assets", "jsons")

class DictionaryBuilder:
    def __init__(self):
        """
        Initializes the DictionaryBuilder.
        Sets up the MediaPipe Holistic model to detect face, pose, and hand landmarks.
        """
        self.mp_holistic = mp.solutions.holistic
        self.ai_model = self.mp_holistic.Holistic(
            min_detection_confidence=0.5, 
            model_complexity=1
        )

    def get_anchor_point(self, pose_landmarks):
        """
        Calculates the center of the chest (mathematical midpoint between the left 
        and right shoulders). MediaPipe Pose: Left Shoulder=11, Right Shoulder=12.
        """
        if not pose_landmarks:
            # Default to the center of the screen if no pose is detected
            return (0.5, 0.5, 0.0)
            
        left_shoulder = pose_landmarks.landmark[11]
        right_shoulder = pose_landmarks.landmark[12]
        
        avg_x = (left_shoulder.x + right_shoulder.x) / 2.0
        avg_y = (left_shoulder.y + right_shoulder.y) / 2.0
        avg_z = (left_shoulder.z + right_shoulder.z) / 2.0
        
        return (avg_x, avg_y, avg_z)

    def get_scale_factor(self, pose_landmarks):
        """
        Calculates the scale multiplier to prevent the "zooming in and out" effect.
        Measures the distance between the shoulders and forces it to a standard size.
        """
        if not pose_landmarks:
            return 1.0
            
        left_shoulder = pose_landmarks.landmark[11]
        right_shoulder = pose_landmarks.landmark[12]
        
        # Calculate the 3D distance between the two shoulders
        shoulder_width = math.sqrt(
            (left_shoulder.x - right_shoulder.x)**2 + 
            (left_shoulder.y - right_shoulder.y)**2 + 
            (left_shoulder.z - right_shoulder.z)**2
        )
        
        if shoulder_width < 0.001: return 1.0
        
        # Normalize the skeleton so the shoulder width is always exactly 0.5 units
        return 0.5 / shoulder_width

    def convert_landmarks_to_list(self, landmarks_object, anchor=(0.0, 0.0, 0.0), scale=1.0, target_indices=None) -> list:
        """
        Converts a MediaPipe landmarks object into a standard Python list of coordinates.
        Subtracts the anchor coordinates to make all points relative to the chest.
        
        :param landmarks_object: The raw landmark data returned by MediaPipe.
        :param anchor: The (x, y, z) tuple representing the center of the chest.
        :param scale: The multiplier to normalize the size of the skeleton.
        :param target_indices: An optional list of specific indices to extract in order.
        :return: A list of [x, y, z] coordinates rounded to 3 decimal places.
        """
        if not landmarks_object: 
            return []
        
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
            # Subtract anchor for relative position, then multiply by scale
            # GODOT COORDINATE MAPPING:
            # X is unchanged. Y is inverted (MediaPipe + is Down, Godot + is Up).
            x = round((landmark.x - anchor_x) * scale, 3)
            y = round((landmark.y - anchor_y) * scale, 3)
            z = round((landmark.z - anchor_z) * scale, 3)
            
            optimized_points.append([x, y, z])
            
        return optimized_points

    def process_video_to_json(self, word_name: str, num_keyframes: int = 30) -> None:
        """
        Reads an MP4 video file and extracts specific "Key Poses" (e.g., 30 frames)
        to optimize the animation data for Unity IK Interpolation, capturing complex movement.
        
        :param word_name: The name of the word (without extension) to process.
        :param num_keyframes: The number of crucial poses to extract from the video.
        """
        # Using the smart paths we defined above
        video_path = os.path.join(MP4_DIR, f"{word_name}.mp4")
        
        # Shard JSON folders
        prefix = word_name[:2] if len(word_name) >= 2 else word_name
        first_letter = word_name[0] if len(word_name) > 0 else ""
        shard_dir = os.path.join(JSON_DIR, first_letter, prefix)
        os.makedirs(shard_dir, exist_ok=True)
        json_output_path = os.path.join(shard_dir, f"{word_name}.json")
        
        video_capture = cv2.VideoCapture(video_path)
        
        if not video_capture.isOpened():
            print(f"[ERROR] Could not open video: {video_path}")
            return
            
        total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Calculate the exact frame indices to extract as "Key Poses"
        if total_frames > num_keyframes:
            target_indices = [int(i * (total_frames - 1) / (num_keyframes - 1)) for i in range(num_keyframes)]
        else:
            target_indices = list(range(total_frames))
            
        full_animation_data = []
        current_frame_idx = 0

        while video_capture.isOpened():
            success, frame_image = video_capture.read()
            if not success: 
                break 
            
            # Only run the AI model if this frame is one of our target key poses
            if current_frame_idx in target_indices:
                image_rgb = cv2.cvtColor(frame_image, cv2.COLOR_BGR2RGB)
                ai_results = self.ai_model.process(image_rgb)
                
                anchor = self.get_anchor_point(ai_results.pose_landmarks)
                scale = self.get_scale_factor(ai_results.pose_landmarks)
                
                # Face Contours
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
                
                # If we collected all the required key poses, we can stop reading
                if len(full_animation_data) == len(target_indices):
                    break
                    
            current_frame_idx += 1
        
        video_capture.release()
        
        with open(json_output_path, 'w') as json_file:
            json.dump(full_animation_data, json_file, separators=(',', ':'))

# =======================================================================
# EXECUTION BLOCK: AUTOMATIC BATCH PROCESSING (SMART SKIP MODE)
# =======================================================================
if __name__ == "__main__":
    tool = DictionaryBuilder()
    
    # Using the smart paths to create the directories if they are missing
    os.makedirs(MP4_DIR, exist_ok=True)
    os.makedirs(JSON_DIR, exist_ok=True)
    
    # Auto-detect all MP4 files in the directory so you don't have to type them manually!
    words_to_process = [f.replace('.mp4', '') for f in os.listdir(MP4_DIR) if f.endswith('.mp4')]
    
    missing_mp4s = []
    
    print(f"[SYSTEM] Starting HIGH-DETAIL generation for {len(words_to_process)} words...\n")
    
    for word in words_to_process:
        video_path = os.path.join(MP4_DIR, f"{word}.mp4")
        
        # Shard JSON folders
        prefix = word[:2] if len(word) >= 2 else word
        first_letter = word[0] if len(word) > 0 else ""
        shard_dir = os.path.join(JSON_DIR, first_letter, prefix)
        json_path = os.path.join(shard_dir, f"{word}.json")
        
        # Force Rebuild: We want to overwrite with our newly compressed JSONs
        FORCE_REBUILD = True
        if not FORCE_REBUILD and os.path.exists(json_path):
            print(f"[SKIP] '{word}.json' already exists. Saving time!")
            continue
            
        if os.path.exists(video_path):
            print(f"[PROCESSING] Extracting {30} key poses for: '{word}'...")
            # Passing 30 extracts enough keyframes to capture complex motion smoothly.
            tool.process_video_to_json(word, num_keyframes=30)
        else:
            print(f"[WARNING] Skipping '{word}': Could not find {video_path}")
            missing_mp4s.append(word)
            
    if missing_mp4s:
        print("\n=========================================")
        print("🚨 SUMMARY: MISSING MP4 FILES 🚨")
        print("=========================================")
        for missing in missing_mp4s:
            print(f" - {missing}.mp4")
        print("=========================================")
    else:
        print("\n[SUCCESS] All high-detail JSONs generated successfully! Ready for the Player.")