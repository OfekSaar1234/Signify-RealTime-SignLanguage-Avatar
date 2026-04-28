import re
import json
import os
import queue
import threading
from utils.logger import logger

class ASLTranslator:
    """
    Consumes English text from a queue, translates it into an ASL gloss sequence,
    and pushes the sequence to the output gloss queue.
    """
    def __init__(self, text_queue: queue.Queue, gloss_queue: queue.Queue, is_running_callback, config_file="asl_rules.json"):
        self.text_queue = text_queue
        self.gloss_queue = gloss_queue
        self.is_running_callback = is_running_callback
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, "config", config_file)
        
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                rules = json.load(f)
                self.stop_words = set(rules.get("stop_words", []))
                self.time_words = set(rules.get("time_words", []))
        else:
            logger.warning(f"Config file {config_file} not found at {config_path}. Using empty rules.")
            self.stop_words = set()
            self.time_words = set()

    def start(self):
        threading.Thread(target=self._translate_loop, daemon=True).start()

    def _translate_loop(self):
        while self.is_running_callback():
            try:
                text = self.text_queue.get(timeout=1)
            except queue.Empty:
                continue
                
            glosses = self.text_to_gloss(text)
            if glosses:
                logger.info(f"Translated to ASL: {glosses}")
                self.gloss_queue.put(glosses)

    def text_to_gloss(self, text: str) -> list:
        clean_text = re.sub(r'[^\w\s]', '', text.lower())
        words = clean_text.split()
        
        time_glosses = []
        topic_comment_glosses = []
        
        for word in words:
            if word in self.stop_words:
                continue
            upper_word = word.upper()
            if word in self.time_words:
                time_glosses.append(upper_word)
            else:
                topic_comment_glosses.append(upper_word)
        
        return time_glosses + topic_comment_glosses
