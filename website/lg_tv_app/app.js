// State variables
let audioCtx = null;
let audioSource = null;
let processorNode = null;
let isStreaming = false;
let websocket = null;
let videoWebsocket = null;

// DOM Elements
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const wsUrlInput = document.getElementById('wsUrlInput');
const video = document.getElementById('broadcastVideo');
const avatarBox = document.getElementById('avatarBox');
const avatarStream = document.getElementById('avatarStream');

// Initialize Web Audio API components
function initAudio() {
    if (audioCtx) return;

    console.log("Initializing AudioContext and Web Audio graph...");
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    audioCtx = new AudioContextClass();

    // Create MediaElementSource from news video
    audioSource = audioCtx.createMediaElementSource(video);

    // Create ScriptProcessorNode (4096 samples, 1 input channel, 1 output channel)
    // 4096 at 48000Hz is ~85ms of audio latency, perfectly suited for real-time streaming
    processorNode = audioCtx.createScriptProcessor(4096, 1, 1);

    // Process audio samples
    processorNode.onaudioprocess = function(event) {
        if (!isStreaming) return;

        const inputData = event.inputBuffer.getChannelData(0);

        // Downsample input audio data to exactly 16000Hz
        const downsampled = downsample(inputData, audioCtx.sampleRate, 16000);

        // Convert the downsampled Float32 samples to 16-bit signed linear PCM (Int16)
        const pcmBuffer = float32ToInt16(downsampled);

        // Stream raw PCM bytes over the WebSocket if connected
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(pcmBuffer);
        }
    };

    // Connect nodes
    // 1. Connect video source to destination (so audio plays on TV speakers)
    audioSource.connect(audioCtx.destination);

    // 2. Connect video source to processor node for analysis/streaming
    audioSource.connect(processorNode);

    // 3. Connect processor node to destination (required for onaudioprocess to trigger)
    processorNode.connect(audioCtx.destination);
    
    console.log("Web Audio graph built successfully. AudioContext sample rate:", audioCtx.sampleRate);
}

/**
 * Downsamples a Float32Array audio buffer using linear interpolation.
 * @param {Float32Array} inputBuffer 
 * @param {number} inputSampleRate 
 * @param {number} outputSampleRate 
 * @returns {Float32Array}
 */
function downsample(inputBuffer, inputSampleRate, outputSampleRate) {
    if (inputSampleRate === outputSampleRate) {
        return inputBuffer;
    }
    if (inputSampleRate < outputSampleRate) {
        console.warn("Input sample rate is lower than target output sample rate. Returning original buffer.");
        return inputBuffer;
    }

    const sampleRateRatio = inputSampleRate / outputSampleRate;
    const newLength = Math.round(inputBuffer.length / sampleRateRatio);
    const result = new Float32Array(newLength);

    for (let i = 0; i < newLength; i++) {
        const index = i * sampleRateRatio;
        const left = Math.floor(index);
        const right = Math.ceil(index);
        const weight = index - left;

        const leftVal = left < inputBuffer.length ? inputBuffer[left] : 0;
        const rightVal = right < inputBuffer.length ? inputBuffer[right] : 0;

        result[i] = leftVal + weight * (rightVal - leftVal);
    }
    return result;
}

/**
 * Converts a Float32Array of audio samples to a 16-bit signed linear PCM ArrayBuffer.
 * @param {Float32Array} float32Array 
 * @returns {ArrayBuffer}
 */
function float32ToInt16(float32Array) {
    const buffer = new ArrayBuffer(float32Array.length * 2); // 2 bytes per 16-bit sample
    const view = new DataView(buffer);

    for (let i = 0; i < float32Array.length; i++) {
        // Clamp values to [-1.0, 1.0] range to prevent clipping/overflows
        const s = Math.max(-1.0, Math.min(1.0, float32Array[i]));
        // Scale to 16-bit signed integer range: [-32768, 32767]
        const val = s < 0 ? s * 0x8000 : s * 0x7FFF;
        // Write Int16 (little-endian is standard for web PCM audio transmission)
        view.setInt16(i * 2, Math.round(val), true);
    }
    return buffer;
}

// UI Badge updates
function updateConnectionStatus(state) {
    const wsBadge = document.getElementById('wsBadge');
    const badgeText = wsBadge.querySelector('.badge-text');

    wsBadge.className = 'badge'; // reset classes

    if (state === 'disconnected') {
        wsBadge.classList.add('disconnected');
        badgeText.textContent = 'Disconnected';
    } else if (state === 'connecting') {
        wsBadge.classList.add('connecting');
        badgeText.textContent = 'Connecting';
    } else if (state === 'connected') {
        wsBadge.classList.add('connected');
        badgeText.textContent = 'Connected';
    }
}

function updateAudioStatus(state) {
    const audioBadge = document.getElementById('audioBadge');
    const badgeText = audioBadge.querySelector('.badge-text');

    audioBadge.className = 'badge'; // reset classes

    if (state === 'idle') {
        audioBadge.classList.add('idle');
        badgeText.textContent = 'Idle';
    } else if (state === 'streaming') {
        audioBadge.classList.add('streaming');
        badgeText.textContent = 'Active';
    }
}

