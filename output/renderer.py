import cv2
import numpy as np
import queue
from utils.logger import logger

class OpenCVRenderer:
    """
    Renders the 2D coordinate data onto an OpenCV canvas.
    Runs in the main thread to ensure UI responsiveness.
    """
    def __init__(self, frame_queue: queue.Queue, is_running_callback, app_settings: dict, streamer=None):
        self.frame_queue = frame_queue
        self.is_running_callback = is_running_callback
        self.streamer = streamer
        
        display_settings = app_settings.get("display", {"height": 720, "width": 1280})
        self.height = display_settings.get("height", 720)
        self.width = display_settings.get("width", 1280)
        
        # Scaling and offsets
        self.scale = display_settings.get("scale", 0.35)
        self.offset = display_settings.get("offset", 0.5)
        
        self.display_canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self.BODY_PART_COLORS = self._load_colors(app_settings)

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
        Runs the OpenCV UI loop. This MUST be run on the main thread.
        """
        logger.info("OpenCV Renderer started. Press 'q' on the window to quit.")
        
        while self.is_running_callback():
            try:
                # Wait briefly. If queue empty, spin to keep OpenCV UI responsive.
                frame_payload = self.frame_queue.get(timeout=0.05)
                frame_data = frame_payload.get("data", {})
                ui_label = frame_payload.get("label", "Waiting...")
                wait_ms = frame_payload.get("wait_ms", 33)
                
                # Broadcast the raw frame data if a streamer is attached
                if self.streamer and frame_data:
                    self.streamer.broadcast(frame_data)
                    
                self.display_canvas.fill(0)
                
                if frame_data:
                    self._draw_points(frame_data)
                    
                cv2.putText(self.display_canvas, ui_label, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.imshow("Signify - Continuous Player", self.display_canvas)
                
                if cv2.waitKey(wait_ms) & 0xFF == ord('q'):
                    logger.info("Quit signal received from UI.")
                    break
                    
            except queue.Empty:
                if cv2.waitKey(10) & 0xFF == ord('q'):
                    logger.info("Quit signal received from UI.")
                    break

        cv2.destroyAllWindows()
        logger.info("OpenCV window destroyed.")

    def _draw_points(self, frame_data: dict):
        for key, color in self.BODY_PART_COLORS.items():
            if key in frame_data:
                points_list = frame_data[key]
                for point_coordinates in points_list:
                    x_float = (point_coordinates[0] * self.scale) + self.offset
                    y_float = (point_coordinates[1] * self.scale) + self.offset
                    
                    center_x = int(x_float * self.width)
                    center_y = int(y_float * self.height)
                    
                    cv2.circle(self.display_canvas, (center_x, center_y), 2, color, -1)
