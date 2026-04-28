import speech_recognition as sr
import threading
import queue
from utils.logger import logger

class AudioTranscriber:
    """
    Consumes raw audio segments from a queue and transcribes them into text using
    the Google Web Speech API. Outputs the transcribed text to the next queue.
    """
    def __init__(self, speech_queue: queue.Queue, text_queue: queue.Queue, is_running_callback):
        self.speech_queue = speech_queue
        self.text_queue = text_queue
        self.is_running_callback = is_running_callback
        self.recognizer = sr.Recognizer()

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
            audio_obj = sr.AudioData(audio_bytes, sample_rate, sample_width)
            text = self.recognizer.recognize_google(audio_obj)
            logger.info(f"Audio Transcribed: '{text}'")
            
            # Push the text to the NLP/Translator queue
            self.text_queue.put(text)
        except sr.UnknownValueError:
            logger.debug("Unrecognized background noise. Ignored.")
        except sr.RequestError as e:
            logger.error(f"Speech Recognition API Error: {e}")
