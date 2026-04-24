# Signify – AI Real-Time ASL Avatar Overlay

A blazing-fast desktop overlay that captures system audio, translates it into American Sign Language (ASL), and drives a 3D VRM avatar in real-time.

## 🚀 Core Architecture
- **Frontend (Godot 4 + VRM):** High-performance, native transparent click-through window. Eliminates the overhead of browser-based rendering.
- **Backend (Python):** Uses `pyaudiowpatch` for Windows WASAPI loopback (internal audio capture) and MediaPipe/SciPy for server-side Kinematic Retargeting (Quaternions).
- **Data Pipeline:** Zero-latency Local LRU Cache → WebSocket Stream → Godot SLERP Interpolation.

## 🗺️ Roadmap & Phases
1. **High-Performance Database:** Convert MediaPipe spatial points to Quaternions, optimize JSON payloads, and implement in-memory LRU caching.
2. **Internal Audio Capture:** Hook into Windows WASAPI for physical-mic-free system audio listening (YouTube, Zoom) with Voice Activity Detection (VAD) and STT.
3. **Fast Local NLP Translation:** Convert STT English to ASL glosses instantly using a local `O(1)` ruleset.
4. **Just-In-Time (JIT) Fetching:** Auto-scrape, build, and cache missing sign JSONs on the fly without dropping frames.
5. **Godot Native Integration:** Render the VRM avatar in an always-on-top window driven by live WebSocket Quaternion data.
