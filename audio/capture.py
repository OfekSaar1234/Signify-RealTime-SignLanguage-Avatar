import pyaudiowpatch as pyaudio
import numpy as np
import time
import queue
import threading
from utils.logger import logger

class SystemAudioCapture:
    """
    Captures system audio using WASAPI Loopback, applies Voice Activity Detection (VAD)
    based on RMS volume, and pushes complete speech segments to the provided queue.
    """
    def __init__(self, speech_queue: queue.Queue, is_running_callback, config=None):
        self.speech_queue = speech_queue
        self.is_running_callback = is_running_callback
        self.config = config or {}
        
        # Constants from config or defaults
        self.chunk_size = self.config.get("chunk_size", 4096)
        self.silence_threshold = self.config.get("silence_threshold", 500)
        self.pyaudio_instance = pyaudio.PyAudio()
        
    def start(self):
        threading.Thread(target=self._capture_loop, daemon=True).start()

    def _capture_loop(self):
        time.sleep(2) # Give the system time to boot UI
        try:
            wasapi_info = self.pyaudio_instance.get_host_api_info_by_type(pyaudio.paWASAPI)
        except OSError:
            logger.error("WASAPI is not available on this system.")
            return

        default_speakers = self.pyaudio_instance.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
        loopback_device = None
        
        if not default_speakers["isLoopbackDevice"]:
            for loopback in self.pyaudio_instance.get_loopback_device_info_generator():
                if default_speakers["name"] in loopback["name"]:
                    loopback_device = loopback
                    break
        else:
            loopback_device = default_speakers
            
        if not loopback_device:
            logger.error("Default loopback output device not found.")
            return
            
        logger.info(f"Target Audio Device: {loopback_device['name']}")
        
        raw_audio_queue = queue.Queue()
        
        def callback(in_data, frame_count, time_info, status):
            raw_audio_queue.put(in_data)
            return (in_data, pyaudio.paContinue)
        
        sample_rate = int(loopback_device["defaultSampleRate"])
        channels = loopback_device["maxInputChannels"]
        sample_width = self.pyaudio_instance.get_sample_size(pyaudio.paInt16)
        
        stream = self.pyaudio_instance.open(
            format=pyaudio.paInt16, channels=channels, rate=sample_rate,
            frames_per_buffer=self.chunk_size, input=True,
            input_device_index=loopback_device["index"], stream_callback=callback
        )
        
        stream.start_stream()
        logger.info("🎙️ Live System Audio (Loopback) Mode Activated 🎙️")
        
        max_silence_chunks = int((sample_rate / self.chunk_size) * 1.5) 
        max_recording_chunks = int((sample_rate / self.chunk_size) * 15) 
        
        frames = []
        is_recording = False
        silence_chunks = 0
        
        while self.is_running_callback():
            try:
                chunk = raw_audio_queue.get(timeout=1)
            except queue.Empty:
                continue
                
            audio_data_np = np.frombuffer(chunk, dtype=np.int16)
            if channels > 1:
                # Downmix to Mono by taking one channel
                audio_data_np = audio_data_np[::channels]
            
            mono_chunk = audio_data_np.tobytes()
            rms = np.sqrt(np.mean(np.square(audio_data_np.astype(np.float32)))) if len(audio_data_np) > 0 else 0
            
            if rms > self.silence_threshold:
                if not is_recording: 
                    logger.debug("Audio detected! Recording...")
                is_recording = True
                silence_chunks = 0
                frames.append(mono_chunk)
                
            elif is_recording:
                silence_chunks += 1
                frames.append(mono_chunk)
                
            # Trigger processing on Silence OR Max Duration reached
            if is_recording and (silence_chunks > max_silence_chunks or len(frames) > max_recording_chunks):
                is_recording = False 
                audio_bytes = b''.join(frames)
                frames = [] 
                
                # Push the complete audio segment to the next stage of the pipeline
                # We need to pass sample_rate and sample_width so the transcriber knows how to read it
                self.speech_queue.put({
                    "audio_bytes": audio_bytes,
                    "sample_rate": sample_rate,
                    "sample_width": sample_width
                })
                    
        stream.stop_stream()
        stream.close()
        self.pyaudio_instance.terminate()
        logger.info("Audio capture loop cleanly exited.")
