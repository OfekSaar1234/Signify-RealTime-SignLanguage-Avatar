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
import numpy as np

class AvatarDrawer:
    def __init__(self):
        """
        Initializes the drawer and defines the color scheme for the avatar.
        """
        # A dictionary mapping the short keys to specific colors.
        # Format: (Blue, Green, Red) - OpenCV uses BGR, not RGB.
        self.BODY_PART_COLORS = {
            "f": (0, 255, 255),  # Face -> Yellow
            "p": (255, 0, 255),  # Pose (Body) -> Magenta
            "l": (0, 255, 0),    # Left Hand -> Green
            "r": (0, 255, 0)     # Right Hand -> Green
        }

    def draw_frame(self, canvas: np.ndarray, frame_data: dict) -> None:
        """
        Reads a single frame of data and draws it onto the provided canvas.

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