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

# --- ROBUST PATH SETUP ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

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

    def convert_landmarks_to_list(self, landmarks_object) -> list:
        """
        Converts a MediaPipe landmarks object into a standard Python list of coordinates.
        
        :param landmarks_object: The raw landmark data returned by MediaPipe.
        :return: A list of [x, y, z] coordinates rounded to 5 decimal places.
        """
        if not landmarks_object: 
            return []
        
        optimized_points = []
        
        for landmark in landmarks_object.landmark:
            x = round(landmark.x, 5)
            y = round(landmark.y, 5)
            z = round(landmark.z, 5)
            
            optimized_points.append([x, y, z])
            
        return optimized_points

    def process_video_to_json(self, word_name: str) -> None:
        """
        Reads an MP4 video file frame by frame, extracts the landmarks using AI,
        and saves the complete animation data into a JSON file.
        
        :param word_name: The name of the word (without extension) to process.
        """
        # Using the smart paths we defined above
        video_path = os.path.join(MP4_DIR, f"{word_name}.mp4")
        json_output_path = os.path.join(JSON_DIR, f"{word_name}.json")
        
        video_capture = cv2.VideoCapture(video_path)
        full_animation_data = []

        while video_capture.isOpened():
            success, frame_image = video_capture.read()
            if not success: 
                break 
            
            image_rgb = cv2.cvtColor(frame_image, cv2.COLOR_BGR2RGB)
            ai_results = self.ai_model.process(image_rgb)
            
            current_frame_data = {
                "f": self.convert_landmarks_to_list(ai_results.face_landmarks),
                "p": self.convert_landmarks_to_list(ai_results.pose_landmarks),
                "l": self.convert_landmarks_to_list(ai_results.left_hand_landmarks),
                "r": self.convert_landmarks_to_list(ai_results.right_hand_landmarks)
            }
            
            full_animation_data.append(current_frame_data)
        
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
    
    words_to_process = [
        "thank"
    ]
    
    missing_mp4s = []
    
    print(f"[SYSTEM] Starting HIGH-DETAIL generation for {len(words_to_process)} words...\n")
    
    for word in words_to_process:
        video_path = os.path.join(MP4_DIR, f"{word}.mp4")
        json_path = os.path.join(JSON_DIR, f"{word}.json")
        
        # Smart Skip: If the JSON file is already ready, do not generate it again
        if os.path.exists(json_path):
            print(f"[SKIP] '{word}.json' already exists. Saving time!")
            continue
            
        if os.path.exists(video_path):
            print(f"[PROCESSING] Generating high-detail data for: '{word}'...")
            tool.process_video_to_json(word)
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