// Start Broadcast / Stream handler
function startBroadcast() {
    const wsUrl = wsUrlInput.value.trim() || 'ws://localhost:8766';
    
    // Disable start button, enable stop button
    startBtn.disabled = true;
    stopBtn.disabled = false;

    // Initialize & resume audio context inside user event to bypass browser security policies
    try {
        initAudio();
        if (audioCtx && audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
    } catch (e) {
        console.error("Failed to initialize or resume AudioContext:", e);
        stopBroadcast();
        return;
    }

    // Set streaming active state
    isStreaming = true;

    // Start video playback
    video.play().then(() => {
        if (playbackSpeed) {
            video.playbackRate = parseFloat(playbackSpeed.value);
        }
    }).catch(err => {
        console.error("Video playback failed:", err);
        console.log("Starting fallback audio oscillator...");
        try {
            const osc = audioCtx.createOscillator();
            osc.frequency.setValueAtTime(440, audioCtx.currentTime);
            osc.connect(processorNode);
            osc.start();
            window.fallbackOsc = osc;
        } catch (e) {
            console.error("Failed to start fallback oscillator:", e);
        }
    });

    // Update WebSocket connection state to connecting
    updateConnectionStatus('connecting');

    // Close any existing socket just in case
    if (websocket) {
        try {
            websocket.close();
        } catch (e) {}
    }
    if (videoWebsocket) {
        try {
            videoWebsocket.close();
        } catch (e) {}
    }

    console.log("Connecting to Audio WebSocket server:", wsUrl);
    websocket = new WebSocket(wsUrl);
    websocket.binaryType = 'arraybuffer';
    
    // Connect to Video WebSocket
    let videoWsUrl = 'ws://localhost:8765';
    try {
        const urlObj = new URL(wsUrl);
        videoWsUrl = `ws://${urlObj.hostname}:8765`;
    } catch (e) {}
    
    console.log("Connecting to Video WebSocket server:", videoWsUrl);
    videoWebsocket = new WebSocket(videoWsUrl);
    videoWebsocket.onmessage = function(event) {
        if (avatarStream && event.data) {
            avatarStream.src = "data:image/jpeg;base64," + event.data;
        }
    };

    websocket.onopen = function() {
        console.log("WebSocket connection established.");
        updateConnectionStatus('connected');
        updateAudioStatus('streaming');
        avatarBox.classList.add('streaming');
    };

    websocket.onclose = function(e) {
        console.log("WebSocket connection closed.", e);
        // Cleanly stop the broadcast if the connection closed
        stopBroadcast();
    };

    websocket.onerror = function(err) {
        console.error("WebSocket connection error:", err);
        // Cleanly stop the broadcast on connection errors
        stopBroadcast();
    };
}

// Stop Broadcast handler
function stopBroadcast() {
    console.log("Stopping broadcast and cleaning up...");
    isStreaming = false;

    // Pause video
    video.pause();

    // Stop fallback oscillator if active
    if (window.fallbackOsc) {
        try {
            window.fallbackOsc.stop();
        } catch (e) {}
        window.fallbackOsc = null;
    }

    // Cleanly close WebSocket and remove event listeners to avoid self-triggering stopBroadcast
    if (websocket) {
        websocket.onopen = null;
        websocket.onclose = null;
        websocket.onerror = null;
        try {
            websocket.close();
        } catch (e) {}
        websocket = null;
    }
    if (videoWebsocket) {
        videoWebsocket.onmessage = null;
        try {
            videoWebsocket.close();
        } catch (e) {}
        videoWebsocket = null;
    }

    // Reset UI Badges and Avatar animation classes
    updateConnectionStatus('disconnected');
    updateAudioStatus('idle');
    avatarBox.classList.remove('streaming');

    // Reset button states
    startBtn.disabled = false;
    stopBtn.disabled = true;
}

// Event Listeners
startBtn.addEventListener('click', startBroadcast);
stopBtn.addEventListener('click', stopBroadcast);
video.addEventListener('ended', stopBroadcast);

console.log("Signify TV App initialized. Ready to broadcast.");

// --- Playback Speed Control ---
const playbackSpeed = document.getElementById('playbackSpeed');
if (playbackSpeed) {
    playbackSpeed.addEventListener('change', (e) => {
        video.playbackRate = parseFloat(e.target.value);
    });
    // Set initial
    video.playbackRate = parseFloat(playbackSpeed.value);
}

// --- Avatar Box Drag Logic ---
const avatarDragHandle = document.getElementById('avatarDragHandle');
let isDragging = false;
let initialX;
let initialY;

if (avatarDragHandle) {
    avatarDragHandle.addEventListener('mousedown', dragStart);
    document.addEventListener('mouseup', dragEnd);
    document.addEventListener('mousemove', drag);
}

function dragStart(e) {
    if (e.target === avatarDragHandle || avatarDragHandle.contains(e.target)) {
        isDragging = true;
        
        const rect = avatarBox.getBoundingClientRect();
        
        if (avatarBox.style.left === '') {
            avatarBox.style.left = rect.left + 'px';
            avatarBox.style.top = rect.top + 'px';
        }
        
        initialX = e.clientX - rect.left;
        initialY = e.clientY - rect.top;
    }
}

function dragEnd(e) {
    isDragging = false;
}

function drag(e) {
    if (isDragging) {
        e.preventDefault();
        
        // Remove bottom/right so they don't fight with left/top
        avatarBox.style.bottom = 'auto';
        avatarBox.style.right = 'auto';
        avatarBox.style.transform = 'none'; // clear any existing transforms
        
        const currentX = e.clientX - initialX;
        const currentY = e.clientY - initialY;
        
        avatarBox.style.left = `${currentX}px`;
        avatarBox.style.top = `${currentY}px`;
    }
}
