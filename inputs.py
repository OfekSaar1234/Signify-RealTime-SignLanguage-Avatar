import threading
import queue
import time
import numpy as np
import speech_recognition as sr
import pyaudiowpatch as pyaudio
from asl_translator import ASLTranslator

def live_typing_stream(phrase_queue: queue.Queue, is_running_callback):
    """
    Runs in a separate thread. Acts as a simulator for the microphone API.
    Translates typed English into ASL glosses and pushes them to the shared queue.
    """
    translator = ASLTranslator()
    time.sleep(2) 
    
    print("\n" + "="*50)
    print("🎙️ LIVE INPUT MODE ACTIVATED 🎙️")
    print("Type an English sentence in the terminal and press ENTER.")
    print("To quit, click the video window and press 'q'.")
    print("="*50 + "\n")
    
    while is_running_callback():
        try:
            user_text = input("Type a sentence: ")
            
            if not user_text.strip():
                continue
                
            print(f"\n[MIC] You typed: '{user_text}'")
            asl_glosses = translator.text_to_gloss(user_text)
            print(f"[BRAIN] Translated to ASL: {asl_glosses}")
            
            phrase_queue.put(asl_glosses)
            
        except EOFError:
            break

def live_audio_stream(phrase_queue: queue.Queue, is_running_callback):
    """
    Runs in a separate thread. Acts as the system audio (loopback) listener.
    Captures audio continuously, chunks it using a Voice Activity (Volume) threshold,
    and sends complete phrases to Google Web Speech API natively without blocking.
    """
    translator = ASLTranslator()
    recognizer = sr.Recognizer()
    
    time.sleep(2) 
    
    print("\n" + "="*50)
    print("🎙️ LIVE SYSTEM AUDIO (LOOPBACK) MODE ACTIVATED 🎙️")
    print("Play a YouTube video or Zoom call. The system will detect when speech stops.")
    print("To quit, click the video window and press 'q'.")
    print("="*50 + "\n")
    
    with pyaudio.PyAudio() as p:
        try:
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        except OSError:
            print("[MIC ERROR] WASAPI is not available on this system.")
            return

        # Locate the default speakers and its hidden Loopback channel
        default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
        loopback_device = None
        
        if not default_speakers["isLoopbackDevice"]:
            for loopback in p.get_loopback_device_info_generator():
                if default_speakers["name"] in loopback["name"]:
                    loopback_device = loopback
                    break
        else:
            loopback_device = default_speakers
            
        if not loopback_device:
            print("[MIC ERROR] Default loopback output device not found.")
            return
            
        print(f"[MIC] Target Audio Device: {loopback_device['name']}")
        
        audio_queue = queue.Queue()
        
        def callback(in_data, frame_count, time_info, status):
            audio_queue.put(in_data)
            return (in_data, pyaudio.paContinue)
        
        sample_rate = int(loopback_device["defaultSampleRate"])
        channels = loopback_device["maxInputChannels"]
        sample_width = p.get_sample_size(pyaudio.paInt16)
        chunk_size = 4096 
        
        stream = p.open(
            format=pyaudio.paInt16, channels=channels, rate=sample_rate,
            frames_per_buffer=chunk_size, input=True,
            input_device_index=loopback_device["index"], stream_callback=callback
        )
        
        stream.start_stream()
        
        SILENCE_THRESHOLD = 500  
        MAX_SILENCE_CHUNKS = int((sample_rate / chunk_size) * 1.5) 
        MAX_RECORDING_CHUNKS = int((sample_rate / chunk_size) * 15) # Force process after 15s to prevent memory leaks
        
        frames = []
        is_recording = False
        silence_chunks = 0
        
        while is_running_callback():
            try:
                chunk = audio_queue.get(timeout=1)
            except queue.Empty:
                continue
                
            audio_data_np = np.frombuffer(chunk, dtype=np.int16)
            if channels > 1:
                audio_data_np = audio_data_np[::channels]
            
            mono_chunk = audio_data_np.tobytes()
            rms = np.sqrt(np.mean(np.square(audio_data_np.astype(np.float32)))) if len(audio_data_np) > 0 else 0
            
            if rms > SILENCE_THRESHOLD:
                if not is_recording: print("[MIC] Audio detected! Recording...")
                is_recording = True
                silence_chunks = 0
                frames.append(mono_chunk)
                
            elif is_recording:
                silence_chunks += 1
                frames.append(mono_chunk)
                
            # Trigger processing on Silence OR Max Duration reached
            if is_recording and (silence_chunks > MAX_SILENCE_CHUNKS or len(frames) > MAX_RECORDING_CHUNKS):
                is_recording = False 
                audio_bytes = b''.join(frames)
                frames = [] 
                
                def process_audio(raw_audio):
                    try:
                        audio_obj = sr.AudioData(raw_audio, sample_rate, sample_width)
                        text = recognizer.recognize_google(audio_obj)
                        print(f"\n[MIC] Audio Transcribed: '{text}'")
                        asl_glosses = translator.text_to_gloss(text)
                        if asl_glosses:
                            print(f"[BRAIN] Translated to ASL: {asl_glosses}")
                            phrase_queue.put(asl_glosses)
                    except sr.UnknownValueError:
                        print("[MIC] Unrecognized background noise. Ignored.")
                    except sr.RequestError as e:
                        print(f"[MIC] API Network Error: {e}")
                        
                threading.Thread(target=process_audio, args=(audio_bytes,), daemon=True).start()
                    
        stream.stop_stream()
        stream.close()