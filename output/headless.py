import queue
import time
from utils.logger import logger

class HeadlessRenderer:
    """
    Consumes frames from the queue and broadcasts them via the websocket streamer.
    Runs without a GUI, designed for the Electron frontend.
    """
    def __init__(self, frame_queue: queue.Queue, is_running_callback, app_settings: dict, streamer=None):
        self.frame_queue = frame_queue
        self.is_running_callback = is_running_callback
        self.streamer = streamer

    def run_blocking(self):
        logger.info("Headless Renderer started for Electron UI. Press Ctrl+C in terminal to quit.")
        
        while self.is_running_callback():
            try:
                frame_payload = self.frame_queue.get(timeout=0.05)
                frame_data = frame_payload.get("data", {})
                wait_ms = frame_payload.get("wait_ms", 33)
                
                # Broadcast the raw frame data
                if self.streamer and frame_data:
                    self.streamer.broadcast(frame_data)
                    
                # Pace the frames
                time.sleep(wait_ms / 1000.0)
                    
            except queue.Empty:
                pass
            except KeyboardInterrupt:
                break
                
        logger.info("Headless Renderer stopped.")
