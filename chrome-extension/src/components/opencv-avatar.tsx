import React, { useState, useEffect } from 'react';

interface OpenCVAvatarProps {
  className?: string;
  wsUrl?: string;
}

export function OpenCVAvatar({ className = '', wsUrl = 'ws://localhost:8765' }: OpenCVAvatarProps) {
  const [frameSrc, setFrameSrc] = useState<string | null>(null);

  useEffect(() => {
    let ws: WebSocket;
    let reconnectTimeout: number;

    const connect = () => {
      try {
        ws = new WebSocket(wsUrl);
        
        ws.onmessage = (event) => {
          if (event.data) {
            setFrameSrc("data:image/jpeg;base64," + event.data);
          }
        };

        ws.onclose = () => {
          console.log("Avatar WebSocket closed. Reconnecting...");
          reconnectTimeout = setTimeout(connect, 3000);
        };
      } catch (err) {
        console.error("Avatar WebSocket connection error:", err);
        reconnectTimeout = setTimeout(connect, 3000);
      }
    };

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      if (ws) {
        ws.onclose = null;
        ws.close();
      }
    };
  }, [wsUrl]);

  return (
    <div className={`relative bg-black flex items-center justify-center overflow-hidden ${className}`}>
      {frameSrc ? (
        <img 
          src={frameSrc} 
          alt="Signify Avatar Stream" 
          className="w-full h-full object-contain"
        />
      ) : (
        <div className="text-green-500 font-mono text-sm">Waiting for connection...</div>
      )}
    </div>
  );
}
