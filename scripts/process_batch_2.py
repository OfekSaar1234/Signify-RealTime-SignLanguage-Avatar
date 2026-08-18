import os
import re
import requests
from bs4 import BeautifulSoup
import concurrent.futures
import subprocess

PROJECT_ROOT = r"C:\Users\User\Desktop\Signify"
MP4_DIR = os.path.join(PROJECT_ROOT, "assets", "mp4")
JSON_DIR = os.path.join(PROJECT_ROOT, "assets", "jsons")

words=[
    "accept", "achieve", "adapt", "adjust", "admire", "admit", "advise", "afford", "agree", "alert",
    "allow", "amuse", "analyze", "announce", "annoy", "answer", "apologize", "appear", "applaud", "appreciate",
    "approve", "argue", "arrange", "arrest", "arrive", "attach", "attack", "attempt", "attend", "attract",
    "avoid", "awake", "bake", "balance", "ban", "bang", "bare", "bat", "bathe", "battle",
    "beam", "beg", "behave", "belong", "bleach", "bless", "blind", "blink", "blot", "blush",
    "boast", "boil", "bolt", "bomb", "book", "bore", "borrow", "bounce", "bow", "box",
    "brake", "branch", "breathe", "bruise", "brush", "bubble", "bump", "burn", "bury", "buzz",
    "calculate", "camp", "care", "carry", "carve", "cause", "challenge", "change", "charge", "chase",
    "cheat", "check", "cheer", "chew", "choke", "chop", "claim", "clap", "clean", "clear",
    "clip", "close", "coach", "coil", "collect", "color", "comb", "command", "communicate", "compare",
    "compete", "complain", "complete", "concentrate", "concern", "confess", "confuse", "connect", "consider", "consist",
    "contain", "continue", "copy", "correct", "cough", "count", "cover", "crack", "crash", "crawl",
    "cross", "crush", "cry", "cure", "curl", "curve", "cycle", "dam", "damage", "dance",
    "dare", "decay", "deceive", "decide", "decorate", "delay", "delight", "deliver", "depend", "describe",
    "desert", "deserve", "destroy", "detect", "develop", "disagree", "disappear", "disapprove", "disarm", "discover",
    "dislike", "divide", "double", "doubt", "drag", "drain", "dream", "dress", "drip", "drop",
    "drown", "drum", "dry", "dust", "earn", "educate", "embarrass", "employ", "empty", "encourage",
    "end", "enjoy", "enter", "entertain", "escape", "examine", "excite", "excuse", "exercise", "exist",
    "expand", "expect", "explain", "explode", "extend", "face", "fade", "fail", "fancy", "fasten",
    "fax", "fear", "fence", "fetch", "file", "fill", "film", "fire", "fit", "fix",
    "flap", "flash", "float", "flood", "flow", "flower", "fold", "follow", "fool", "force",
    "form", "found", "frame", "frighten", "fry", "gather", "gaze", "glow", "glue", "grab",
    "grate", "grease", "greet", "grin", "grip", "groan", "guarantee", "guard", "guess", "guide",
    "hammer", "hand", "handle", "hang", "happen", "harass", "harm", "hate", "haunt", "head",
    "heal", "heap", "heat", "help", "hook", "hop", "hope", "hover", "hug", "hum",
    "hunt", "hurry", "identify", "ignore", "imagine", "impress", "improve", "include", "increase", "influence",
    "inform", "inject", "injure", "instruct", "intend", "interest", "interfere", "interrupt", "introduce", "invent",
    "invite", "irritate", "itch", "jail", "jam", "jog", "join", "joke", "judge", "juggle",
    "jump", "kick", "kiss", "kneel", "knit", "knock", "knot", "label", "land", "last",
    "laugh", "launch", "learn", "level", "license", "lick", "lie", "lighten", "like", "list",
    "listen", "live", "load", "lock", "look", "love", "man", "manage", "march", "mark",
    "marry", "match", "mate", "matter", "measure", "meddle", "melt", "memorize", "mend", "miss",
    "mix", "moan", "moor", "mourn", "move", "muddle", "mug", "multiply", "murder", "nail",
    "name", "need", "nest", "nod", "note", "notice", "number", "obey", "object", "observe",
    "obtain", "occur", "offend", "offer", "open", "order", "pack", "paddle", "paint", "park",
    "part", "pass", "paste", "pat", "pause", "peck", "pedal", "peel", "peep", "perform",
    "permit", "phone", "pick", "pinch", "pine", "place", "plan", "plant", "play", "please",
    "plug", "point", "poke", "polish", "pop", "possess", "post", "pour", "practice", "pray",
    "preach", "precede", "prefer", "prepare", "present", "preserve", "press", "pretend", "prevent", "prick",
    "print", "produce", "program", "promise", "protect", "provide", "pull", "pump", "punch", "puncture",
    "punish", "push", "question", "queue", "race", "radiate", "rain", "raise", "reach", "realize",
    "receive", "recognize", "record", "reduce", "reflect", "refuse", "regret", "reign", "reject", "rejoice",
    "relax", "release", "rely", "remain", "remember", "remind", "remove", "repair", "repeat", "replace",
    "reply", "report", "reproduce", "request", "rescue", "retire", "return", "rhyme", "rinse", "risk",
    "rob", "rock", "roll", "rot", "rub", "ruin", "rule", "rush", "sack", "sail",
    "satisfy", "save", "saw", "scare", "scatter", "scold", "scorch", "scrape", "scratch", "scream",
    "screw", "seal", "search", "separate", "serve", "settle", "shade", "share", "shave", "shelter",
    "shiver", "shock", "shop", "shrug", "sigh", "sign", "signal", "sin", "sip", "ski",
    "skip", "slap", "slip", "slow", "smash", "smell", "smile", "smoke", "snatch", "sneeze",
    "sniff", "snore", "snow", "soak", "soothe", "sound", "spare", "spark", "sparkle", "spell",
    "spill", "spoil", "spot", "spray", "sprout", "squash", "squeak", "squeal", "squeeze", "stain",
    "stamp", "stare", "start", "stay", "steer", "step", "stir", "stitch", "stop", "store",
    "strap", "strengthen", "stretch", "strip", "stroke", "stuff", "subtract", "succeed", "suck", "suffer",
    "suggest", "suit", "supply", "support", "suppose", "surprise", "surround", "suspect", "suspend", "switch",
    "talk", "tame", "tap", "taste", "tease", "telephone", "tempt", "terrify", "test", "thank",
    "thaw", "tick", "tickle", "tie", "time", "tip", "tire", "touch", "tour", "tow",
    "trace", "trade", "train", "transport", "trap", "travel", "treat", "tremble", "trick", "trip",
    "trot", "trouble", "trust", "try", "tug", "tumble", "turn", "twist", "type", "undress",
    "unfasten", "unite", "unlock", "unpack", "untidy", "use", "vanish", "visit", "wail", "wait",
    "walk", "wander", "want", "warm", "warn", "wash", "waste", "watch", "water", "wave",
    "weigh", "welcome", "whine", "whip", "whirl", "whisper", "whistle", "wink", "wipe", "wish",
    "wobble", "wonder", "work", "worry", "wrap", "wreck", "wrestle", "wriggle", "xray", "yawn",
    "yell", "zip", "zoom", "actor", "adjective", "adult", "adventure", "advice", "afternoon", "airport",
    "album", "alcohol", "alien", "ambulance", "anger", "animal", "apartment", "apple", "architect", "arm",
    "army", "art", "artist", "ash", "assistant", "athlete", "atmosphere", "attack", "audience", "author",
    "autumn", "avenue", "baby", "background", "bacon", "badge", "bag", "baker", "balloon", "banana",
    "bank", "bar", "baseball", "basket", "bath", "bathroom", "battery", "beach", "bear", "beard",
    "bed", "bedroom", "beer", "belt", "bench", "bicycle", "bird", "birth", "birthday", "biscuit",
    "bit", "bite", "blade", "blanket", "block", "blood", "blouse", "board", "boat", "body",
    "bomb", "bone", "book", "boot", "border", "bottle", "bottom", "bowl", "boy", "brain",
    "branch", "brass", "bread", "breakfast", "breath", "brick", "bridge", "brother", "brush", "bucket",
    "budget", "building", "bulb", "bus", "bush", "business", "butter", "button", "cabbage", "cable",
    "cafe", "cake", "calculator", "calendar", "calf", "call", "camera", "camp", "campaign", "can",
    "canal", "candle", "cap", "capital", "captain", "car", "card", "cardboard", "carpet", "carrot",
    "cart", "case", "cash", "castle", "cat", "cattle", "cause", "cave", "ceiling", "cell",
    "cent", "center", "century", "chain", "chair", "chalk", "chance", "change", "channel", "chapter",
    "character", "charge", "charity", "cheese", "chemical", "chemistry", "chest", "chicken", "chief", "child",
    "chin", "chocolate", "choice", "church", "circle", "city", "class", "classroom", "clay", "clerk",
    "climate", "clock", "cloth", "clothes", "cloud", "club", "coach", "coal", "coast", "coat",
    "code", "coffee", "coin", "collar", "college", "color", "column", "comb", "comedy", "committee",
    "company", "competition", "computer", "condition", "connection", "continent", "contract", "cook", "copper", "copy",
    "cord", "corn", "corner", "cost", "cotton", "cough", "country", "course", "court", "cousin",
    "cow", "crack", "cream", "creator", "creature", "credit", "crew", "crime", "criminal", "crop",
    "cross", "crowd", "crown", "cry", "culture", "cup", "cupboard", "curtain", "curve", "cushion",
    "custom", "customer", "cycle", "damage", "dance", "danger", "dark", "data", "daughter", "day",
    "death", "debt", "decision", "decrease", "deep", "deer", "degree", "delay", "demand", "dentist",
    "department", "depth", "desert", "design", "desire", "desk", "detail", "development", "diamond", "diary",
    "dictionary", "diet", "difference", "difficulty", "dinner", "direction", "director", "dirt", "discovery", "disease",
    "dish", "distance", "doctor", "dog", "dollar", "door", "dot", "doubt", "drain", "drawer",
    "dress", "drink", "driver", "drop", "drug", "drum", "dust", "duty", "ear", "earth",
    "east", "edge", "education", "effect", "egg", "elbow", "election", "electricity", "elephant", "employee",
    "employer", "energy", "engine", "engineer", "entertainment", "entrance", "entry", "environment", "equipment", "error",
    "estate", "event", "exam", "examination", "example", "exchange", "excitement", "exercise", "experience", "experiment",
    "expert", "explanation", "eye", "face", "fact", "factory", "fall", "family", "fan", "farm",
    "farmer", "fat", "father", "fault", "fear", "feather", "fee", "feeling", "female", "fence",
    "festival", "fiction", "field", "fight", "figure", "file", "film", "finger", "fire", "fish",
    "flag", "flame", "flavor", "flesh", "flight", "flock", "floor", "flower", "flour", "fly",
    "focus", "fog", "fold", "food", "foot", "football", "force", "forest", "fork", "form",
    "fortune", "frame", "freedom", "friend", "frog", "front", "fruit", "fuel", "fun", "function",
    "fund", "furniture", "future", "gallery", "game", "garage", "garden", "garlic", "gas", "gate"
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
