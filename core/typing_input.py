import threading
import queue
import time
from utils.logger import logger

class TypingInput:
    """
    Acts as an alternative input mechanism to the microphone/audio loopback.
    Takes typed English sentences from the terminal and pushes them to the text queue.
    """
    def __init__(self, text_queue: queue.Queue, is_running_callback):
        self.text_queue = text_queue
        self.is_running_callback = is_running_callback

    def start(self):
        threading.Thread(target=self._typing_loop, daemon=True).start()

    def _typing_loop(self):
        time.sleep(2) # Give the system time to boot UI
        logger.info("⌨️ Live Typing Mode Activated ⌨️")
        logger.info("Type an English sentence in the terminal and press ENTER.")
        
        while self.is_running_callback():
            try:
                user_text = input("Type a sentence: ")
                if not user_text.strip():
                    continue
                
                logger.info(f"Typed: '{user_text}'")
                self.text_queue.put(user_text)
            except EOFError:
                break
