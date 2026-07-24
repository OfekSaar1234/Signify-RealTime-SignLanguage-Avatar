let capturingTabId: number | null = null;
let pendingStreamId: string | null = null;

async function setupOffscreenDocument(path: string) {
  const hasOffscreen = await chrome.offscreen.hasDocument();
  if (hasOffscreen) {
    await chrome.offscreen.closeDocument();
  }

  try {
    await chrome.offscreen.createDocument({
      url: path,
      reasons: [chrome.offscreen.Reason.USER_MEDIA, chrome.offscreen.Reason.AUDIO_PLAYBACK],
      justification: 'Capture tab audio for sign language translation',
    });
    chrome.action.setBadgeText({ text: "CRT" });
  } catch (e) {
    chrome.action.setBadgeText({ text: "EX" });
    throw e;
  }
}

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'offscreen_ready' && pendingStreamId) {
    chrome.action.setBadgeText({ text: "RDY" });
    chrome.runtime.sendMessage({
      target: 'offscreen',
      type: 'start_capture',
      streamId: pendingStreamId
    });
    pendingStreamId = null;
  } else if (msg.type === 'ws_open') {
    chrome.action.setBadgeText({ text: "WS" });
    if (capturingTabId) {
      chrome.tabs.sendMessage(capturingTabId, { action: 'started_capture' }).catch(() => {});
    }
  } else if (msg.type === 'ws_err') {
    chrome.action.setBadgeText({ text: "WSX" });
  }
});

chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.id) return;

  chrome.tabs.sendMessage(tab.id, { action: 'toggle_avatar' }).catch(() => {});

  if (capturingTabId !== tab.id) {
    try {
      chrome.action.setBadgeText({ text: "ID" });
      const streamId = await new Promise<string>((resolve, reject) => {
        chrome.tabCapture.getMediaStreamId({ targetTabId: tab.id }, (id) => {
          if (chrome.runtime.lastError) reject(chrome.runtime.lastError);
          else if (id) resolve(id);
          else reject(new Error("No stream ID returned"));
        });
      });

      pendingStreamId = streamId;
      await setupOffscreenDocument('offscreen.html');
      
      capturingTabId = tab.id;
    } catch (err) {
      chrome.action.setBadgeText({ text: "ERR" });
      console.error("Failed to capture tab audio:", err);
    }
  }
});
