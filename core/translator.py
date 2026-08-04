import re
import json
import os
import queue
import threading
from utils.logger import logger

def simple_lemmatize(word):
    # Dictionary of explicit irregular verbs or specific mappings
    irregular = {
        "spoke": "speak",
        "wanted": "want",
        "designed": "design",
        "communicating": "communication",
        "app": "application",
        "saw": "see",
        "went": "go",
        "ate": "eat",
        "drank": "drink",
        "slept": "sleep",
        "bought": "buy",
        "sold": "sell",
        "paid": "pay",
        "thought": "think",
        "made": "make"
    }
    if word in irregular:
        return irregular[word]
        
    # Simple rule-based stripping for common regular verbs
    if len(word) > 4:
        if word.endswith("ing"):
            return word[:-3]
        if word.endswith("ed"):
            if word[-3] in ['t', 'd']:
                return word[:-2] # wanted -> want
            else:
                return word[:-1] # designed -> design
        if word.endswith("s") and not word.endswith("ss"):
            return word[:-1]
            
    return word

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
                
            # Safely lemmatize the word to base form
            word = simple_lemmatize(word)
            
            upper_word = word.upper()
            if word in self.time_words:
                time_glosses.append(upper_word)
            else:
                topic_comment_glosses.append(upper_word)
        
        return time_glosses + topic_comment_glosses
