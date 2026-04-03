# Signify Project - Action Plan & To-Do List

## 📝 Current State & Architecture Options (Review with Ori)

### 1. Current State of `main.py`
- **Audio Capture:** Uses `sr.Microphone()`. It currently listens to the **external physical microphone** (room noise, your voice), *not* the internal computer audio.
- **Speech-to-Text (STT):** Uses `recognize_google()`. This sends audio to Google's free Web Speech API, returning English text.
- **Translation Brain:** Passes the English text to `asl_translator.py`, which uses a local JSON ruleset to rearrange time words and replace words. It is lightning-fast but translates word-for-word (does not fully understand ASL grammar).

### 2. Audio Capture Options (Internal PC Audio)
*How to capture YouTube/Zoom audio from the computer itself.*
- **Option A: No Code Changes (Hardware/OS Route)**
  - **How it works:** Enable "Stereo Mix" in Windows Sound Settings, or install a free Virtual Audio Cable (like VB-Cable). Set it as your default microphone.
  - **Pros:** Zero code changes required in `main.py`. The existing `sr.Microphone()` will just pick up the computer's audio automatically.
  - **Cons:** Requires one-time manual setup on the host computer.
- **Option B: Code Changes (Software Route)**
  - **How it works:** Replace `pyaudio` with `pyaudiowpatch` in Python, and rewrite the capture logic to explicitly target the Windows WASAPI Loopback device.
  - **Pros:** Works out-of-the-box for any user without them needing to install Virtual Audio Cables or change Windows settings.
  - **Cons:** Requires rewriting the audio listening thread in `main.py`.

### 3. NLP "Brain" Options (Translation to ASL)
*How to convert English text/audio into ASL Gloss.*
- **Option A: Current Setup (Local Python Brain)**
  - **Flow:** Free Google STT -> Local `asl_translator.py`.
  - **Pros:** 100% Free, unlimited, and instantaneous (zero delay).
  - **Cons:** "Dumb" translation. Translates word-for-word and misses complex ASL grammatical structures.
- **Option B: Hybrid Setup (Gemini Pro for Text)** *(Recommended for Phase 3)*
  - **Flow:** Free Google STT -> Send English Text to Gemini Pro API -> Receive ASL Gloss.
  - **Pros:** Extremely accurate, understands context and ASL grammar (Time-Topic-Comment).
  - **Cons:** Network latency (1-3 seconds to get a response). Free-tier limits (e.g., 15 requests/min) might cause blocks if the video is fast-paced.
- **Option C: All-in-One AI (Gemini 1.5 Pro for Audio)**
  - **Flow:** Capture Raw PC Audio -> Send directly to Gemini 1.5 Pro -> Receive ASL Gloss.
  - **Pros:** Skips the STT middle-man. Gemini understands vocal tone, emphasis, and context perfectly.
  - **Cons:** Uploading audio is slow. Highest latency for real-time translation. Audio tokens eat into free-tier limits extremely fast.

---

## 🛠️ Phase 1: Foundation (Stability & Performance)

- [ ] **Refactor Data Factory Paths (Sharding):** Update `dictionary_builder.py` so that instead of saving to a flat `assets/jsons/` directory, it calculates an alphabetical sub-path (e.g., `assets/jsons/a/ap/apple.json`). This prevents OS-level directory scanning bottlenecks when scaling up to 40,000 files.
- [ ] **Write a Data Migration Script:** Create a quick, one-time Python script to read all currently existing flat JSON files and move them into the new sharded folder structure automatically.
- [ ] **Update Avatar Controller Paths:** Modify the disk-reading logic in `main.py` so that when the system looks for a word, it dynamically reconstructs the exact sharded path to locate the file instantly.
- [ ] **Implement LRU Cache for Word Loading:** Isolate the specific function in `main.py` that reads the JSON file from the SSD. Wrap it using `@lru_cache(maxsize=500)` from the `functools` library to prevent repeated disk reads for the same words and eliminate micro-stutters.
- [ ] **JSON Optimization & Minification:** Write a short side-script to process all JSON files. Truncate the decimal precision of the coordinates (keep only 3-4 digits instead of 15) to drastically reduce the file footprint and speed up memory/network loading.
- [ ] **Pre-load Common Vocabulary (Cache Warming):** Add a boot-up sequence in `main.py` that automatically triggers the read function for the top 100 most common English words. This warms up the RAM cache so the initial user experience has zero read latency.



## 🎙️ Phase 2: Real-Time Speech-to-Text (Live STT) Integration
*Goal: Replace manual typing with a microphone that detects when a sentence ends. (Fully autonomous).*
- [X] **Install STT Dependencies:** Run `pip install SpeechRecognition pyaudio`.
- [X] **Integrate Google STT (Producer Thread):** Create a new `live_audio_stream` background thread to replace `live_typing_stream` in `main.py`.
- [X] **Voice Activity Detection (VAD):** Configure the system to wait for silence (end of sentence) before sending the audio buffer to the Google Web Speech API.
- [X] **Queue Integration:** Verify the returned text successfully passes to `asl_translator.py` and the resulting ASL glosses are pushed into the `phrase_queue`.



## 🧠 Phase 3: Upgrading the "Brain" to Gemini Pro (NLP)
*Goal: Replace hardcoded syntax rules with an advanced language model for accurate ASL Gloss translation.*
- [ ] **Gemini Pro API Integration:** Create a new function in `asl_translator.py` to send the full transcribed sentence to the Gemini Pro API.
- [ ] **System Prompt Engineering:** Use the prompt: *"You are an ASL translator. Convert the following English sentence to ASL Gloss strictly using Time-Topic-Comment structure. Return ONLY a Python list of strings"*.
- [ ] **Security & Tier Limits:** Securely integrate the API key and manage requests to stay within the student tier limits.



## 🔄 Phase 4: Just-In-Time (JIT) Data Generation
*Goal: Handle dictionary misses without crashing the system or freezing the avatar.*
- [ ] **Missing Word Detection:** Implement logic in `main.py` to detect when a translated word lacks a corresponding JSON file in `assets/jsons`.
- [ ] **JIT Pipeline:** Open a background thread to run `download_videos.py` (fetch MP4) immediately followed by `dictionary_builder.py` (extract landmarks to JSON).
- [ ] **Smooth Queue Management:** Ensure the main thread continues running smoothly (e.g., playing an "idle" animation) while waiting, and pushes the new JSON to the queue as soon as it's ready.



## 🎞️ Phase 5: Mathematical Motion Smoothing (Interpolation)
*Goal: Create fluid, natural movements and prevent robotic or jittery transitions.*
- [ ] **Refine Linear Interpolation (LERP):** Enhance the transition calculations inside the main loop of `main.py` (between final coordinates of Word A and initial coordinates of Word B).
- [ ] **Tune Transition Frames:** Experiment with generating 5-10 calculated frames so the avatar moves its hands smoothly between positions without looking robotic or jittery.



## 🎮 Phase 6: Unity 3D Integration (Future Step)
*Goal: Transition from the 2D OpenCV development environment to the final production build.*
- [ ] **Await Lecturer Feedback:** Continue putting the Unity build aside until receiving an answer regarding best practices for integrating JSON data with Inverse Kinematics (IK).
- [ ] **Stick to 2D Debugging:** Use the 2D OpenCV skeleton drawer for now to ensure the core logic, WebSockets, and data minification are rock-solid.
- [ ] **Final C# Routing:** Once approved, route the WebSocket server to transmit the lightweight JSON coordinates to the C# receiver script in Unity.
