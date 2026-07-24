chrome.runtime.onMessage.addListener((message) => {
  if (message.target === 'offscreen' && message.type === 'start_capture') {
    startCapture(message.streamId);
  }
});

// Notify the background script that we are ready to receive the streamId
chrome.runtime.sendMessage({ type: 'offscreen_ready' });

let audioCtx = null;
let ws = null;
let stream = null;

async function startCapture(streamId) {
  if (stream) return; // Already capturing

  try {
    stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        mandatory: {
          chromeMediaSource: 'tab',
          chromeMediaSourceId: streamId,
        },
      },
      video: false,
    });

    audioCtx = new AudioContext({ sampleRate: 16000 });
    
    // Ensure the audio context is running (fixes silent audio bugs)
    if (audioCtx.state === 'suspended') {
      await audioCtx.resume();
    }

    const source = audioCtx.createMediaStreamSource(stream);

    // We use a ScriptProcessorNode to capture raw audio data.
    const processor = audioCtx.createScriptProcessor(4096, 1, 1);
    
    ws = new WebSocket('ws://localhost:8766');

    ws.onopen = () => {
      chrome.runtime.sendMessage({ type: 'ws_open' });
    };

    ws.onerror = () => {
      chrome.runtime.sendMessage({ type: 'ws_err' });
    };

    processor.onaudioprocess = (e) => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        const inputData = e.inputBuffer.getChannelData(0);

        // Convert Float32 (-1 to 1) to Int16 (-32768 to 32767)
        const int16Data = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          let s = Math.max(-1, Math.min(1, inputData[i]));
          int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        ws.send(int16Data.buffer);
      }
    };

    // 1. Play the audio naturally to the speakers (Zero delay/glitches!)
    source.connect(audioCtx.destination); 
    
    // 2. Route a copy to the processor for the WebSocket
    source.connect(processor);
    
    // 3. Connect processor to a muted gain node so Chrome still triggers it, but without double-playing
    const silentGain = audioCtx.createGain();
    silentGain.gain.value = 0;
    processor.connect(silentGain);
    silentGain.connect(audioCtx.destination);

    console.log("Audio capture started and streaming to backend.");
  } catch (err) {
    console.error("Failed to start audio capture:", err);
  }
}
