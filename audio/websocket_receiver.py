import asyncio
import websockets
import numpy as np
import queue
import threading
from utils.logger import logger

class WebSocketAudioReceiver:
    """
    Listens for audio bytes sent over WebSockets from the LG webOS TV App.
    """
    def __init__(self, speech_queue: queue.Queue, is_running_callback, host="0.0.0.0", port=8766, config=None):
        self.speech_queue = speech_queue
        self.is_running_callback = is_running_callback
        self.host = host
        self.port = port
        self.config = config or {}
        # Assume incoming is Int16 at 16000Hz (for Whisper)
        self.sample_rate = self.config.get("sample_rate", 16000)
        self.sample_width = 2
        self.silence_threshold = self.config.get("silence_threshold_rms", 100)
        self.loop = None

    def start(self):
        threading.Thread(target=self._run_server, daemon=True).start()

    def _run_server(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        async def main_loop():
            async with websockets.serve(self._handle_client, self.host, self.port):
                logger.info(f"[AUDIO] WebSocket Receiver listening on ws://{self.host}:{self.port}")
                while self.is_running_callback():
                    await asyncio.sleep(1)
                    
        self.loop.run_until_complete(main_loop())

    async def _handle_client(self, websocket, path=None):
        logger.info(f"Client connected for audio streaming: {websocket.remote_address}")
        # VAD Buffering State
        frames = []
        is_recording = False
        silence_chunks = 0
        
        # Max lengths based on 85ms chunks (4096 samples at 16000Hz)
        max_silence_chunks = 3   # ~0.25 seconds of silence (faster triggering)
        max_recording_chunks = 23 # ~2.0 seconds maximum recording
        
        try:
            async for message in websocket:
                if not self.is_running_callback():
                    break
                
                if isinstance(message, bytes):
                    audio_data_np = np.frombuffer(message, dtype=np.int16)
                    rms = np.sqrt(np.mean(np.square(audio_data_np.astype(np.float32)))) if len(audio_data_np) > 0 else 0
                    
                    if rms > self.silence_threshold:
                        is_recording = True
                        silence_chunks = 0
                        frames.append(message)
                    elif is_recording:
                        silence_chunks += 1
                        frames.append(message)
                        
                    if is_recording and (silence_chunks > max_silence_chunks or len(frames) > max_recording_chunks):
                        is_recording = False
                        audio_bytes = b''.join(frames)
                        frames = []
                        
                        logger.debug("WebSocket audio segment completed. Sending to queue.")
                        self.speech_queue.put({
                            "audio_bytes": audio_bytes,
                            "sample_rate": self.sample_rate,
                            "sample_width": self.sample_width,
                            "source": "websocket"
                        })
                else:
                    logger.debug("Received non-binary message on audio websocket")
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {websocket.remote_address}")
        except Exception as e:
            logger.error(f"WebSocket Audio Receiver Error: {e}")
