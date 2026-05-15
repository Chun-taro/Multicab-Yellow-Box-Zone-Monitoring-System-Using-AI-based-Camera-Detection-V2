import { useState, useEffect } from 'react';
import { Maximize2, RefreshCw } from 'lucide-react';

export function VideoFeed({ src, title = "Live Monitoring", stats = {} }) {
  const [timestamp, setTimestamp] = useState(Date.now());
  const [isHovered, setIsHovered] = useState(false);

  const refreshFeed = () => {
    setTimestamp(Date.now());
  };

  return (
    <div 
      className="glass rounded-3xl overflow-hidden relative group"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="absolute inset-x-0 top-0 p-4 flex justify-between items-center z-10 bg-gradient-to-b from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
        <div className="flex items-center gap-6">
          <h3 className="font-semibold text-sm flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            {title}
          </h3>
          
          <div className="flex items-center gap-4 border-l border-white/10 pl-6">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold text-muted uppercase tracking-tight">People</span>
              <span className="text-xs font-bold text-accent">{stats.person_count || 0}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold text-muted uppercase tracking-tight">Vehicles</span>
              <span className="text-xs font-bold text-primary">{stats.vehicle_count || 0}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold text-muted uppercase tracking-tight">AI Speed</span>
              <span className="text-xs font-bold text-emerald-400">{stats.fps_ai || 0} FPS</span>
            </div>
          </div>
        </div>
        
        <div className="flex gap-2">
          <button onClick={refreshFeed} className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors">
            <RefreshCw className="w-4 h-4" />
          </button>
          <button className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors">
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="aspect-video bg-black flex items-center justify-center relative">
        <img 
          src={`${src}?t=${timestamp}`} 
          alt="Video Feed" 
          className="w-full h-full object-contain"
          onError={(e) => {
            e.target.style.display = 'none';
            e.target.nextSibling.style.display = 'flex';
          }}
        />
        <div className="hidden absolute inset-0 flex-col items-center justify-center text-muted gap-3">
          <RefreshCw className="w-10 h-10 opacity-20 animate-spin" />
          <p className="text-sm font-medium">Reconnecting to camera...</p>
        </div>
      </div>
    </div>
  );
}
