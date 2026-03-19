"""
==============================================================================
PROJECT: Signify - Sign Language Translation Avatar
MODULE:  asl_translator.py
PURPOSE: The NLP (Natural Language Processing) Engine.
         Converts standard English text into ASL Glosses (Sign Language Syntax).
         Designed to be lightning-fast for future real-time audio streams.
==============================================================================
"""
import re # 're' stands for Regular Expressions. It is a built-in Python library for advanced text search and manipulation.
import json
import os

class ASLTranslator:
    def __init__(self, config_file="asl_rules.json"):
        """
        Initializes the rules and dictionaries for the ASL translation.
        We use Python 'sets' (the {} brackets) instead of lists [] because 
        searching inside a set is mathematically faster (O(1) time complexity).
        """
        
        # Determine the absolute path to the config file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config", config_file)
        
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                rules = json.load(f)
                self.stop_words = set(rules.get("stop_words", []))
                self.time_words = set(rules.get("time_words", []))
        else:
            print(f"[WARNING] {config_file} not found.")
          

    def text_to_gloss(self, text: str) -> list:
        """
        Takes a normal English sentence and converts it into an ASL Gloss sequence.
        
        :param text: The raw string from the Google Speech-to-Text API.
        :return: A list of strings representing the ASL signs in the correct order.
        """
        
        # --- EXPLAINING re.sub() ---
        # re.sub(pattern, replacement, string) searches for a 'pattern' and replaces it.
        # r'[^\w\s]' is the Regular Expression pattern:
        #   ^    = means "NOT"
        #   \w   = means "Word characters" (a-z, A-Z, 0-9)
        #   \s   = means "Whitespace" (spaces)
        # So, [^\w\s] means: "Find anything that is NOT a letter, NOT a number, and NOT a space."
        # This perfectly targets punctuation like commas (,), periods (.), question marks (?), etc.
        # We replace them with '' (an empty string), effectively deleting them!
        
        clean_text = re.sub(r'[^\w\s]', '', text.lower())
        
        # Split the clean sentence into an array of individual words based on spaces.
        words = clean_text.split()
        
        # We create two separate lists to reorganize the sentence structure.
        time_glosses = []
        topic_comment_glosses = []
        
        # Loop through every word in the sentence
        for word in words:
            
            # 1. REMOVE STOP WORDS
            if word in self.stop_words:
                continue  # 'continue' skips the rest of the loop and moves to the next word.
                
            # 2. CONVERT TO UPPERCASE (Standard ASL Gloss format)
            upper_word = word.upper()
            
            # 3. REORGANIZE SYNTAX
            # If the word is a time word (like "tomorrow"), put it in the time list.
            if word in self.time_words:
                time_glosses.append(upper_word)
            # Otherwise, put it in the standard topic list.
            else:
                topic_comment_glosses.append(upper_word)
        
        # 4. COMBINE THE LISTS
        # In Python, adding two lists together concatenates them.
        # We put the time words first, followed by the rest of the sentence.
        final_sequence = time_glosses + topic_comment_glosses
        
        return final_sequence

# ==========================================
# TEST BLOCK
# This code runs only if we run this specific file directly.
# this file will NOT run if you import this file into main.py.
# ==========================================
if __name__ == "__main__":
    # Create an instance of our translator engine
    translator = ASLTranslator()
    
    # A list of test cases: Each tuple contains (Input English, Expected ASL Output)
    tests = [
        # Test 1: Checks if stop words ('The', 'is') are deleted.
        ("The car is red", ["CAR", "RED"]),
        
        # Test 2: Checks if the time word ('tomorrow') jumps to the front.
        ("I am going to the sea tomorrow", ["TOMORROW", "I", "GOING", "SEA"]),
        
        # Test 3: Checks if punctuation (comma, question mark) is deleted successfully.
        ("Hello, how are you?", ["HELLO", "HOW", "YOU"]),
        
        # Test 4: A complex sentence with multiple time words.
        ("It is raining today in the morning", ["TODAY", "MORNING", "RAINING"])
    ]
    
    print("[SYSTEM] Running ASL Translator Tests...\n")
    
    # Loop through the tests and verify the logic
    for original, expected in tests:
        # Ask our engine to translate the original text
        result = translator.text_to_gloss(original)
        
        # Check if the engine's result matches what we expected
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        # Print the results to the terminal
        print(f"Original: '{original}'")
        print(f"ASL Gloss: {result}")
        print(f"Expected:  {expected}")
        print(f"Status:   {status}\n")
        print("-" * 40)