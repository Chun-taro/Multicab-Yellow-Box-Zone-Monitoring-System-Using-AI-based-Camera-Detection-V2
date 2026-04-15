import { LayoutDashboard, FileText, Settings, History, Camera, Info, X } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
  { icon: History, label: 'Violation Logs', path: '/logs' },
  { icon: FileText, label: 'Analytics', path: '/reports' },
  { icon: Settings, label: 'Zone Setup', path: '/setup' },
];

export function Sidebar({ isOpen, onClose }) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[50]"
          />

          {/* Drawer */}
          <motion.aside
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed left-0 top-0 bottom-0 w-80 glass border-r border-white/10 flex flex-col z-[60] shadow-2xl"
          >
            <div className="p-8">
              <div className="flex items-center justify-between mb-10">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-accent rounded-xl flex items-center justify-center shadow-lg shadow-accent/30">
                    <Camera className="text-white w-6 h-6" />
                  </div>
                  <div>
                    <h1 className="font-bold text-lg tracking-tight text-white">YellowBox</h1>
                    <p className="text-[10px] text-muted tracking-widest uppercase font-semibold">AI Monitor v2</p>
                  </div>
                </div>
                <button 
                  onClick={onClose}
                  className="p-2 hover:bg-white/5 rounded-full transition-colors group"
                >
                  <X className="w-5 h-5 text-muted group-hover:text-white" />
                </button>
              </div>

              <nav className="space-y-2">
                {navItems.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    onClick={onClose}
                    className={({ isActive }) =>
                      `flex items-center gap-4 px-4 py-4 rounded-2xl transition-all duration-200 group ${
                        isActive 
                          ? 'bg-accent/15 text-accent border border-accent/20' 
                          : 'text-muted hover:text-white hover:bg-white/5'
                      }`
                    }
                  >
                    <item.icon className="w-5 h-5" />
                    <span className="font-semibold text-sm">{item.label}</span>
                  </NavLink>
                ))}
              </nav>
            </div>

            <div className="mt-auto p-8 space-y-6">
              <div className="p-5 rounded-[2rem] bg-gradient-to-br from-primary/10 to-accent/10 border border-white/5 relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:scale-110 transition-transform">
                  <Info className="w-12 h-12" />
                </div>
                <p className="text-xs text-white font-bold mb-2 relative z-10">Smart Detection</p>
                <p className="text-[11px] text-muted leading-relaxed relative z-10">AI tracking ensures accuracy on every frame.</p>
              </div>
              
              <div className="text-[10px] text-center text-muted font-bold tracking-tight uppercase">
                © 2026 VEHICLE MONITOR SYSTEM
              </div>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
