import os
import requests
from dotenv import load_dotenv
import threading
import queue
from utils.logger import logger

load_dotenv()

class AudioTranscriber:
    """
    Consumes raw audio segments from a queue and transcribes them into text using
    the Deepgram API. Outputs the transcribed text to the next queue.
    """
    def __init__(self, speech_queue: queue.Queue, text_queue: queue.Queue, is_running_callback):
        self.speech_queue = speech_queue
        self.text_queue = text_queue
        self.is_running_callback = is_running_callback
        
        self.deepgram_api_key = os.environ.get("DEEPGRAM_API_KEY")
        if not self.deepgram_api_key:
            logger.error("DEEPGRAM_API_KEY is not set in .env")

    def start(self):
        threading.Thread(target=self._transcribe_loop, daemon=True).start()

    def _transcribe_loop(self):
        while self.is_running_callback():
            try:
                # Block until we receive a speech segment
                segment = self.speech_queue.get(timeout=1)
            except queue.Empty:
                continue

            audio_bytes = segment.get("audio_bytes")
            sample_rate = segment.get("sample_rate")
            sample_width = segment.get("sample_width")

            # Process in a separate daemon thread to not block the queue consumption
            threading.Thread(target=self._process_segment, args=(audio_bytes, sample_rate, sample_width), daemon=True).start()

    def _process_segment(self, audio_bytes, sample_rate, sample_width):
        try:
            url = f"https://api.deepgram.com/v1/listen?punctuate=true&model=nova-2&encoding=linear16&sample_rate={sample_rate}&channels=1"
            headers = {
                "Authorization": f"Token {self.deepgram_api_key}",
                "Content-Type": "audio/l16"
            }
            response = requests.post(url, headers=headers, data=audio_bytes)
            response.raise_for_status()
            
            result = response.json()
            text = result['results']['channels'][0]['alternatives'][0]['transcript']
            
            if text.strip():
                logger.info(f"Audio Transcribed (Deepgram): '{text}'")
                # Push the text to the NLP/Translator queue
                self.text_queue.put(text)
        except Exception as e:
            logger.error(f"Speech Recognition API Error: {e}")
