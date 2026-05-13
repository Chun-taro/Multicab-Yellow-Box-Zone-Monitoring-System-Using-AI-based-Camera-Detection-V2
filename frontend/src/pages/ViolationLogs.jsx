import { useState, useEffect } from 'react';
import { Search, Filter, Eye, Download, SearchIcon, Clock, AlertCircle } from 'lucide-react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = "http://localhost:5000";

export function ViolationLogs() {
  const [violations, setViolations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedViolation, setSelectedViolation] = useState(null);

  useEffect(() => {
    fetchViolations();
  }, []);

  const fetchViolations = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/violations`);
      // Since db returns list of lists usually, map it correctly if needed
      // Based on dashboard_routes.py process_violations, it returns list of dicts
      setViolations(res.data);
      setLoading(false);
    } catch (error) {
       console.error(error);
    }
  };

  const filtered = violations.filter(v => 
    v.label?.toLowerCase().includes(search.toLowerCase()) ||
    v.timestamp?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-8 max-w-[1400px] mx-auto pb-12">
      <header className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Violation History</h2>
          <p className="text-muted mt-1">Full database of captured parking violations</p>
        </div>
        <div className="flex gap-4">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
            <input 
              type="text" 
              placeholder="Search by vehicle or date..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-white/5 border border-white/10 rounded-2xl pl-11 pr-4 py-2.5 outline-none focus:border-accent/50 transition-colors w-64 text-sm"
            />
          </div>
          <button className="btn-secondary px-6 py-2.5 rounded-2xl flex items-center gap-2 border-white/10">
            <Filter className="w-4 h-4" />
            Filter
          </button>
        </div>
      </header>

      <div className="glass rounded-[2rem] overflow-hidden border-white/5">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-white/[0.02] border-b border-white/5">
                <th className="px-8 py-5 text-sm font-bold uppercase tracking-wider text-muted">Evidence</th>
                <th className="px-8 py-5 text-sm font-bold uppercase tracking-wider text-muted">Vehicle Type</th>
                <th className="px-8 py-5 text-sm font-bold uppercase tracking-wider text-muted">Plate No.</th>
                <th className="px-8 py-5 text-sm font-bold uppercase tracking-wider text-muted">Timestamp</th>
                <th className="px-8 py-5 text-sm font-bold uppercase tracking-wider text-muted text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {(filtered || []).map((v, i) => (
                <tr key={v.id || i} className="border-b border-white/5 hover:bg-white/[0.01] transition-colors group">
                  <td className="px-8 py-4">
                    <div className="w-16 h-10 rounded-lg bg-black/40 overflow-hidden border border-white/10">
                      <img 
                        src={`${API_BASE}/${v.image_path}`} 
                        className="w-full h-full object-cover group-hover:scale-110 transition-transform" 
                        onError={(e) => { 
                          e.target.onerror = null; 
                          e.target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 24 24' fill='none' stroke='%23475569' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M18 8V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2'%3E%3C/path%3E%3Cpath d='m11 13 3-3 3 3'%3E%3C/path%3E%3Cpath d='m14 10 10 10'%3E%3C/path%3E%3Ccircle cx='14' cy='10' r='10'%3E%3C/circle%3E%3C/svg%3E"; 
                        }}
                      />
                    </div>
                  </td>
                  <td className="px-8 py-4">
                    <span className="px-3 py-1 rounded-lg bg-red-400/10 text-red-400 text-xs font-bold border border-red-400/20 uppercase">
                      {v.label}
                    </span>
                  </td>
                  <td className="px-8 py-4">
                    {v.plate_number ? (
                      <span className="text-xs font-black tracking-widest text-emerald-400 bg-emerald-400/10 px-3 py-1 rounded border border-emerald-400/20">
                        {v.plate_number}
                      </span>
                    ) : (
                      <span className="text-xs text-white/20">—</span>
                    )}
                  </td>
                  <td className="px-8 py-4">
                    <div className="flex flex-col">
                      <span className="text-sm font-medium">{v.timestamp?.split(' ')[0]}</span>
                      <span className="text-xs text-muted">{v.timestamp?.split(' ')[1]}</span>
                    </div>
                  </td>
                  <td className="px-8 py-4 text-right">
                    <button 
                      onClick={() => setSelectedViolation(v)}
                      className="p-2.5 rounded-xl bg-white/5 hover:bg-accent hover:text-white transition-all text-muted"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {filtered.length === 0 && (
             <div className="py-20 flex flex-col items-center justify-center text-muted gap-4">
                <SearchIcon className="w-16 h-16 opacity-10" />
                <p className="text-lg font-medium opacity-40">No violations match your search</p>
             </div>
          )}
        </div>
      </div>

      {/* Modal for viewing image */}
      <AnimatePresence>
        {selectedViolation && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center p-8 bg-black/90 backdrop-blur-sm"
            onClick={() => setSelectedViolation(null)}
          >
             <motion.div 
               initial={{ scale: 0.9, opacity: 0 }}
               animate={{ scale: 1, opacity: 1 }}
               exit={{ scale: 0.9, opacity: 0 }}
               className="relative max-w-5xl w-full glass rounded-[2.5rem] overflow-hidden border-white/10 shadow-2xl"
               onClick={(e) => e.stopPropagation()}
             >
                <div className="absolute top-6 right-6 z-10">
                   <button 
                    onClick={() => setSelectedViolation(null)}
                    className="w-10 h-10 rounded-full bg-black/60 hover:bg-black/80 flex items-center justify-center text-white transition-colors"
                   >
                     ✕
                   </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-12">
                   <div className="lg:col-span-8 bg-black">
                      <img 
                        src={`${API_BASE}/${selectedViolation.image_path}`} 
                        className="w-full h-auto object-contain" 
                        alt="Evidence"
                      />
                   </div>
                   <div className="lg:col-span-4 p-8 space-y-8 self-center">
                      <div>
                        <h3 className="text-2xl font-bold mb-2">Violation Details</h3>
                        <p className="text-muted text-sm italic">Captured on Automated AI Intercept</p>
                      </div>

                      <div className="space-y-4">
                         <div className="flex justify-between items-center py-3 border-b border-white/5">
                            <span className="text-sm text-muted flex items-center gap-2"><Clock className="w-4 h-4" /> Timestamp</span>
                            <span className="text-sm font-bold">{selectedViolation.timestamp}</span>
                         </div>
                         <div className="flex justify-between items-center py-3 border-b border-white/5">
                            <span className="text-sm text-muted flex items-center gap-2"><AlertCircle className="w-4 h-4" /> Violation Type</span>
                            <span className="text-sm font-bold text-red-400 capitalize">{selectedViolation.label}</span>
                         </div>
                         <div className="flex justify-between items-center py-3 border-b border-white/5">
                            <span className="text-sm text-muted flex items-center gap-2"><Eye className="w-4 h-4" /> Confidence</span>
                            <span className="text-sm font-bold">98.4%</span>
                         </div>
                      </div>

                      <button className="w-full bg-accent hover:bg-accent/90 text-white font-bold py-4 rounded-2xl flex items-center justify-center gap-3 transition-all">
                         <Download className="w-5 h-5" />
                         Download Evidence
                      </button>
                   </div>
                </div>
             </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
