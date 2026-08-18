import os
import re
import requests
from bs4 import BeautifulSoup
import concurrent.futures
import subprocess

PROJECT_ROOT = r"C:\Users\User\Desktop\Signify"
MP4_DIR = os.path.join(PROJECT_ROOT, "assets", "mp4")
JSON_DIR = os.path.join(PROJECT_ROOT, "assets", "jsons")

words = [
    "the", "of", "to", "and", "a", "in", "is", "it", "you", "that",
    "he", "was", "for", "on", "are", "as", "with", "his", "they", "i",
    "at", "be", "this", "have", "from", "or", "one", "had", "by", "word",
    "but", "not", "what", "all", "were", "we", "when", "your", "can", "said",
    "there", "use", "an", "each", "which", "she", "do", "how", "their", "if",
    "will", "up", "other", "about", "out", "many", "then", "them", "these", "so",
    "some", "her", "would", "make", "like", "him", "into", "time", "has", "look",
    "two", "more", "write", "go", "see", "number", "no", "way", "could", "people",
    "my", "than", "first", "water", "been", "call", "who", "oil", "its", "now",
    "find", "long", "down", "day", "did", "get", "come", "made", "may", "part",
    "over", "new", "sound", "take", "only", "little", "work", "know", "place", "year",
    "live", "me", "back", "give", "most", "very", "after", "thing", "our", "just",
    "name", "good", "sentence", "man", "think", "say", "great", "where", "help", "through",
    "much", "before", "line", "right", "too", "mean", "old", "any", "same", "tell",
    "boy", "follow", "came", "want", "show", "also", "around", "form", "three", "small",
    "set", "put", "end", "does", "another", "well", "large", "must", "big", "even",
    "such", "because", "turn", "here", "why", "ask", "went", "men", "read", "need",
    "land", "different", "home", "us", "move", "try", "kind", "hand", "picture", "again",
    "change", "off", "play", "spell", "air", "away", "animal", "house", "point", "page",
    "letter", "mother", "answer", "found", "study", "still", "learn", "should", "america", "world",
    "high", "every", "near", "add", "food", "between", "own", "below", "country", "plant",
    "last", "school", "father", "keep", "tree", "never", "start", "city", "earth", "eye",
    "light", "thought", "head", "under", "story", "saw", "left", "dont", "few", "while",
    "along", "might", "close", "something", "seem", "next", "hard", "open", "example", "begin",
    "life", "always", "those", "both", "paper", "together", "got", "group", "often", "run",
    "important", "until", "children", "side", "feet", "car", "mile", "night", "walk", "white",
    "sea", "began", "grow", "took", "river", "four", "carry", "state", "once", "book",
    "hear", "stop", "without", "second", "late", "miss", "idea", "enough", "eat", "face",
    "watch", "far", "indian", "real", "almost", "let", "above", "girl", "sometimes", "mountains",
    "cut", "young", "talk", "soon", "list", "song", "being", "leave", "family", "its",
    "body", "music", "color", "stand", "sun", "question", "fish", "area", "mark", "dog",
    "horse", "birds", "problem", "complete", "room", "knew", "since", "ever", "piece", "told",
    "usually", "didnt", "friends", "easy", "heard", "order", "red", "door", "sure", "become",
    "top", "ship", "across", "today", "during", "short", "better", "best", "however", "low",
    "hours", "black", "products", "happen", "whole", "measure", "remember", "early", "waves", "reached",
    "listen", "wind", "rock", "space", "covered", "fast", "several", "hold", "himself", "toward",
    "five", "step", "morning", "passed", "vowel", "true", "hundred", "against", "pattern", "numeral",
    "table", "north", "slowly", "money", "map", "farm", "pulled", "draw", "voice", "seen",
    "cold", "cried", "plan", "notice", "south", "sing", "war", "ground", "fall", "king",
    "town", "ill", "unit", "figure", "certain", "field", "travel", "wood", "fire", "upon",
    "done", "english", "road", "half", "ten", "fly", "gave", "box", "finally", "wait",
    "correct", "oh", "quickly", "person", "became", "shown", "minutes", "strong", "verb", "stars",
    "front", "feel", "fact", "inches", "street", "decided", "contain", "course", "surface", "produce",
    "building", "ocean", "class", "note", "nothing", "rest", "carefully", "scientists", "inside", "wheels",
    "stay", "green", "known", "island", "week", "less", "machine", "base", "ago", "stood",
    "plane", "system", "behind", "ran", "round", "boat", "game", "force", "brought", "understand",
    "warm", "common", "bring", "explain", "dry", "though", "language", "shape", "deep", "thousands",
    "yes", "clear", "equation", "yet", "government", "filled", "heat", "full", "hot", "check",
    "object", "am", "rule", "among", "noun", "power", "cannot", "able", "six", "size",
    "dark", "ball", "material", "special", "heavy", "fine", "pair", "circle", "include", "built",
    "cant", "matter", "square", "syllables", "perhaps", "bill", "felt", "suddenly", "test", "direction",
    "center", "farmers", "ready", "anything", "divided", "general", "energy", "subject", "europe", "moon",
    "region", "return", "believe", "dance", "members", "picked", "simple", "cells", "paint", "mind",
    "love", "cause", "rain", "exercise", "eggs", "train", "blue", "window", "difference", "distance",
    "heart", "site", "sum", "summer", "wall", "forest", "probably", "legs", "sat", "main",
    "winter", "wide", "written", "length", "reason", "kept", "interest", "arms", "brother", "race",
    "present", "beautiful", "store", "job", "edge", "past", "sign", "record", "finished", "discovered",
    "wild", "happy", "beside", "gone", "sky", "glass", "million", "west", "lay", "weather",
    "root", "instruments", "meet", "third", "months", "paragraph", "raised", "represent", "whether", "clothes",
    "flowers", "shall", "teacher", "held", "describe", "drive", "cross", "speak", "solve", "appear",
    "metal", "son", "either", "ice", "sleep", "village", "factors", "result", "jumped", "snow",
    "ride", "care", "floor", "hill", "pushed", "baby", "buy", "century", "outside", "everything",
    "tall", "already", "instead", "phrase", "soil", "bed", "copy", "free", "hope", "spring",
    "case", "laughed", "nation", "quite", "type", "themselves", "temperature", "bright", "lead", "everyone",
    "method", "section", "dictionary", "hair", "age", "amount", "scale", "pounds", "although", "per",
    "broken", "moment", "tiny", "possible", "gold", "milk", "quiet", "natural", "lot", "stone",
    "act", "build", "middle", "speed", "count", "consonant", "someone", "sail", "rolled", "bear",
    "wonder", "smiled", "angle", "fraction", "africa", "killed", "melody", "bottom", "trip", "hole",
    "poor", "lets", "fight", "surprise", "french", "died", "beat", "exactly", "remain", "dress",
    "cat", "myself", "blood", "desk", "catch", "grew", "string", "symbol", "clean", "break",
    "ladies", "uncle", "hunting", "level", "child", "thick", "dropped", "stretch", "shoes", "actually",
    "nose", "afraid", "dead", "sugar", "adjective", "fig", "office", "huge", "gun", "similar",
    "death", "score", "forward", "experience", "rose", "allow", "fear", "workers", "washington", "greek",
    "women", "bought", "led", "march", "northern", "create", "british", "difficult", "match", "win",
    "doesnt", "steel", "total", "deal", "determine", "evening", "hoe", "rope", "cotton", "apple",
    "details", "entire", "corn", "substances", "smell", "tools", "conditions", "cows", "track", "arrived",
    "located", "sir", "seat", "division", "effect", "underline", "view", "born", "oxygen", "plural",
    "various", "agreed", "opposite", "wrong", "chart", "prepared", "pretty", "solution", "fresh", "shop",
    "suffix", "especially", "ahead", "chance", "gather", "basic", "safe", "liquid", "collect", "master",
    "valley", "double", "tie", "rich", "demon", "grand", "pure", "tube", "math", "meat",
    "wash", "exist", "bare", "mice", "tone", "pick", "join", "suggest", "separate", "grace",
    "pocket", "single", "equal", "decimal", "touch", "yours", "cent", "plain", "receive", "mouth",
    "exact", "yard", "slave", "engine", "guess", "silent", "trade", "rather", "compare", "crowd",
    "poem", "enjoy", "elements", "indicate", "except", "flat", "twenty", "motion", "leg", "shoot",
    "thin", "position", "enter", "major", "observe", "necessary", "weight", "curve", "fit", "sand",
    "science", "magnet", "silver", "branch", "sister", "discuss", "guide", "pitch", "coat", "mass",
    "band", "slip", "dream", "condition", "feed", "tool", "arrive", "locate", "gather", "wrong",
    "meant", "ahead", "fresh", "safe", "chance", "subtract", "observe", "heavy", "exact", "liquid",
    "master", "pick", "engine", "twenty", "decimal", "slave", "single", "grace", "motion", "blood",
    "plain", "thin", "receive", "cent", "equal", "position", "enter", "major", "bare", "tube",
    "join", "pocket", "tone", "mice", "grand", "pure", "math", "meat", "demon", "rich",
    "exist", "tie", "wash", "guess", "fraction", "equal", "exact", "decimal", "grace", "single",
    "plain", "slave", "cent", "engine", "equal", "motion", "twenty", "exact", "thin", "position"
]
words = list(set(words)) # Remove any duplicates

