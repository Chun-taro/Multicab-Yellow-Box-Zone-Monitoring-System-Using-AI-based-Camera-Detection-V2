import { motion, AnimatePresence } from 'framer-motion';
import { Eye, Clock, AlertCircle } from 'lucide-react';

export function ViolationList({ violations, onViewImage }) {
  return (
    <div className="flex flex-col gap-3">
      <AnimatePresence initial={false}>
        {violations && violations.length > 0 ? (
          violations.slice(0, 10).map((v, index) => (
            <motion.div
              key={v.id || index}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass p-4 rounded-2xl flex items-center justify-between group hover:bg-white/5 transition-colors border-white/5"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl overflow-hidden bg-black/40 border border-white/10">
                   {/* Thumbnail placeholder or real image if available */}
                   <img 
                      src={`http://localhost:5000/${v.image_path}`} 
                      className="w-full h-full object-cover opacity-60 group-hover:opacity-100 transition-opacity" 
                      alt="v"
                      onError={(e) => { 
                        e.target.onerror = null; 
                        e.target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 24 24' fill='none' stroke='%23475569' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M18 8V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2'%3E%3C/path%3E%3Cpath d='m11 13 3-3 3 3'%3E%3C/path%3E%3Cpath d='m14 10 10 10'%3E%3C/path%3E%3Ccircle cx='14' cy='10' r='10'%3E%3C/circle%3E%3C/svg%3E"; 
                      }}
                   />
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold uppercase tracking-wider text-red-400 bg-red-400/10 px-2 py-0.5 rounded-md border border-red-400/20">
                      {v.label || 'Violation'}
                    </span>
                    <span className="text-[10px] text-muted flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(v.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <p className="text-xs text-muted font-medium">Zone {v.zone_id || 'Alpha'}</p>
                    {v.plate_number ? (
                      <span className="text-[10px] font-black tracking-widest text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded border border-emerald-400/20">
                        {v.plate_number}
                      </span>
                    ) : (
                      <span className="text-[10px] font-medium text-white/20 bg-white/5 px-2 py-0.5 rounded border border-white/10">
                        Unread
                      </span>
                    )}
                  </div>
                </div>
              </div>
              
              <button 
                onClick={() => onViewImage(v)}
                className="p-2.5 rounded-xl bg-white/5 hover:bg-accent hover:text-white transition-all text-muted shadow-sm"
              >
                <Eye className="w-4 h-4" />
              </button>
            </motion.div>
          ))
        ) : (
          <div className="py-12 flex flex-col items-center justify-center text-muted gap-4">
            <AlertCircle className="w-12 h-12 opacity-10" />
            <p className="text-sm font-medium opacity-40">Scanning for violations...</p>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
