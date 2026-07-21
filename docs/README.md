<p align="center">
  <img src="../gui/assets/logo.png" alt="Signify Logo" width="120"/>
</p>

<h1 align="center">Signify — Real-Time Sign Language Avatar</h1>

<p align="center">
  <b>A low-latency desktop application that captures live audio, translates spoken English into American Sign Language (ASL), and drives a 2D skeleton avatar in real-time.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue?style=flat-square&logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/AWS-S3%20%2B%20EC2-orange?style=flat-square&logo=amazonaws" alt="AWS"/>
  <img src="https://img.shields.io/badge/MediaPipe-Holistic-green?style=flat-square&logo=google" alt="MediaPipe"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License"/>
</p>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [System Architecture](#-system-architecture)
- [End-to-End Pipeline](#-end-to-end-pipeline)
- [How We Achieve Low Latency](#-how-we-achieve-low-latency)
- [Cloud Data Factory (AWS S3 Pipeline)](#-cloud-data-factory--aws-s3-pipeline)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Configuration](#-configuration)
- [Output Modes](#-output-modes)
- [Roadmap](#-roadmap)

---

## 🌐 Overview

Signify is a fully offline-capable desktop overlay that **listens** to system audio (YouTube, Zoom, podcasts — anything playing through your speakers), **transcribes** it to text using Google STT, **translates** the English text into ASL gloss ordering, and **animates** a 2D skeleton avatar — all in real-time.

The animation data (JSON files containing body/face/hand landmark coordinates) is pre-processed on AWS EC2 and served from a public **Amazon S3 bucket**, enabling the client to fetch sign animations at runtime with near-zero overhead.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SIGNIFY CLIENT                              │
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────┐   ┌──────────┐ │
│  │ Audio Capture │──▶│  Transcriber │──▶│Translator│──▶│ Animator  │ │
│  │  (WASAPI /   │   │ (Google STT) │   │(ASL NLP) │   │(Keyframe │ │
│  │   Dual Mic)  │   │              │   │          │   │ + Interp) │ │
│  └──────────────┘   └──────────────┘   └──────────┘   └────┬─────┘ │
│         ▲                                                   │       │
│         │  OR                                               ▼       │
│  ┌──────────────┐                                    ┌──────────┐   │
│  │ Typing Input │───────────────────────────────────▶│ Renderer  │   │
│  │  (Terminal)  │            (bypasses audio)        │(OpenCV /  │   │
│  └──────────────┘                                    │VirtualCam)│   │
│                                                      └─────┬────┘   │
│                                                            │        │
│                                                   ┌────────▼──────┐ │
│                                                   │  WebSocket    │ │
│                                                   │  Streamer     │ │
│                                                   └───────┬───────┘ │
└───────────────────────────────────────────────────────────┼─────────┘
                                                            │
                                                     (WebSockets)
                                                            ▼
                                    ┌─────────────────────────────────────────────────┐
                                    │               LG webOS TV App                   │
                                    │ - Real-Time VAD Audio Streaming (Port 8766)     │
                                    │ - Draggable/Resizable Interpreter Overlay       │
                                    │ - Dynamic Playback Speed Controller             │
                                    └─────────────────────────────────────────────────┘
                                    ▲
                                    │  HTTP GET (on cache miss)
                                    ▼
                    ┌───────────────────────────────┐
                    │   AWS S3 Public Bucket         │
                    │ signify-asl-dictionary-v1      │
                    │  └── dictionary/               │
                    │       ├── hello.json            │
                    │       ├── thank.json            │
                    │       ├── you.json              │
                    │       └── ... (1,000+ words)    │
                    └───────────────────────────────┘
                                    ▲
                                    │  Uploaded by
                                    ▼
                    ┌───────────────────────────────┐
                    │   AWS EC2 Cloud Pipeline       │
                    │  (Ephemeral Data Factory)      │
                    │                                │
                    │  Scrape MP4 → MediaPipe AI     │
                    │  → Extract Landmarks → JSON    │
                    │  → Upload to S3 → Delete local │
                    └───────────────────────────────┘
```

---

## 🔄 End-to-End Pipeline

The runtime pipeline is a **multi-threaded, queue-connected chain** of independent stages. Each stage runs on its own daemon thread and communicates exclusively through `queue.Queue` objects, ensuring full decoupling and zero blocking between stages.

### Stage 1 — Audio Capture (`audio/dual_capture.py`)
- Hooks into **Windows WASAPI loopback** using `pyaudiowpatch` to capture internal system audio (no physical microphone needed).
- Supports **Dual Audio Mode**: captures both the microphone and system loopback simultaneously with a **Voice Lock** mechanism — only one source is processed at a time to prevent crosstalk.
- Uses **RMS-based Voice Activity Detection (VAD)** to detect speech boundaries and chunk audio into discrete segments on silence timeouts.

### Stage 2 — Speech-to-Text (`audio/transcriber.py`)
- Consumes raw audio segments from the speech queue.
- Sends audio to the **Google Web Speech API** (`speech_recognition` library) for transcription.
- Each segment is processed in its own daemon thread to prevent queue backup.

### Stage 3 — English → ASL Translation (`core/translator.py`)
- Applies **ASL gloss ordering** rules using a rule-based NLP engine:
  - **Stop word removal** — Strips English-only grammar words (`a`, `the`, `is`, etc.) that don't exist in ASL.
  - **Time-Topic-Comment reordering** — Moves temporal words (`tomorrow`, `now`, `yesterday`) to the front of the sentence, following ASL syntax.
- Rules are defined in a JSON config (`config/asl_rules.json`) for easy extension.

### Stage 4 — Animation Playback (`core/animator.py`)
- Receives an ordered list of ASL glosses and fetches the corresponding animation JSON for each word.
- **Fetches animation data directly from Amazon S3** via HTTP GET:
  ```
  https://signify-asl-dictionary-v1.s3.amazonaws.com/dictionary/{word}.json
  ```
- Uses an **in-memory LRU cache** (`@lru_cache(maxsize=128)`) so repeated signs never hit the network twice.
- Applies **linear interpolation** between keyframes and **cross-word transition blending** for smooth, natural motion.
- Performs **missing frame imputation** (gap filling) to recover from MediaPipe tracking drops in the source data.
- Plays a looping **idle animation** when no speech is detected, with smooth transitions in and out.

### Stage 5 — Rendering (`output/`)
- Draws the 2D skeleton using a custom **Catmull-Rom spline renderer** with glow effects for a premium organic look (no stick figures).
- Supports three output modes:
  - `opencv` — Local display window (always-on-top).
  - `virtual_cam` — Streams to OBS Virtual Camera for use in Zoom/Teams/Google Meet.
  - `electron` — Headless mode for external UI consumers.
- Broadcasts raw frame data over **WebSockets** (Port 8765) for the LG webOS TV App and other external consumers.

---

## ⚡ How We Achieve Low Latency

Signify is engineered for speed at every layer. Here's how we minimize end-to-end delay from spoken word to animated sign:

### 1. Queue-Decoupled Multi-Threading
Every pipeline stage (capture → transcribe → translate → animate → render) runs on its own thread. Stages communicate through lock-free `queue.Queue` objects with **backpressure** (`maxsize=30` on the frame queue). No stage ever blocks another — the system processes data as fast as each stage can consume it.

### 2. Pre-Computed Animation Data (Zero AI at Runtime)
The heaviest computation — **MediaPipe Holistic AI inference** — is done **entirely offline** on AWS EC2 during the dictionary build phase. At runtime, the client **never runs any AI model**. It simply fetches pre-computed JSON coordinate arrays from S3. This eliminates the ~50-200ms per-frame GPU/CPU cost that real-time AI would impose.

### 3. S3 CDN-Served Dictionary with LRU Cache
Animation JSONs are served from an **Amazon S3 public bucket** with global edge caching. The client uses a **persistent `requests.Session`** with HTTP keep-alive for connection reuse, and wraps all fetches in a **128-entry LRU in-memory cache** (`functools.lru_cache`). After a word is fetched once, every subsequent use is an `O(1)` RAM lookup — zero network cost.

### 4. Compact JSON Payloads
Each animation JSON stores only **30 keyframes** per word (uniformly sampled from the source video), with landmark coordinates **rounded to 3 decimal places** and serialized with **no whitespace** (`separators=(',', ':')`) to minimize payload size. Face data is further optimized by extracting only **essential contour indices** (jaw, lips, eyes) instead of the full 468-point face mesh — a ~10x size reduction.

### 5. Real-Time Frame Interpolation
Between the 30 stored keyframes, the client generates **smooth intermediate frames on-the-fly** using linear interpolation (configurable `interpolation_frames`). This means 30 keyframes can produce 120+ rendered frames, giving buttery-smooth 60 FPS playback from minimal stored data. Cross-word **transition blending** prevents jarring jumps between signs.

### 6. Aggressive Audio Chunking
Audio is chunked into phrases using a **configurable silence timeout** (default: 0.5 seconds) rather than waiting for long pauses. This means the transcriber receives short, frequent segments — reducing the STT latency from seconds to hundreds of milliseconds per phrase.

### 7. Native WASAPI Loopback (Zero Latency Capture)
By capturing audio directly from the **Windows WASAPI loopback device**, we bypass any virtual audio cable or software routing. This is the lowest-latency audio capture method available on Windows — audio is intercepted at the driver level before it even reaches the speakers.

---

## ☁️ Cloud Data Factory — AWS S3 Pipeline

The ASL dictionary is built offline using an **ephemeral EC2 compute pipeline** that processes words in bulk and uploads the results to S3.

### How It Works

```
┌──────────┐    ┌──────────────┐    ┌────────────────┐    ┌──────────┐    ┌──────────┐
│  Word    │───▶│ Web Scraper  │───▶│  MediaPipe AI  │───▶│  JSON    │───▶│ S3       │
│  List    │    │(signasl.org) │    │  (Holistic)    │    │ Builder  │    │ Upload   │
└──────────┘    └──────────────┘    └────────────────┘    └──────────┘    └──────────┘
                                                                              │
                                                                    Local files deleted
```

### Processing Each Word — Step by Step

The pipeline is defined in `aws/cloud_pipeline.py` and processes each word as follows:

1. **Skip Check** — Query S3 with `head_object()` to see if `dictionary/{word}.json` already exists. If it does, skip entirely (idempotent reruns are free).

2. **Video Download** — Scrape [signasl.org](https://www.signasl.org) for the word's demonstration video. The scraper uses rotating User-Agent headers, polite random delays (1.5–4.5s), and automatic retry with 30s backoff on HTTP 429 rate limits.

3. **AI Landmark Extraction** — Open the downloaded MP4 with OpenCV, sample **30 keyframes** uniformly across the video, and run each frame through **MediaPipe Holistic** to extract:
   - **Pose landmarks** (33 points — shoulders, arms, hips)
   - **Left & right hand landmarks** (21 points each — wrist + fingers)
   - **Face contour landmarks** — selectively extracted by index:
     - Jawline (36 indices)
     - Lips (20 indices)
     - Right eye (16 indices)
     - Left eye (16 indices)
   - All coordinates are **anchor-normalized** (relative to chest midpoint) and **scale-normalized** (shoulder width → 0.5 units) to ensure consistency across different signers and camera distances.

4. **JSON Upload** — The processed animation data is serialized to compact JSON and uploaded directly to the S3 bucket at key `dictionary/{word}.json`.

5. **Cleanup** — Both the local MP4 and JSON files are deleted from the EC2 instance to keep disk usage minimal.

### Multi-Threaded Execution

The pipeline uses `concurrent.futures.ThreadPoolExecutor` with **5 worker threads** to process multiple words simultaneously. A `threading.Lock` serializes the actual MediaPipe AI inference (which is not thread-safe due to OpenGL/EGL context restrictions), while download and upload operations run fully in parallel.

```python
# From aws/cloud_pipeline.py
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    executor.map(pipeline.execute_word, WORDS)
```

### Word List Generation

The script `aws/generate_words.py` downloads the English frequency word list (top 50K words by usage), filters for alphabetic words ≥ 3 characters, excludes words already processed, and outputs a batch of up to **10,000 new words** ready for the pipeline.

### S3 Bucket Configuration

| Property | Value |
|----------|-------|
| **Bucket Name** | `signify-asl-dictionary-v1` |
| **Region** | `us-east-1` |
| **Access** | Public read (`s3:GetObject` for `*`) |
| **URL Pattern** | `https://signify-asl-dictionary-v1.s3.amazonaws.com/dictionary/{word}.json` |

The bucket policy (`aws/s3_policy.json`) grants anonymous read access so the Signify client can fetch animation data without any AWS credentials.

---

## 📁 Project Structure

```
Signify/
├── main.py                      # Application entry point — wires all pipeline stages
├── run_dashboard.py             # Launches the GUI dashboard
├── requirements.txt             # Python dependencies (client-side)
│
├── audio/
│   ├── dual_capture.py          # WASAPI loopback + microphone capture with Voice Lock
│   └── transcriber.py           # Google STT transcription worker
│
├── core/
│   ├── animator.py              # Keyframe playback engine with S3 fetch + LRU cache
│   ├── translator.py            # English → ASL gloss NLP translator
│   └── typing_input.py          # Terminal-based text input (alternative to audio)
│
├── output/
│   ├── renderer.py              # OpenCV local window renderer
│   ├── virtual_cam.py           # OBS Virtual Camera output (for Zoom/Teams)
│   ├── headless.py              # Headless renderer for external UI consumers
│   └── streamer.py              # WebSocket server for broadcasting frame data
│
├── utils/
│   ├── drawing.py               # Catmull-Rom spline renderer with glow effects
│   └── logger.py                # Centralized logging
│
├── website/
│   └── lg_tv_app/               # LG webOS TV App Proof-of-Concept
│       ├── index.html           # TV Interface with video and overlay
│       ├── style.css            # Styling for draggable/resizable overlay
│       └── app.js               # WebSockets, VAD Audio logic, and Playback controls
│
├── config/
│   ├── app_settings.json        # Master configuration (input/output/playback/audio)
│   └── asl_rules.json           # ASL translation rules (stop words, time words)
│
├── gui/
│   ├── dashboard.py             # CustomTkinter settings GUI with live text input
│   └── assets/                  # Logo and icons
│
├── aws/
│   ├── cloud_pipeline.py        # EC2 Cloud Data Factory (scrape → AI → S3 upload)
│   ├── generate_words.py        # Word list generator (frequency-based, 10K batch)
│   ├── requirements_ec2.txt     # Minimal EC2 dependencies (headless OpenCV)
│   └── s3_policy.json           # S3 bucket public read policy
│
├── scripts/
│   ├── dictionary_builder.py    # Local dictionary builder (legacy, pre-S3)
│   ├── download_videos.py       # Standalone video downloader
│   └── generate_idle.py         # Generates the idle animation loop
│
└── docs/
    └── README.md                # This file
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Windows 10/11** (required for WASAPI loopback audio capture)
- **OBS Virtual Camera** (optional, only needed for `virtual_cam` output mode)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/Signify.git
cd Signify

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

**Option A — GUI Dashboard:**
```bash
python run_dashboard.py
```
The dashboard lets you configure all settings visually and launch/stop the pipeline with a single click. Includes a live text input field for typing mode.

**Option B — Direct Pipeline:**
```bash
python main.py
```
Runs the pipeline directly using the settings in `config/app_settings.json`. In typing mode, you'll be prompted to type sentences in the terminal.

---

## ⚙️ Configuration

All settings are managed through `config/app_settings.json`:

| Setting | Options | Description |
|---------|---------|-------------|
| `input_mode` | `typing`, `audio_loopback`, `dual_audio` | How Signify receives English text |
| `output_mode` | `opencv`, `virtual_cam`, `electron` | Where the avatar is rendered |
| `playback.speed_ms` | `10` – `100` | Delay between keyframes in ms |
| `playback.transition_frames` | `0` – `20` | Smooth frames between different signs |
| `playback.interpolation_frames` | `0` – `10` | Smooth frames between keyframes within a sign |
| `audio.silence_timeout_sec` | `0.1` – `2.0` | How quickly silence ends a speech segment |
| `audio.silence_threshold_rms` | `100` – `2000` | RMS volume threshold for voice detection |
| `network.enable_websocket` | `true` / `false` | Enable WebSocket broadcasting on port 8765 |
| `display.scale` | `0.1` – `1.0` | Avatar size on screen |

---

## 🖥️ Output Modes

| Mode | Use Case | How It Works |
|------|----------|--------------|
| **Local Display** (`opencv`) | Development & demo | Always-on-top OpenCV window. Press `q` to quit. |
| **Virtual Camera** (`virtual_cam`) | Zoom / Teams / Meet | Streams the avatar as a camera device via OBS Virtual Cam. Select "OBS Virtual Camera" as your webcam in any video call app. |
| **TV App Stream** (`websocket`) | LG webOS TV | Streams raw OpenCV JPEGs (cropped) via Port 8765 and receives VAD-buffered audio via Port 8766 from the Web App. |

---

## 🗺️ Roadmap & History

### Phase 1: Core Engine & Desktop Integrations (Completed)
- [x] Multi-threaded queue-based pipeline architecture
- [x] Windows WASAPI loopback audio capture (system audio)
- [x] Dual microphone + loopback capture with Voice Lock
- [x] Google STT speech-to-text integration
- [x] Rule-based English → ASL gloss translation
- [x] AWS EC2 cloud pipeline for bulk sign processing
- [x] Amazon S3 public dictionary with 1,000+ words
- [x] LRU in-memory animation cache
- [x] Frame interpolation and cross-word transition blending
- [x] Catmull-Rom spline rendering with glow effects
- [x] OBS Virtual Camera output for video calls
- [x] CustomTkinter GUI dashboard

### Phase 2: Web & Smart TV Integrations (Current)
- [x] WebSocket Audio Receiver for remote stream ingestion
- [x] Smart VAD (Voice Activity Detection) Buffering over WebSockets
- [x] LG webOS TV App Proof-of-Concept
- [x] Cropped streaming optimizations for low latency JPEGs
- [x] Draggable/Resizable TV Overlay
- [x] Real-time TV playback speed controls (0.25x - 1.0x)

### Future Roadmap
- [ ] Scale S3 dictionary to 10,000+ words
- [ ] Deepgram Streaming WebSockets for instant STT (millisecond latency)
- [ ] 3D VRM avatar rendering (Godot / Three.js)
- [ ] Fingerspelling fallback for out-of-dictionary words

---

<p align="center">
  <i>Built with ❤️ for the Deaf and Hard-of-Hearing community.</i>
</p>
