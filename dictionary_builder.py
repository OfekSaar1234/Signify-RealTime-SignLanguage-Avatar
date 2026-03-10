"""
==============================================================================
PROJECT: Signify - Sign Language Translation Avatar
MODULE:  dictionary_builder.py
PURPOSE: The "Data Factory". 
         This script is responsible for the Extract-Transform-Load (ETL) process.
         1. Reads raw MP4 video files.
         2. Uses AI (MediaPipe) to detect the human skeleton.
         3. Optimizes the data (rounding numbers, removing unnecessary face points).
         4. Saves the result as a lightweight JSON file for the Unity Engine.
==============================================================================
"""

import cv2
import mediapipe as mp
import json
import os

class DictionaryBuilder:
    def __init__(self):
        """
        Initializes the AI model and defines optimization settings.
        """
        # Initialize MediaPipe Holistic (The AI that detects Face, Body, and Hands)
        self.mp_holistic = mp.solutions.holistic
        self.ai_model = self.mp_holistic.Holistic(
            min_detection_confidence=0.5, 
            model_complexity=1
        )
        
        # === OPTIMIZATION SETTING ===
        # MediaPipe detects 468 face points. We only need the eyes, eyebrows, and mouth
        # for a realistic avatar. Saving all 468 points would make the JSON files huge.
        # This list contains only the specific indices we want to keep.
        self.FACE_INDICES_TO_KEEP = [
            0, 13, 14, 17, 37, 39, 40, 61, 78, 81, 82, 95, 146, 178, 185, 191, 267, 269, 270, 291,
            308, 311, 312, 324, 375, 402, 409, 415, # Mouth
            70, 63, 105, 66, 107, 336, 296, 334, 293, 300, # Eyebrows
            33, 133, 362, 263 # Eyes
        ]

    def convert_landmarks_to_list(self, landmarks_object, apply_face_filter: bool = False) -> list:
        """
        Converts the complex MediaPipe result object into a simple Python list.

        :param landmarks_object: The raw detection result from MediaPipe (contains .x, .y, .z).
        :param apply_face_filter: Boolean (True/False). If True, we discard most face points to save space.
        :return: A list of lists containing coordinates, e.g., [[0.5, 0.2, -0.1], ...]
        """
        if not landmarks_object: 
            return []
        
        optimized_points = []
        
        # Loop through every detected point (landmark)
        for index, landmark in enumerate(landmarks_object.landmark):
            
            # If this is a face, and the current index is NOT in our "Keep List", skip it.
            if apply_face_filter and index not in self.FACE_INDICES_TO_KEEP: 
                continue
            
            # Rounding to 4 decimal places (e.g., 0.123456 -> 0.1235)
            # This reduces the file size by ~40% without losing visible quality.
            x = round(landmark.x, 4)
            y = round(landmark.y, 4)
            z = round(landmark.z, 4)
            
            optimized_points.append([x, y, z])
            
        return optimized_points

    def process_video_to_json(self, word_name: str) -> None:
        """
        The main function. Opens the video, runs the AI, and saves the JSON.

        :param word_name: The name of the word to process (e.g., "hello"). 
                          The script expects "assets/hello.mp4" to exist.
        """
        video_path = f"assets/{word_name}.mp4"
        json_output_path = f"assets/{word_name}.json"
        
        # Open the video file
        video_capture = cv2.VideoCapture(video_path)
        
        # This list will store the data for every single frame of the video
        full_animation_data = []

        print(f"[STATUS] Processing video: {word_name}...")

        while video_capture.isOpened():
            success, frame_image = video_capture.read()
            if not success: 
                break # Stop if the video ends
            
            # MediaPipe requires RGB color format (OpenCV uses BGR by default)
            image_rgb = cv2.cvtColor(frame_image, cv2.COLOR_BGR2RGB)
            
            # Run the AI detection
            ai_results = self.ai_model.process(image_rgb)
            
            # Extract and organize the data for this specific frame
            current_frame_data = {
                "f": self.convert_landmarks_to_list(ai_results.face_landmarks, apply_face_filter=True),
                "p": self.convert_landmarks_to_list(ai_results.pose_landmarks),
                "l": self.convert_landmarks_to_list(ai_results.left_hand_landmarks),
                "r": self.convert_landmarks_to_list(ai_results.right_hand_landmarks)
            }
            
            full_animation_data.append(current_frame_data)
        
        video_capture.release()
        
        # Save the list to a JSON file
        with open(json_output_path, 'w') as json_file:
            json.dump(full_animation_data, json_file, separators=(',', ':'))
            
        print(f"[SUCCESS] Data saved to: {json_output_path}")

# =======================================================================
# EXECUTION BLOCK: AUTOMATIC BATCH PROCESSING
# =======================================================================
if __name__ == "__main__":
    tool = DictionaryBuilder()
    
    # The exact 25 words needed for our 10 Test Phrases
    words_to_process = [
        "today", "sea", "beautiful", "tomorrow", "i", "going", 
        "yesterday", "saw", "bird", "now", "you", "work", 
        "morning", "cold", "night", "will", "sleep", "later", 
        "see", "fly", "tree", "happy", "soon", "he", "home"
    ]
    
    # We will keep track of missing files here
    missing_mp4s = []
    
    print(f"[SYSTEM] Starting batch processing of {len(words_to_process)} words...")
    
    for word in words_to_process:
        video_path = f"assets/{word}.mp4"
        json_path = f"assets/{word}.json"
        
        # 1. SMART CHECK: Does the JSON already exist?
        if os.path.exists(json_path):
            print(f"[SKIP] '{word}.json' already exists. Saving time!")
            continue 
            
        # 2. SAFETY CHECK: Make sure you actually moved the MP4 to the assets folder
        if os.path.exists(video_path):
            tool.process_video_to_json(word)
        else:
            print(f"[WARNING] Skipping '{word}': Could not find {video_path}")
            missing_mp4s.append(word)  # Add the missing word to our report list
            
    print("\n[SYSTEM] Batch processing complete! Your Dictionary is ready.")
    
    # 3. PRINT THE SUMMARY REPORT
    if missing_mp4s:
        print("\n=========================================")
        print("🚨 SUMMARY: MISSING MP4 FILES 🚨")
        print("=========================================")
        print(f"You are missing {len(missing_mp4s)} video(s). Please download them into the 'assets' folder:")
        for missing in missing_mp4s:
            print(f" - {missing}.mp4")
        print("=========================================")
    else:
        print("\n[SUCCESS] All 25 words have been successfully processed or skipped! You are ready to run main.py!")