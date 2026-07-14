import threading
import queue
import time
import sys
from utils.logger import logger

class StdinListener:
    """
    Runs unconditionally to listen for IPC commands (like !CLEAR_QUEUE!) from the dashboard.
    If input_mode is 'typing', it also acts as the primary text input mechanism.
    """
    def __init__(self, text_queue: queue.Queue, is_running_callback, clear_queues_callback, input_mode: str):
        self.text_queue = text_queue
        self.is_running_callback = is_running_callback
        self.clear_queues_callback = clear_queues_callback
        self.input_mode = input_mode

    def start(self):
        threading.Thread(target=self._listen_loop, daemon=True).start()

    def _listen_loop(self):
        time.sleep(2) # Give the system time to boot UI
        
        if self.input_mode == "typing":
            logger.info("Live Typing Mode Activated")
            logger.info("Type an English sentence in the terminal and press ENTER.")
        
        while self.is_running_callback():
            try:
                # Use sys.stdin.readline to be safely compatible with subprocess piping
                user_text = sys.stdin.readline()
                if not user_text: # EOF
                    break
                    
                user_text = user_text.strip()
                if not user_text:
                    continue
                
                # Check for IPC commands first
                if user_text == "!CLEAR_QUEUE!":
                    logger.info("IPC Command Received: CLEAR_QUEUE")
                    self.clear_queues_callback()
                    continue
                
                # If not a command and typing mode is active, send to queue
                if self.input_mode == "typing":
                    logger.info(f"Typed: '{user_text}'")
                    self.text_queue.put(user_text)
                    
            except Exception as e:
                logger.error(f"Error in StdinListener: {e}")
                break
