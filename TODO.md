# Signify - Action Plan

## 🏗️ Core Architecture Upgrades
- [ ] **Math:** Calculate Quaternions in Python (`SciPy`) instead of raw XYZ points.
- [ ] **Render:** Godot 4 Native (transparent overlay, no browser overhead).
- [ ] **Audio:** Windows WASAPI Loopback (`pyaudiowpatch`) for internal PC audio.

## 🚀 Phase 1: Zero-Latency Data Pipeline
- [ ] Update `dictionary_builder.py` to calculate and save VRM Quaternions.
- [ ] Minimize JSON payloads (3-4 decimal precision max).
- [ ] Shard JSON folders (e.g., `a/ap/apple.json`) to prevent OS-level read bottlenecks.
- [ ] Implement `@lru_cache` in `player.py` to eliminate repeated hard-drive reads.
- [ ] Warm-up cache on boot (auto-load top 100 common ASL words into RAM).

## 🎙️ Phase 2: Native Audio & Local NLP
- [ ] Integrate WASAPI loopback capture with memory-safe Voice Activity Detection (VAD).
- [ ] Process internal audio via STT (Google Speech API or local Whisper).
- [ ] Expand `asl_rules.json` for instantaneous `O(1)` local text-to-gloss NLP.

## 🔄 Phase 3: JIT (Just-In-Time) Fetching
- [ ] Detect missing ASL vocabulary seamlessly during live translation.
- [ ] Spin up a background thread to: Download MP4 → Build JSON → Push to Queue.
- [ ] Maintain smooth Godot idle animation while JIT processing happens.

## 🎮 Phase 4: Godot 4 Native Integration
- [ ] Initialize Godot 4 project + `godot-vrm` plugin.
- [ ] Configure transparent, click-through, always-on-top window bounds.
- [ ] Hook up GDScript WebSocket client to read Python Quaternion stream.
- [ ] Apply smooth `Quaternion.slerp()` to the VRM bone skeleton.
