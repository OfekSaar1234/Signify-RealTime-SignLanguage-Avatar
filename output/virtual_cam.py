import numpy as np
import cv2
import queue
import threading
import time
from utils.logger import logger

try:
    import pyvirtualcam
    VIRTUAL_CAM_AVAILABLE = True
except ImportError:
    VIRTUAL_CAM_AVAILABLE = False
    logger.warning("pyvirtualcam is not installed. Virtual Camera mode will not work.")

class VirtualCamStreamer:
    """
    Renders 3D coordinate data into a 2D numpy array and streams it directly 
    to a registered virtual camera (e.g., OBS Virtual Camera).
    """
    def __init__(self, frame_queue: queue.Queue, is_running_callback, app_settings: dict, streamer=None):
        self.frame_queue = frame_queue
        self.is_running_callback = is_running_callback
        self.streamer = streamer
        
        display_settings = app_settings.get("display", {"height": 720, "width": 1280})
        self.height = display_settings.get("height", 720)
        self.width = display_settings.get("width", 1280)
        self.fps = 30
        
        self.scale = 0.35
        self.offset = 0.5
        
        self.BODY_PART_COLORS = self._load_colors(app_settings)
        # pyvirtualcam expects RGB, but if the original settings were BGR (OpenCV standard),
        # we convert them here.
        self.RGB_COLORS = {k: (v[2], v[1], v[0]) for k, v in self.BODY_PART_COLORS.items()}
        
        # We need to maintain the last frame data if the animator hasn't yielded a new one
        self.last_drawn_canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)

    def _load_colors(self, settings):
        colors = {k: tuple(v) for k, v in settings.get("colors", {}).items()}
        if not colors:
            colors = {
                "f": (0, 255, 255),  "p": (255, 0, 255),
                "l": (0, 255, 0),    "r": (0, 255, 0)
            }
        return colors

    def run_blocking(self):
        """
        Runs the Virtual Camera loop. We run this blockingly similar to OpenCV renderer,
        so it keeps the main thread alive.
        """
        if not VIRTUAL_CAM_AVAILABLE:
            logger.error("Cannot start Virtual Camera because pyvirtualcam is missing.")
            return

        logger.info("Initializing Virtual Camera... (Ensure OBS Virtual Cam is installed and running if using OBS backend)")
        try:
            with pyvirtualcam.Camera(width=self.width, height=self.height, fps=self.fps) as cam:
                logger.info(f"Virtual Camera Active: {cam.device} ({cam.width}x{cam.height} @ {cam.fps}fps)")
                
                canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
                
                while self.is_running_callback():
                    # We try to get a new frame. If none, we redraw the last one to maintain 30FPS for Zoom
                    try:
                        frame_payload = self.frame_queue.get(timeout=1.0 / self.fps)
                        frame_data = frame_payload.get("data", {})
                        
                        # Broadcast the raw frame data if a websocket streamer is attached
                        if self.streamer and frame_data:
                            self.streamer.broadcast(frame_data)
                            
                        canvas.fill(0)
                        if frame_data:
                            self._draw_points(canvas, frame_data)
                            self.last_drawn_canvas = canvas.copy()
                        else:
                            canvas = self.last_drawn_canvas.copy()
                    except queue.Empty:
                        # Queue empty, use the last frame
                        canvas = self.last_drawn_canvas.copy()
                        
                    # Send to the virtual camera driver
                    cam.send(canvas)
                    cam.sleep_until_next_frame()
                    
        except Exception as e:
            logger.error(f"Failed to start Virtual Camera: {e}")
            logger.error("Did you install OBS Virtual Cam plugin?")
            
        logger.info("Virtual Camera stream ended.")

    def _draw_points(self, canvas: np.ndarray, frame_data: dict):
        for key, color in self.RGB_COLORS.items():
            if key in frame_data:
                points_list = frame_data[key]
                for point_coordinates in points_list:
                    x_float = (point_coordinates[0] * self.scale) + self.offset
                    y_float = (point_coordinates[1] * self.scale) + self.offset
                    
                    center_x = int(x_float * self.width)
                    center_y = int(y_float * self.height)
                    
                    cv2.circle(canvas, (center_x, center_y), 2, color, -1)
