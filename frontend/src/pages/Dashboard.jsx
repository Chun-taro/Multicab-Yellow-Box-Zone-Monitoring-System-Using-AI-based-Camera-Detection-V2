import { useState, useEffect } from 'react';
import { StatCard } from '../components/StatCard';
import { VideoFeed } from '../components/VideoFeed';
import { ViolationList } from '../components/ViolationList';
import { AlertTriangle, Camera, X, ExternalLink, Calendar, Activity, CreditCard, Upload, PlayCircle, Film } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

const API_BASE = "http://localhost:5000";

export function Dashboard() {
  const [violations, setViolations] = useState([]);
  const [stats, setStats] = useState({ total_violations: 0 });
  const [selectedViolation, setSelectedViolation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [cameraConfig, setCameraConfig] = useState({ camera_source: '0' });
  const [isUpdatingSource, setIsUpdatingSource] = useState(false);
  const [showCustomSource, setShowCustomSource] = useState(false);
  const [customSource, setCustomSource] = useState('');
  const [realtimeStats, setRealtimeStats] = useState({});
  const [testVideos, setTestVideos] = useState([]);
  const [isUploading, setIsUploading] = useState(false);

  const fetchData = async () => {
    try {
      const [vRes, sRes, cRes, tvRes] = await Promise.all([
        axios.get(`${API_BASE}/api/recent_violations`),
        axios.get(`${API_BASE}/api/stats`),
        axios.get(`${API_BASE}/api/config`),
        axios.get(`${API_BASE}/api/test_videos`)
      ]);
      setViolations(vRes.data);
      setStats(sRes.data);
      setCameraConfig(cRes.data);
      setTestVideos(tvRes.data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
    }
  };

  const handleSourceChange = async (source) => {
    if (!source) return;
    setIsUpdatingSource(true);
    try {
      await axios.post(`${API_BASE}/set_camera`, { source });
      setCameraConfig(prev => ({ ...prev, camera_source: source }));
      setTimeout(() => { window.location.reload(); }, 1000);
    } catch (error) {
      console.error("Failed to update camera source:", error);
    } finally {
      setIsUpdatingSource(false);
    }
  };

  const handleVideoUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('video', file);

    setIsUploading(true);
    try {
      const res = await axios.post(`${API_BASE}/api/upload_video`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      if (res.data.success) {
        // Refresh video list
        const tvRes = await axios.get(`${API_BASE}/api/test_videos`);
        setTestVideos(tvRes.data);
        // Automatically switch to the new video
        handleSourceChange(`camera/${res.data.filename}`);
      }
    } catch (error) {
      console.error("Upload failed:", error);
      alert("Failed to upload video.");
    } finally {
      setIsUploading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    const abortController = new AbortController();

    const pollForUpdates = async () => {
      while (isMounted) {
        try {
          const res = await axios.get(`${API_BASE}/api/wait_for_violation`, {
            signal: abortController.signal
          });
          if (res.data.update && isMounted) {
            await fetchData();
          }
        } catch (error) {
          if (axios.isCancel(error) || !isMounted) break;
          console.error("Polling error:", error);
          if (isMounted) {
            await new Promise(resolve => setTimeout(resolve, 3000));
          }
        }
      }
    };

    fetchData().then(() => {
      if (isMounted) pollForUpdates();
    });

    // Real-time stats polling (every 2 seconds)
    const statsInterval = setInterval(async () => {
      if (!isMounted) return;
      try {
        const res = await axios.get(`${API_BASE}/api/realtime_stats`, {
          signal: abortController.signal
        });
        setRealtimeStats(res.data);
      } catch (error) {
        if (!axios.isCancel(error)) {
          console.error("Error fetching realtime stats:", error);
        }
      }
    }, 2000);

    return () => {
      isMounted = false;
      abortController.abort();
      clearInterval(statsInterval);
    };
  }, []);


  return (
    <div className="space-y-4 max-w-[1400px] mx-auto">
      <header className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">System Overview</h2>
          <p className="text-muted text-xs">Real-time AI monitoring and violation detection</p>
        </div>
        <div className="flex gap-3 items-center">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold text-muted uppercase tracking-widest">Input Source</span>
            <select
              value={showCustomSource ? 'custom' : cameraConfig.camera_source}
              onChange={(e) => {
                if (e.target.value === 'custom') {
                  setShowCustomSource(true);
                } else {
                  setShowCustomSource(false);
                  handleSourceChange(e.target.value);
                }
              }}
              disabled={isUpdatingSource}
              className="bg-zinc-900 border border-white/10 rounded-xl px-3 py-1.5 text-xs font-bold outline-none focus:border-accent/50 transition-colors cursor-pointer disabled:opacity-50 text-white"
            >
              <option value="0" className="bg-zinc-900 text-white">Default Camera (Index 0)</option>
              <option value="1" className="bg-zinc-900 text-white">Secondary Camera (Index 1)</option>
              <option value="2" className="bg-zinc-900 text-white">Third Camera (Index 2)</option>
              
              {testVideos.map(video => (
                <option key={video} value={`camera/${video}`} className="bg-zinc-900 text-white">
                  Test: {video}
                </option>
              ))}
              
              <option value="custom" className="bg-zinc-900 text-white">+ Custom RTSP/Stream</option>
            </select>
          </div>

          <div className="relative">
            <input
              type="file"
              id="video-upload"
              className="hidden"
              accept="video/*"
              onChange={handleVideoUpload}
              disabled={isUploading}
            />
            <label
              htmlFor="video-upload"
              className={`flex items-center gap-2 px-3 py-1.5 bg-zinc-900 border border-white/10 rounded-xl text-xs font-bold cursor-pointer hover:border-accent/50 transition-colors ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <Upload className={`w-3.5 h-3.5 ${isUploading ? 'animate-bounce' : ''}`} />
              {isUploading ? 'UPLOADING...' : 'UPLOAD TEST VIDEO'}
            </label>
          </div>

          {showCustomSource && (
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="rtsp://admin:password@ip:port/..."
                value={customSource}
                onChange={(e) => setCustomSource(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSourceChange(customSource)}
                className="bg-zinc-900 border border-white/10 rounded-xl px-4 py-1.5 text-xs font-medium w-64 outline-none focus:border-accent/50 text-white"
              />
              <button
                onClick={() => handleSourceChange(customSource)}
                disabled={isUpdatingSource || !customSource}
                className="px-4 py-1.5 bg-accent hover:bg-accent/90 text-white text-[10px] font-bold rounded-xl transition-all disabled:opacity-50"
              >
                CONNECT
              </button>
            </div>
          )}

          <div className="flex items-center gap-2 px-4 py-2 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            {isUpdatingSource ? 'SWITCHING...' : 'AI ACTIVE'}
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Main Feed + Stats */}
        <div className="lg:col-span-9 space-y-4">
          <VideoFeed 
            src={`${API_BASE}/video_feed`} 
            className="h-[600px] lg:h-[680px]" 
            stats={realtimeStats}
          />

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <StatCard
              title="Total Violations"
              value={loading ? '—' : stats.total_violations}
              icon={AlertTriangle}
              color="danger"
            />
            <StatCard
              title="Saved Videos"
              value={loading ? '—' : testVideos.length}
              icon={Film}
              color="primary"
            />
            <StatCard
              title="Active Cameras"
              value="1"
              icon={Camera}
              color="accent"
            />
          </div>
        </div>

        {/* Live Alerts */}
        <div className="lg:col-span-3">
          <div className="glass p-6 rounded-[2.5rem] h-[680px] flex flex-col border border-white/5">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-bold text-white/90">Live Alerts</h3>
              <div className="px-3 py-1 bg-accent/10 border border-accent/20 rounded-full">
                <span className="text-[10px] font-bold text-accent uppercase tracking-wider">
                  {violations.length} recent
                </span>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
              <ViolationList
                violations={violations}
                onViewImage={setSelectedViolation}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Evidence Modal */}
      <AnimatePresence>
        {selectedViolation && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedViolation(null)}
              className="absolute inset-0 bg-black/80 backdrop-blur-md"
            />
            <motion.div
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              className="relative w-full max-w-4xl glass rounded-[2.5rem] overflow-hidden shadow-2xl border border-white/10"
            >
              <div className="flex flex-col lg:flex-row h-full">
                {/* Image */}
                <div className="lg:flex-1 bg-black/40 flex items-center justify-center min-h-[360px]">
                  <img
                    src={`${API_BASE}/${selectedViolation.image_path}`}
                    alt="Violation Evidence"
                    className="max-w-full max-h-full object-contain"
                    onError={(e) => {
                      e.target.src = "https://via.placeholder.com/1280x720/1a1a1a/ffffff?text=Evidence+Not+Available";
                    }}
                  />
                </div>

                {/* Details */}
                <div className="w-full lg:w-72 p-8 flex flex-col border-t lg:border-t-0 lg:border-l border-white/10">
                  <div className="flex justify-between items-start mb-6">
                    <div>
                      <h4 className="text-[10px] font-bold text-accent uppercase tracking-widest mb-1">Violation Details</h4>
                      <h3 className="text-xl font-bold capitalize text-white">{selectedViolation.label}</h3>
                    </div>
                    <button
                      onClick={() => setSelectedViolation(null)}
                      className="p-2 hover:bg-white/5 rounded-full transition-colors"
                    >
                      <X className="w-5 h-5 text-muted hover:text-white" />
                    </button>
                  </div>

                  <div className="space-y-5 flex-1">
                    <div className="flex items-center gap-4 group">
                      <div className="p-3 bg-white/5 rounded-2xl group-hover:bg-accent/10 transition-colors">
                        <Calendar className="w-5 h-5 text-accent" />
                      </div>
                      <div>
                        <p className="text-[10px] font-bold text-muted uppercase tracking-tight">Timestamp</p>
                        <p className="text-sm font-medium">
                          {new Date(selectedViolation.timestamp || selectedViolation.violation_timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 group">
                      <div className="p-3 bg-white/5 rounded-2xl group-hover:bg-primary/10 transition-colors">
                        <Activity className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <p className="text-[10px] font-bold text-muted uppercase tracking-tight">Stop Duration</p>
                        <p className="text-sm font-medium">{selectedViolation.stop_duration}s</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 group">
                      <div className="p-3 bg-white/5 rounded-2xl group-hover:bg-amber-500/10 transition-colors">
                        <CreditCard className="w-5 h-5 text-amber-500" />
                      </div>
                      <div>
                        <p className="text-[10px] font-bold text-muted uppercase tracking-tight">Plate Number</p>
                        <p className="text-sm font-bold tracking-wider text-white">
                          {selectedViolation.plate_number || "NOT DETECTED"}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
