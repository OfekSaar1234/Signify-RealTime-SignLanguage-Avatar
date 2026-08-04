import os
import re
import requests
from bs4 import BeautifulSoup
import concurrent.futures
import subprocess

PROJECT_ROOT = r"C:\Users\User\Desktop\Signify"
MP4_DIR = os.path.join(PROJECT_ROOT, "assets", "mp4")
JSON_DIR = os.path.join(PROJECT_ROOT, "assets", "jsons")

text = """
Hello everyone, we're really happy to be here today! Our project is an app designed to help deaf and hard-of-hearing people with everyday communication.

Our goal is to take speech and text in real time and turn it into a clear, simple 3D display of sign language on the screen.

We wanted to create an easy, accessible tool that helps bridge the language gap and makes communicating smoother for everyone.
"""

def clean_word(word):
    # Remove non-alphabetical characters except digits if needed, here we just keep alphanumeric
    cleaned = re.sub(r'[^a-z0-9]', '', word.lower())
    return cleaned

# extract words
raw_words = re.split(r'[\s\-]+', text)
words = set([clean_word(w) for w in raw_words if w])
words = [w for w in words if len(w) > 0]

print(f"Extracted {len(words)} unique words.")

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
