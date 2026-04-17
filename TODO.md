# Signify Project - Action Plan & To-Do List

## 📝 Architecture Decisions (Max Performance Path)

### 1. Frontend & Rendering Engine: Godot 4 + VRM
- **Why:** Godot runs natively (C++) and avoids the massive RAM/CPU overhead of browser-based solutions like Electron + Three.js. It handles OS-level transparent windows natively and highly efficiently.
- **Standard:** We are using the **VRM Standard** for avatars. This ensures a uniform bone hierarchy, preventing the need for manual dictionary mapping, and natively supports unified semantic facial expressions.

### 2. Kinematic Retargeting (Python Server-Side Math)
- **Why:** Sending raw 3D XYZ coordinates to the frontend requires heavy calculations (Inverse Kinematics) on the rendering side, causing latency. JavaScript solutions (like Kalidokit) are deprecated and lock finger movements, destroying ASL signs.
- **Solution:** The Python backend will convert MediaPipe spatial points into **Quaternions (Angles)** using libraries like `SciPy` (Cross Products) *before* saving them to the JSON/sending them over WebSockets. Godot will simply receive these exact angles and apply them instantly to the VRM skeleton with zero math required on the frontend.

### 3. Audio Capture: Windows Internal Loopback
- **Decision:** Capture computer internal audio (YouTube, Zoom, etc.) natively, without requiring external physical microphones or manual OS configurations.
- **Solution:** Use Python with `pyaudiowpatch` to hook directly into the Windows WASAPI Loopback device.

---

## 🛠️ Phase 1: High-Performance Local Database (Zero Latency)
*Goal: Build an ultra-fast local "database" of ASL movement JSONs that uses minimal disk reads and consumes almost zero latency.*

- [ ] **Python Backend Kinematics (Crucial!):** Update `dictionary_builder.py`. Instead of saving raw `x,y,z` points, implement a math function (using `SciPy`) to calculate the exact joint angles (**Quaternions**) required for a VRM skeleton.
- [ ] **Minimal JSON Footprint:** Ensure the generated JSON files contain *only* the calculated Quaternions and truncate decimal precision (3-4 digits max) to drastically reduce file size and WebSocket transmission payloads.
- [ ] **Refactor Data Factory Paths (Sharding):** Update `dictionary_builder.py` so that instead of saving to a flat `assets/jsons/` directory, it calculates an alphabetical sub-path (e.g., `assets/jsons/a/ap/apple.json`). This prevents OS-level directory scanning bottlenecks when scaling up to 40,000 files.
- [ ] **Write a Data Migration Script:** Create a quick, one-time Python script to read all currently existing flat JSON files and move them into the new sharded folder structure automatically.
- [ ] **In-Memory LRU Cache:** In `main.py`, isolate the file-reading function and wrap it with `@lru_cache(maxsize=1000)` from `functools`. This ensures that a word loaded once never hits the hard drive again.
- [ ] **Pre-load Common Vocabulary (Cache Warming):** Add a boot-up sequence in `main.py` that automatically triggers the read function for the top 100 most common English words. This warms up the RAM cache so the initial user experience has zero read latency.

## 🎙️ Phase 2: Internal PC Audio Capture (Windows WASAPI)
*Goal: Listen to the computer's internal audio (YouTube, Zoom) natively without needing a physical microphone.*

- [ ] **Install WASAPI Package:** Run `pip install pyaudiowpatch` to replace standard `pyaudio`.
- [ ] **Implement WASAPI Loopback:** Rewrite `live_audio_stream()` in `main.py` to explicitly locate and target the Windows WASAPI Loopback default output device.
- [ ] **Voice Activity Detection (VAD):** Ensure the listener accurately detects silence in the computer audio stream to know when a sentence is finished.
- [ ] **STT Processing:** Send the loopback audio buffer to Google Web Speech API (or a fast local model like Whisper later on) to retrieve English text.

## 🧠 Phase 3: Fast Local NLP Translation (No Cloud API Delays)
*Goal: Keep translation local and instantaneous for maximum performance.*

- [ ] **Enhance Local Ruleset:** Expand `asl_rules.json` to handle more complex time-words, stop-words, and common idiom replacements.
- [ ] **Refine `asl_translator.py`:** Optimize the regex parsing to maintain `O(1)` complexity while performing smarter sentence restructuring. *(Note: AI translation like Gemini Pro is paused to prioritize 0-latency performance).*

## 🔄 Phase 4: Just-In-Time (JIT) Data Fetching
*Goal: Handle dictionary misses without crashing the system or freezing the avatar.*

- [ ] **Missing Word Detection:** Implement logic in `main.py` to detect when a translated word lacks a corresponding JSON file in `assets/jsons`.
- [ ] **JIT Pipeline:** Open a background thread to run `download_videos.py` (fetch MP4) immediately followed by `dictionary_builder.py` (extract landmarks to JSON).
- [ ] **Smooth Queue Management:** Ensure the main thread continues running smoothly (e.g., playing an "idle" animation) while waiting, and pushes the new JSON to the queue as soon as it's ready.

## 🎮 Phase 5: Godot 4 & VRM Native Integration (Frontend)
*Goal: Replace OpenCV/Unity with a high-performance Godot 4 native window acting as the transparent overlay.*

- [ ] **Godot Project Setup:** Initialize a Godot 4 project and install the `godot-vrm` addon.
- [ ] **Transparent OS Window:** Configure the Godot `DisplayServer` settings: `transparent_bg = true`, `borderless = true`, and `always_on_top = true`. Handle mouse passthrough (click-through) so the user can interact with apps behind the avatar.
- [ ] **WebSocket Client:** Create a GDScript `WebSocketPeer` script to connect to `main.py` (`ws://localhost:8765`).
- [ ] **Quaternion Application:** Write a script to take the incoming WebSocket JSON (Quaternions) and apply them directly to the VRM model's bones.
- [ ] **Spherical Linear Interpolation (SLERP):** Utilize Godot's built-in `Quaternion.slerp()` inside the `_process(delta)` loop. This will smoothly interpolate between the received JSON keyframes and eliminate any jitter.
