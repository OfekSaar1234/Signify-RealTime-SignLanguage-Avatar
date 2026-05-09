import React, { useEffect, useRef, useState } from 'react';

const App: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // Settings for drawing
  const colors = {
    f: '#00FFFF', // Face (Cyan)
    p: '#FF00FF', // Pose (Magenta)
    l: '#00FF00', // Left Hand (Green)
    r: '#00FF00', // Right Hand (Green)
  };

  useEffect(() => {
    // Connect to Python WebSocket
    const connectWs = () => {
      const ws = new WebSocket('ws://localhost:8765');
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        console.log('Connected to Signify Pipeline');
      };

      ws.onclose = () => {
        setIsConnected(false);
        setTimeout(connectWs, 1000); // Reconnect loop
      };

      ws.onmessage = (event) => {
        const frameData = JSON.parse(event.data);
        drawSkeleton(frameData);
      };
    };

    connectWs();
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const drawSkeleton = (frameData: any) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const width = canvas.width;
    const height = canvas.height;
    const scale = 0.35;
    const offset = 0.5;

    // Helper to draw a single point with glow
    const drawPoint = (x: number, y: number, color: string) => {
      const cx = (x * scale + offset) * width;
      const cy = (y * scale + offset) * height;

      ctx.beginPath();
      ctx.arc(cx, cy, 4, 0, 2 * Math.PI);
      ctx.fillStyle = color;
      
      // Glow effect
      ctx.shadowBlur = 15;
      ctx.shadowColor = color;
      ctx.fill();
      
      // Reset shadow for performance on non-glowing parts if needed, but we keep it here
    };

    // Helper to draw line
    const drawLine = (pt1: any, pt2: any, color: string) => {
      if (!pt1 || !pt2) return;
      
      const x1 = (pt1[0] * scale + offset) * width;
      const y1 = (pt1[1] * scale + offset) * height;
      const x2 = (pt2[0] * scale + offset) * width;
      const y2 = (pt2[1] * scale + offset) * height;

      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.lineCap = 'round';
      
      // Glow effect for lines
      ctx.shadowBlur = 10;
      ctx.shadowColor = color;
      
      ctx.stroke();
    };

    // Pose connections (Simplified mapping based on mediapipe standard)
    const poseConnections = [
      [11, 12], [11, 13], [13, 15], [12, 14], [14, 16], // Arms
      [11, 23], [12, 24], [23, 24], // Torso
    ];

    // Draw Pose
    if (frameData.p) {
      // Points
      frameData.p.forEach((pt: number[]) => {
        drawPoint(pt[0], pt[1], colors.p);
      });
      // Lines
      poseConnections.forEach(([i, j]) => {
        if (frameData.p[i] && frameData.p[j]) {
          drawLine(frameData.p[i], frameData.p[j], colors.p);
        }
      });
    }

    // Draw Hands
    const drawHand = (handData: any[], color: string) => {
      if (!handData) return;
      handData.forEach((pt: number[]) => drawPoint(pt[0], pt[1], color));
      // Simplified hand skeleton lines
      const connections = [
        [0,1], [1,2], [2,3], [3,4], // Thumb
        [0,5], [5,6], [6,7], [7,8], // Index
        [0,9], [9,10], [10,11], [11,12], // Middle
        [0,13], [13,14], [14,15], [15,16], // Ring
        [0,17], [17,18], [18,19], [19,20], // Pinky
      ];
      connections.forEach(([i, j]) => {
        if (handData[i] && handData[j]) {
          drawLine(handData[i], handData[j], color);
        }
      });
    };

    drawHand(frameData.l, colors.l);
    drawHand(frameData.r, colors.r);

    // Catmull-Rom Spline implementation for face
    const drawSpline = (pts: number[][], color: string, isClosed: boolean) => {
      if (!pts || pts.length < 3) return;
      
      const toPixel = (pt: number[]) => {
        return {
          x: (pt[0] * scale + offset) * width,
          y: (pt[1] * scale + offset) * height
        };
      };

      const pixels = pts.map(toPixel);
      if (isClosed) pixels.push(pixels[0]); // Close loop
      
      ctx.beginPath();
      ctx.moveTo(pixels[0].x, pixels[0].y);
      
      // Simple lines for face to avoid complex Catmull-Rom math in JS for now,
      // but drawn continuously
      for (let i = 1; i < pixels.length; i++) {
        ctx.lineTo(pixels[i].x, pixels[i].y);
      }
      
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.shadowBlur = 5;
      ctx.shadowColor = color;
      if (isClosed) {
        ctx.closePath();
      }
      ctx.stroke();
    };

    // Draw Face (with splines if available)
    if (frameData.fj) {
      drawSpline(frameData.fj, colors.f, false); // Jaw
      drawSpline(frameData.fl, colors.f, true);  // Lips
      drawSpline(frameData.fre, colors.f, true); // Right Eye
      drawSpline(frameData.fle, colors.f, true); // Left Eye
    } else if (frameData.f) {
      // Fallback
      frameData.f.forEach((pt: number[]) => {
        drawPoint(pt[0], pt[1], colors.f);
      });
    }
  };

  const handleClose = () => {
    if ((window as any).electronAPI) {
      (window as any).electronAPI.closeWindow();
    }
  };

  return (
    <div 
      className="w-screen h-screen overflow-hidden flex items-center justify-center relative group" 
      style={{ WebkitAppRegion: 'drag' } as any}
    >
      <button 
        onClick={handleClose}
        className="absolute top-4 right-4 z-50 text-white/0 hover:text-white bg-black/0 hover:bg-black/50 w-8 h-8 rounded-full transition-all flex items-center justify-center cursor-pointer opacity-0 group-hover:opacity-100"
        style={{ WebkitAppRegion: 'no-drag' } as any}
      >
        ✕
      </button>

      {/* Main Canvas centered inside the narrower window */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1280px] h-[720px] pointer-events-none">
        <canvas 
          ref={canvasRef} 
          width={1280} 
          height={720} 
          className="w-full h-full"
        />
      </div>
    </div>
  );
};

export default App;
