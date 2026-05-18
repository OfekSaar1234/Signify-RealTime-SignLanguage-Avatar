import os
import json
import queue

from utils.logger import logger
from core.translator import ASLTranslator
from core.animator import Animator
from output.renderer import OpenCVRenderer
from output.virtual_cam import VirtualCamStreamer
from output.streamer import WebSocketStreamer
from output.headless import HeadlessRenderer

# Input mechanisms
from audio.dual_capture import DualAudioCapture
from audio.transcriber import AudioTranscriber
from core.typing_input import TypingInput

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "app_settings.json")

def load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Configuration file missing at {CONFIG_PATH}. Using empty defaults.")
        return {}

if __name__ == "__main__":
    logger.info("Booting up Signify Pipeline Architecture...")
    app_settings = load_config()

    # Shared Queues
    speech_audio_queue = queue.Queue()
    text_queue = queue.Queue()
    gloss_queue = queue.Queue()
    frame_queue = queue.Queue(maxsize=30) # Backpressure

    # Global Run State
    is_running = True
    def is_running_callback():
        return is_running

    # Initialize Modules
    
    # 1. Outputs
    streamer = None
    network_cfg = app_settings.get("network", {})
    if network_cfg.get("enable_websocket", False):
        streamer = WebSocketStreamer(
            host=network_cfg.get("ws_host", "localhost"),
            port=network_cfg.get("ws_port", 8765)
        )
        streamer.start()

    output_mode = app_settings.get("output_mode", "opencv")
    
    # Force websocket for electron
    if output_mode == "electron" and not streamer:
        streamer = WebSocketStreamer(
            host=network_cfg.get("ws_host", "localhost"),
            port=network_cfg.get("ws_port", 8765)
        )
        streamer.start()

    if output_mode == "virtual_cam":
        logger.info("Initializing Output: Virtual Camera")
        renderer = VirtualCamStreamer(frame_queue, is_running_callback, app_settings, streamer=streamer)
    else:
        logger.info("Initializing Output: OpenCV Window")
        renderer = OpenCVRenderer(frame_queue, is_running_callback, app_settings, streamer=streamer)
    
    # 2. Core Logic
    animator = Animator(gloss_queue, frame_queue, is_running_callback, app_settings)
    animator.start()
    
    translator = ASLTranslator(text_queue, gloss_queue, is_running_callback)
    translator.start()

    # 3. Inputs
    input_mode = app_settings.get("input_mode", "typing")
    
    if input_mode == "audio_loopback" or input_mode == "dual_audio":
        logger.info(f"Initializing Input: Audio Capture ({input_mode})")
        transcriber = AudioTranscriber(speech_audio_queue, text_queue, is_running_callback)
        transcriber.start()
        
        capture = DualAudioCapture(speech_audio_queue, is_running_callback, config=app_settings.get("audio", {}))
        capture.start()
    else:
        logger.info("Initializing Input: Manual Typing")
        typing_input = TypingInput(text_queue, is_running_callback)
        typing_input.start()

    # Block on the Renderer loop until user quits (press 'q' on the OpenCV window)
    try:
        renderer.run_blocking()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received.")
    finally:
        is_running = False
        logger.info("Pipeline closed cleanly.")