import { useState, useEffect } from 'react';
import { StatCard } from '../components/StatCard';
import { VideoFeed } from '../components/VideoFeed';
import { ViolationList } from '../components/ViolationList';
import { Shield, Camera, AlertTriangle, Activity, X, ExternalLink, Calendar } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

const API_BASE = "http://localhost:5000";

export function Dashboard() {
  const [violations, setViolations] = useState([]);
  const [stats, setStats] = useState({ total_violations: 0 });
  const [selectedViolation, setSelectedViolation] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [vRes, sRes] = await Promise.all([
        axios.get(`${API_BASE}/api/recent_violations`),
        axios.get(`${API_BASE}/api/stats`)
      ]);
      setViolations(vRes.data);
      setStats(sRes.data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000); // Poll every 3 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-8 max-w-[1400px] mx-auto">
      <header className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">System Overview</h2>
          <p className="text-muted mt-1">Real-time AI monitoring and violation detection</p>
        </div>
        <div className="flex gap-4">
           {/* Quick status badges */}
           <div className="flex items-center gap-2 px-4 py-2 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              AI CORE ACTIVE
           </div>
        </div>
      </header>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Total Violations" 
          value={stats.total_violations} 
          icon={AlertTriangle} 
          color="danger"
          trend={12}
        />
        <StatCard 
          title="Active Cameras" 
          value="1" 
          icon={Camera} 
          color="accent"
        />
        <StatCard 
          title="Avg. Response" 
          value="250ms" 
          icon={Activity} 
          color="primary"
        />
        <StatCard 
          title="System Security" 
          value="High" 
          icon={Shield} 
          color="success"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Main Feed Section - Now Expanded */}
        <div className="lg:col-span-9 space-y-6">
          <div className="relative group">
            <VideoFeed src={`${API_BASE}/video_feed`} className="h-[600px] lg:h-[700px]" />
          </div>
          
          <div className="glass p-8 rounded-[2.5rem]">
            <h3 className="text-xl font-bold mb-6 flex items-center gap-3 text-white/90">
              <Activity className="w-6 h-6 text-accent" />
              Dynamic System Performance
            </h3>
            <div className="h-56 flex items-end gap-1.5 px-2">
               {/* Mock bars for frequency visualization */}
               {[...Array(45)].map((_, i) => (
                 <div 
                   key={i} 
                   className="flex-1 bg-accent/20 rounded-t-md hover:bg-accent/50 transition-all duration-300 transform origin-bottom hover:scale-y-110"
                   style={{ height: `${Math.random() * 80 + 20}%` }}
                 />
               ))}
            </div>
          </div>
        </div>

        {/* Live Alerts Section - Refined for Side */}
        <div className="lg:col-span-3 space-y-6">
          <div className="glass p-8 rounded-[2.5rem] h-[850px] lg:h-[950px] flex flex-col border border-white/5">
            <div className="flex justify-between items-center mb-8">
              <h3 className="text-xl font-bold text-white/90">Live Alerts</h3>
              <div className="px-3 py-1 bg-accent/10 border border-accent/20 rounded-full">
                <span className="text-[10px] font-bold text-accent uppercase tracking-wider">Active</span>
              </div>
            </div>
            
            <div className="flex-1 overflow-y-auto pr-3 -mr-3 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
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
              className="relative w-full max-w-5xl glass rounded-[2.5rem] overflow-hidden shadow-2xl border border-white/10"
            >
              <div className="flex flex-col lg:flex-row h-full">
                {/* Image Section */}
                <div className="lg:flex-1 bg-black/40 flex items-center justify-center min-h-[400px]">
                  <img 
                    src={`${API_BASE}/${selectedViolation.image_path}`} 
                    alt="Violation Evidence"
                    className="max-w-full max-h-full object-contain"
                    onError={(e) => {
                      e.target.src = "https://via.placeholder.com/1280x720/1a1a1a/ffffff?text=Evidence+Not+Available";
                    }}
                  />
                </div>
                
                {/* Info Section */}
                <div className="w-full lg:w-80 p-8 flex flex-col border-t lg:border-t-0 lg:border-l border-white/10">
                  <div className="flex justify-between items-start mb-8">
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
                  
                  <div className="space-y-6 flex-1">
                    <div className="flex items-center gap-4 group">
                      <div className="p-3 bg-white/5 rounded-2xl group-hover:bg-accent/10 transition-colors">
                        <Calendar className="w-5 h-5 text-accent" />
                      </div>
                      <div>
                        <p className="text-[10px] font-bold text-muted uppercase tracking-tight">Timestamp</p>
                        <p className="text-sm font-medium">{new Date(selectedViolation.timestamp || selectedViolation.violation_timestamp).toLocaleString()}</p>
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
                  </div>

                  <div className="mt-8 pt-8 border-t border-white/5">
                    <button className="w-full py-4 bg-accent hover:bg-accent/90 text-white rounded-2xl font-bold flex items-center justify-center gap-2 transition-all shadow-lg shadow-accent/20">
                      <ExternalLink className="w-4 h-4" />
                      Full Report
                    </button>
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
