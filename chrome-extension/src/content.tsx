import React, { useState, useEffect, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import { motion } from 'framer-motion';
import { OpenCVAvatar } from './components/opencv-avatar';
import './index.css';

function ContentApp() {
  const [isVisible, setIsVisible] = useState(true);
  const [isCapturing, setIsCapturing] = useState(false);
  const dragRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const listener = (msg: any) => {
      if (msg.action === 'toggle_avatar') {
        setIsVisible(true);
      } else if (msg.action === 'started_capture') {
        setIsCapturing(true);
      }
    };
    chrome.runtime.onMessage.addListener(listener);
    return () => chrome.runtime.onMessage.removeListener(listener);
  }, []);

  if (!isVisible) return null;

  return (
    <motion.div 
      drag
      dragConstraints={{ left: -window.innerWidth + 250, right: 0, top: -window.innerHeight + 350, bottom: 0 }}
      dragElastic={0.1}
      dragMomentum={false}
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      className="fixed bottom-4 right-4 z-[999999] rounded-xl shadow-2xl overflow-hidden" 
      style={{ 
        width: '250px', height: '350px', cursor: 'grab', resize: 'both', 
        minWidth: '150px', minHeight: '200px', maxWidth: '800px', maxHeight: '800px',
        backgroundColor: '#000000', boxSizing: 'border-box', border: '1px solid #1f2937',
        pointerEvents: 'auto'
      }}
      whileTap={{ cursor: 'grabbing' }}
    >
      {!isCapturing && (
        <div className="absolute top-2 left-2 right-2 bg-yellow-500/90 text-white text-xs px-2 py-2 rounded text-center font-bold z-50 pointer-events-none">
          Click extension icon to start hearing!
        </div>
      )}
      <div className="w-full h-full relative flex items-center justify-center pointer-events-none" style={{ backgroundColor: '#000000' }}>
        <OpenCVAvatar className="w-full h-full relative" />
      </div>
    </motion.div>
  );
}

// Inject into the page
const container = document.createElement('div');
container.id = 'signify-extension-root';
// Prevent layout shift on host pages (like CBS)
container.style.position = 'fixed';
container.style.top = '0';
container.style.left = '0';
container.style.width = '0';
container.style.height = '0';
container.style.zIndex = '999999';
container.style.overflow = 'visible';
container.style.pointerEvents = 'none'; // Prevent container from blocking
document.body.appendChild(container);

// Handle Fullscreen API (e.g. YouTube/CBS fullscreen buttons)
document.addEventListener('fullscreenchange', () => {
  if (document.fullscreenElement) {
    document.fullscreenElement.appendChild(container);
  } else {
    document.body.appendChild(container);
  }
});

const root = createRoot(container);
root.render(
  <React.StrictMode>
    <ContentApp />
  </React.StrictMode>
);
