"""
==============================================================================
PROJECT: Signify - Sign Language Translation Avatar
MODULE:  download_videos.py
PURPOSE: ASL Video Scraper and Downloader.
         Fetches and downloads MP4 video files for specific ASL words 
         from signasl.org to build the local dataset.
==============================================================================
"""

import os
import requests
from bs4 import BeautifulSoup
import concurrent.futures

# --- CONFIGURATION ---
# my specific desktop path
DOWNLOAD_DIR = r"C:\Users\User\Desktop\Signify\assets\mp4"

# This ensures the folder is created if it doesn't already exist on your desktop
os.makedirs(DOWNLOAD_DIR, exist_ok=True) 

# The specific words needed to download
WORDS = [
    "hello", "goodbye", "yes", "no", "please", "thank", "you", "sorry", "excuse", "me",
    "help", "who", "what", "where", "when", "why", "how", "stop", "go", "come",
    "more", "finish", "eat", "drink", "sleep", "want", "need", "like", "love", "hate",
    "happy", "sad", "angry", "tired", "good", "bad", "beautiful", "ugly", "big", "small",
    "hot", "cold", "day", "night", "morning", "afternoon", "evening", "today", "tomorrow", "yesterday",
    "now", "later", "time", "home", "work", "school", "friend", "family", "mother", "father",
    "brother", "sister", "son", "daughter", "man", "woman", "boy", "girl", "name", "age",
    "color", "red", "blue", "green", "yellow", "black", "white", "number", "one", "two",
    "three", "four", "five", "six", "seven", "eight", "nine", "ten", "money", "buy",
    "sell", "pay", "cost", "cheap", "expensive", "food", "water", "apple", "book", "car",
    # Motivation Video Words
    "i", "dont", "know", "that", "dream", "is", "have", "care", "disappointing", 
    "it", "might", "been", "as", "working", "toward", "but", "are", "holding", 
    "in", "your", "mind", "its", "possible"
]

def fetch_and_download(word):
    """
    Scrapes the signasl.org webpage for the video URL of a given word 
    and downloads the MP4 file directly to the configured folder.
    
    :param word: The specific ASL word to search for and download.
    """
    url = f"https://www.signasl.org/sign/{word}"
    
    # We use a User-Agent so the website thinks we are a regular browser
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        # 1. Fetch the webpage
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"[-] No page found for: {word}")
            return

        # 2. Parse the HTML to find the video
        soup = BeautifulSoup(response.text, 'html.parser')
        video_tag = soup.find('video')
        
        if not video_tag:
            print(f"[-] No video tag found on page for: {word}")
            return
            
        source_tag = video_tag.find('source')
        video_url = source_tag['src'] if source_tag and source_tag.has_attr('src') else video_tag.get('src')
        
        if not video_url:
            print(f"[-] Could not extract video URL for: {word}")
            return

        # Handle relative URLs just in case
        if video_url.startswith('/'):
            video_url = f"https://www.signasl.org{video_url}"

        # 3. Download the actual video file
        vid_response = requests.get(video_url, stream=True, timeout=15)
        vid_response.raise_for_status()
        
        # Save directly to your chosen path
        file_path = os.path.join(DOWNLOAD_DIR, f"{word}.mp4")
        
        # Write the file in larger chunks for speed
        with open(file_path, "wb") as f:
            for chunk in vid_response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        print(f"[+] Success: {word}.mp4")

    except requests.exceptions.RequestException as e:
        print(f"[!] Network error processing '{word}': {e}")
    except Exception as e:
        print(f"[!] Error processing '{word}': {e}")

# --- EXECUTION ---
if __name__ == "__main__":
    print(f"Starting download of {len(WORDS)} ASL videos to {DOWNLOAD_DIR}...")
    
    # Concurrency: This runs 5 downloads at the same time. 
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(fetch_and_download, WORDS)
        
    print("All downloads finished! Check your desktop folder.")