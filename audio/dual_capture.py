import pyaudiowpatch as pyaudio
import numpy as np
import time
import queue
import threading
from utils.logger import logger

class DualAudioCapture:
    """
    Captures both physical Microphone and system Loopback simultaneously.
    Uses a 'Voice Lock' to ensure only one source is processed at a time
    (speak one at a time rule).
    """
    def __init__(self, speech_queue: queue.Queue, is_running_callback, config=None):
        self.speech_queue = speech_queue
        self.is_running_callback = is_running_callback
        self.config = config or {}
        
        self.chunk_size = self.config.get("chunk_size", 4096)
        self.silence_threshold = self.config.get("silence_threshold_rms", 500)
        
        # Shared lock state to prevent clashing
        self.active_source_lock = threading.Lock()
        self.init_lock = threading.Lock()
        self.active_source = None  # Can be "mic", "loopback", or None

    def start(self):
        # We start both threads
        threading.Thread(target=self._capture_loop, args=("loopback",), daemon=True).start()
        # Stagger the start time slightly to help avoid PortAudio initialization clashes
        threading.Thread(target=self._capture_loop, args=("mic",), daemon=True).start()

    def _capture_loop(self, source_type: str):
        if source_type == "mic":
            time.sleep(2.5) # Staggered boot delay
        else:
            time.sleep(2.0)
        
        with self.init_lock:
            # Instantiate PyAudio inside the thread to avoid cross-thread PortAudio locks
            p_instance = pyaudio.PyAudio()
            
            target_device = None
            try:
                if source_type == "loopback":
                    wasapi_info = p_instance.get_host_api_info_by_type(pyaudio.paWASAPI)
                    default_output = p_instance.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
                    
                    if not default_output["isLoopbackDevice"]:
                        for loopback in p_instance.get_loopback_device_info_generator():
                            if default_output["name"] in loopback["name"]:
                                target_device = loopback
                                break
                        # Fallback if name matching fails (e.g., due to Windows character limits)
                        if not target_device:
                            for loopback in p_instance.get_loopback_device_info_generator():
                                target_device = loopback
                                break
                    else:
                        target_device = default_output
                else: # mic
                    # Use standard default API for the microphone to avoid WASAPI host errors
                    target_device = p_instance.get_default_input_device_info()
            except OSError as e:
                logger.error(f"[{source_type.upper()}] Could not get default devices: {e}")
                return

            if not target_device:
                logger.error(f"Target device for {source_type} not found.")
                return
                
            logger.info(f"[{source_type.upper()}] Target Audio Device: {target_device['name']}")
            
            raw_audio_queue = queue.Queue()
            
            def callback(in_data, frame_count, time_info, status):
                raw_audio_queue.put(in_data)
                return (in_data, pyaudio.paContinue)
            
            sample_rate = int(target_device["defaultSampleRate"])
            channels = target_device["maxInputChannels"]
            sample_width = p_instance.get_sample_size(pyaudio.paInt16)
            
            try:
                stream = p_instance.open(
                    format=pyaudio.paInt16, channels=channels, rate=sample_rate,
                    frames_per_buffer=self.chunk_size, input=True,
                    input_device_index=target_device["index"], stream_callback=callback
                )
                stream.start_stream()
            except Exception as e:
                logger.error(f"[{source_type.upper()}] Failed to open stream: {e}")
                return
                
            logger.info(f"[AUDIO] Live {source_type.capitalize()} Capture Started")
            
        # Dynamic Chunking from config
        max_silence_sec = self.config.get("silence_timeout_sec", 0.5)
        max_recording_sec = self.config.get("max_recording_sec", 5.0)
        max_silence_chunks = int((sample_rate / self.chunk_size) * max_silence_sec) 
        max_recording_chunks = int((sample_rate / self.chunk_size) * max_recording_sec)  
        
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
                audio_data_np = audio_data_np[::channels]
            
            mono_chunk = audio_data_np.tobytes()
            rms = np.sqrt(np.mean(np.square(audio_data_np.astype(np.float32)))) if len(audio_data_np) > 0 else 0
            
            if rms > self.silence_threshold:
                with self.active_source_lock:
                    if self.active_source is None:
                        # Claim the voice lock
                        self.active_source = source_type
                        is_recording = True
                        silence_chunks = 0
                        frames.append(mono_chunk)
                        logger.debug(f"[{source_type.upper()}] Voice Lock acquired. Recording...")
                    elif self.active_source == source_type:
                        # Continue recording if we own the lock
                        is_recording = True
                        silence_chunks = 0
                        frames.append(mono_chunk)
                    else:
                        # Another source is recording, we ignore our audio
                        pass
                
            elif is_recording:
                silence_chunks += 1
                frames.append(mono_chunk)
                
            if is_recording and (silence_chunks > max_silence_chunks or len(frames) > max_recording_chunks):
                is_recording = False 
                audio_bytes = b''.join(frames)
                frames = [] 
                
                # Release the lock
                with self.active_source_lock:
                    logger.debug(f"[{source_type.upper()}] Voice Lock released.")
                    self.active_source = None
                
                self.speech_queue.put({
                    "audio_bytes": audio_bytes,
                    "sample_rate": sample_rate,
                    "sample_width": sample_width,
                    "source": source_type
                })
                    
        stream.stop_stream()
        stream.close()
        p_instance.terminate()
        logger.info(f"[{source_type.upper()}] Audio capture loop cleanly exited.")
