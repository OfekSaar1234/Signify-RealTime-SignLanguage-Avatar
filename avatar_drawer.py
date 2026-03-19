"""
==============================================================================
PROJECT: Signify - Sign Language Translation Avatar
MODULE:  avatar_drawer.py
PURPOSE: The "Renderer" (The Painter).
         This module is responsible for taking the raw mathematical data (JSON)
         and drawing it visually on the screen.
         Current Mode: "Points Only" (Simple Mode).
         It draws dots for every detected joint but does not draw connecting lines.
         This is the most efficient and error-proof way to visualize raw data.
==============================================================================
"""
import cv2
import json
import os
import numpy as np

class AvatarDrawer:
    def __init__(self):
        """
        Initializes the drawer and defines the color scheme for the avatar's body parts.
        """
        # Determine the absolute path to the config file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config", "app_settings.json")
        
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                settings = json.load(f)
                # Convert the JSON lists [B, G, R] back into tuples (B, G, R) for OpenCV
                self.BODY_PART_COLORS = {k: tuple(v) for k, v in settings.get("colors", {}).items()}
        else:
            print("[WARNING] app_settings.json not found. Using default colors.")
            self.BODY_PART_COLORS = {
                "f": (0, 255, 255),  "p": (255, 0, 255),
                "l": (0, 255, 0),    "r": (0, 255, 0)
            }

    def draw_frame(self, canvas: np.ndarray, frame_data: dict) -> None:
        """
        Reads a single frame of data and draws its points onto the provided canvas.

        :param canvas: A numpy array representing the black background image. 
                       Shape is usually (720, 1280, 3).
        :param frame_data: A dictionary containing the coordinates for this specific frame.
                           Example: {'p': [[0.5, 0.2, 0.0], ...], 'l': ...}
        """
        # Get the dimensions of the screen (Height, Width, Color Channels)
        canvas_height, canvas_width, _ = canvas.shape

        # Loop through the body parts defined in our colors dictionary
        # key: e.g., "p" for Pose
        # color: e.g., (255, 0, 255) for Magenta
        for key, color in self.BODY_PART_COLORS.items():
            
            # Check if this specific body part exists in the current frame's data
            # (Sometimes a hand might go off-screen and not be detected)
            if key in frame_data:
                
                # Retrieve the list of [x, y, z] points for this body part
                points_list = frame_data[key]
                
                # Loop through every single point (joint) in that list
                for point_coordinates in points_list:
                    # The coordinates in the JSON are "Normalized" (0.0 to 1.0).
                    # We must multiply them by the screen size to get actual pixels.
                    # x * width = Horizontal Pixel
                    # y * height = Vertical Pixel
                    x_float = point_coordinates[0]
                    y_float = point_coordinates[1]
                    
                    center_x = int(x_float * canvas_width)
                    center_y = int(y_float * canvas_height)
                    
                    # Draw a filled circle at this location
                    # radius=2, thickness=-1 (filled)
                    cv2.circle(canvas, (center_x, center_y), 2, color, -1)