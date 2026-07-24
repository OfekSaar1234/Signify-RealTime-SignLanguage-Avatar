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
      className="fixed bottom-4 right-4 z-[999999] bg-black rounded-xl shadow-2xl border border-gray-800 flex flex-col" 
      style={{ width: '250px', height: '350px', cursor: 'grab', resize: 'both', overflow: 'hidden', minWidth: '150px', minHeight: '200px', maxWidth: '800px', maxHeight: '800px' }}
      whileTap={{ cursor: 'grabbing' }}
    >
      <div className="bg-gray-900 px-3 py-2 flex items-center justify-between select-none">
        <span className="text-white text-sm font-semibold flex items-center gap-2">
          Signify {isCapturing && <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />}
        </span>
        <div className="absolute top-2 right-2 bg-red-500/80 text-white text-xs px-2 py-1 rounded cursor-pointer pointer-events-auto" onClick={() => setIsVisible(false)}>
          Close
        </div>

        {!isCapturing && (
          <div className="absolute bottom-2 left-2 right-2 bg-yellow-500/90 text-white text-xs px-2 py-2 rounded text-center font-bold">
            Click extension icon to start hearing!
          </div>
        )}
      </div>
      <div className="w-full h-full relative bg-black flex items-center justify-center pointer-events-none">
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
document.body.appendChild(container);

const root = createRoot(container);
root.render(
  <React.StrictMode>
    <ContentApp />
  </React.StrictMode>
);
