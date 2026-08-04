import os
import requests
from bs4 import BeautifulSoup
import concurrent.futures
import subprocess

PROJECT_ROOT = r"C:\Users\User\Desktop\Signify"
MP4_DIR = os.path.join(PROJECT_ROOT, "assets", "mp4")

words_to_check = ["application", "want", "design", "program"]

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
    executor.map(fetch_and_download, words_to_check)

print("Finished downloads. Now running dictionary_builder.py...")

# Run dictionary_builder.py
subprocess.run(["python", os.path.join(PROJECT_ROOT, "scripts", "dictionary_builder.py")], check=True)

print("Done pipeline.")