print(f"Loaded {len(words)} unique words.")

def json_exists(word):
    prefix = word[:2] if len(word) >= 2 else word
    first_letter = word[0] if len(word) > 0 else ""
    json_path = os.path.join(JSON_DIR, first_letter, prefix, f"{word}.json")
    return os.path.exists(json_path)

def mp4_exists(word):
    return os.path.exists(os.path.join(MP4_DIR, f"{word}.mp4"))

words_to_download = []
for word in words:
    if not json_exists(word):
        if not mp4_exists(word):
            words_to_download.append(word)
            
print(f"Need to download {len(words_to_download)} words.")

def fetch_and_download(word):
    url = f"https://www.signasl.org/sign/{word}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"[-] No page found for: {word}")
            return False

        soup = BeautifulSoup(response.text, 'html.parser')
        video_tag = soup.find('video')
        if not video_tag:
            print(f"[-] No video tag found on page for: {word}")
            return False
            
        source_tag = video_tag.find('source')
        video_url = source_tag['src'] if source_tag and source_tag.has_attr('src') else video_tag.get('src')
        if not video_url:
            print(f"[-] Could not extract video URL for: {word}")
            return False

        if video_url.startswith('/'):
            video_url = f"https://www.signasl.org{video_url}"

        vid_response = requests.get(video_url, stream=True, timeout=15)
        vid_response.raise_for_status()
        
        file_path = os.path.join(MP4_DIR, f"{word}.mp4")
        with open(file_path, "wb") as f:
            for chunk in vid_response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        print(f"[+] Success: {word}.mp4")
        return True
    except Exception as e:
        print(f"[!] Error processing '{word}': {e}")
        return False

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    executor.map(fetch_and_download, words_to_download)

print("Finished downloads. Now running dictionary_builder.py...")

# Run dictionary_builder.py
subprocess.run(["python", os.path.join(PROJECT_ROOT, "scripts", "dictionary_builder.py")], check=True)

print("Done pipeline.")
