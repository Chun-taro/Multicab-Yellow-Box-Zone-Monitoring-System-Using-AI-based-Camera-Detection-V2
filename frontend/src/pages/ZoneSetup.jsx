import { useState, useRef, useEffect } from 'react';
import { Save, Undo, Info, Camera, MousePointer2 } from 'lucide-react';
import axios from 'axios';
import { motion } from 'framer-motion';

const API_BASE = "http://localhost:5000";

export function ZoneSetup() {
  const [points, setPoints] = useState([]);
  const [config, setConfig] = useState(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [timestamp, setTimestamp] = useState(Date.now());

  useEffect(() => {
    axios.get(`${API_BASE}/api/config`).then(res => setConfig(res.data));
    
    const handleResize = () => resizeCanvas();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const resizeCanvas = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (video && canvas) {
      canvas.width = video.clientWidth;
      canvas.height = video.clientHeight;
      draw();
    }
  };

  const handleCanvasClick = (e) => {
    if (points.length >= 4) return;
    
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    setPoints(prev => [...prev, { x, y }]);
  };

  const draw = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 3;
    ctx.fillStyle = 'rgba(245, 158, 11, 0.2)';

    if (points.length > 0) {
      ctx.beginPath();
      ctx.moveTo(points[0].x, points[0].y);
      points.forEach((p, i) => {
        if (i > 0) ctx.lineTo(p.x, p.y);
        
        // Draw point circles
        ctx.save();
        ctx.fillStyle = '#f59e0b';
        ctx.beginPath();
        ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      });

      if (points.length === 4) {
        ctx.closePath();
        ctx.fill();
      }
      ctx.stroke();
    }
  };

  useEffect(() => {
    draw();
  }, [points]);

  const saveZone = async () => {
    if (points.length !== 4) return alert("Select exactly 4 points");

    const video = videoRef.current;
    const scaleX = video.naturalWidth / video.clientWidth;
    const scaleY = video.naturalHeight / video.clientHeight;

    const realPoints = points.map(p => [
      Math.round(p.x * scaleX),
      Math.round(p.y * scaleY)
    ]);

    try {
      await axios.post(`${API_BASE}/api/zone`, { zone: realPoints });
      alert("Zone saved successfully!");
      setPoints([]);
    } catch (err) {
      console.error(err);
      alert("Failed to save zone");
    }
  };

  return (
    <div className="space-y-8 max-w-[1400px] mx-auto">
      <header className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Zone Configuration</h2>
          <p className="text-muted mt-1">Define the Yellow Box detection area</p>
        </div>
        <div className="flex gap-4">
          <button 
            onClick={() => setPoints([])} 
            className="btn-secondary px-6 py-2.5 rounded-2xl flex items-center gap-2 border-white/10"
          >
            <Undo className="w-4 h-4" />
            Reset Points
          </button>
          <button 
            onClick={saveZone} 
            className="btn-primary px-6 py-2.5 rounded-2xl flex items-center gap-2 shadow-lg shadow-accent/20"
            disabled={points.length !== 4}
          >
            <Save className="w-4 h-4" />
            Save Configuration
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        <div className="lg:col-span-1 space-y-6">
          <div className="glass p-6 rounded-3xl space-y-4">
            <h3 className="font-bold flex items-center gap-2">
              <Info className="w-4 h-4 text-accent" />
              Instructions
            </h3>
            <ul className="text-sm text-muted space-y-4">
              <li className="flex gap-3">
                <span className="w-6 h-6 rounded-full bg-accent/10 border border-accent/20 flex-shrink-0 flex items-center justify-center text-accent text-xs font-bold">1</span>
                <span>Wait for the video feed to load fully.</span>
              </li>
              <li className="flex gap-3">
                <span className="w-6 h-6 rounded-full bg-accent/10 border border-accent/20 flex-shrink-0 flex items-center justify-center text-accent text-xs font-bold">2</span>
                <span>Click 4 points in order (clockwise or counter-clockwise) to outline the yellow box.</span>
              </li>
              <li className="flex gap-3">
                <span className="w-6 h-6 rounded-full bg-accent/10 border border-accent/20 flex-shrink-0 flex items-center justify-center text-accent text-xs font-bold">3</span>
                <span>The polygon will automatically fill when the 4th point is added.</span>
              </li>
            </ul>
          </div>

          <div className="glass p-6 rounded-3xl bg-amber-400/5 border-amber-400/10">
            <div className="flex items-center gap-3 text-amber-400 mb-2">
              <MousePointer2 className="w-5 h-5" />
              <h3 className="font-bold">Point Count</h3>
            </div>
            <p className="text-3xl font-bold font-mono">{points.length} / 4</p>
          </div>
        </div>

        <div className="lg:col-span-3">
          <div className="glass rounded-[2.5rem] overflow-hidden relative border-white/5 shadow-2xl">
            <div className="absolute top-6 left-6 z-20 px-4 py-2 rounded-xl bg-black/60 backdrop-blur border border-white/10 flex items-center gap-3">
               <Camera className="w-4 h-4 text-accent" />
               <span className="text-xs font-bold uppercase tracking-widest">Setup Mode</span>
            </div>
            
            <div className="relative aspect-video bg-black flex items-center justify-center">
              <img 
                ref={videoRef}
                src={`${API_BASE}/video_feed`}
                alt="Setup Feed"
                className="w-full h-full object-contain"
                onLoad={resizeCanvas}
              />
              <canvas 
                ref={canvasRef}
                onClick={handleCanvasClick}
                className="absolute inset-0 cursor-crosshair z-10 w-full h-full"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
