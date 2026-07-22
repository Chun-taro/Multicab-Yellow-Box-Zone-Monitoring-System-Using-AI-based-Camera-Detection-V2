import { LayoutDashboard, FileText, Settings, History, Camera, X, Home, LogOut, Cpu } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import Cookies from 'js-cookie';

const navItems = [
  { icon: Home, label: 'Home', path: '/' },
  { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
  { icon: History, label: 'Violation Logs', path: '/logs' },
  { icon: FileText, label: 'Analytics', path: '/reports' },
  { icon: Settings, label: 'Zone Setup', path: '/setup' },
  { icon: Cpu, label: 'System Status', path: '/compatibility' },
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
            className="fixed left-0 top-0 bottom-0 w-72 glass border-r border-white/10 flex flex-col z-[60] shadow-2xl"
          >
            <div className="p-6">
              <div className="flex items-center justify-between mb-8">
                <NavLink
                  to="/"
                  onClick={onClose}
                  className="flex items-center gap-3 hover:opacity-80 transition-opacity"
                >
                  <div className="w-9 h-9 bg-accent rounded-xl flex items-center justify-center shadow-lg shadow-accent/30">
                    <Camera className="text-white w-5 h-5" />
                  </div>
                  <div>
                    <h1 className="font-bold text-base tracking-tight text-white">YellowBox</h1>
                    <p className="text-[10px] text-muted tracking-widest uppercase font-semibold">AI Monitor v2</p>
                  </div>
                </NavLink>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-white/5 rounded-full transition-colors group"
                >
                  <X className="w-5 h-5 text-muted group-hover:text-white" />
                </button>
              </div>

              <nav className="space-y-1">
                {navItems.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    onClick={onClose}
                    className={({ isActive }) =>
                      `flex items-center gap-4 px-4 py-3 rounded-2xl transition-all duration-200 group ${
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

            <div className="mt-auto p-6 space-y-4">
              <button
                onClick={() => {
                  Cookies.remove('auth_token');
                  onClose();
                  window.location.href = '/login';
                }}
                className="w-full flex items-center gap-4 px-4 py-3 rounded-2xl text-muted hover:text-red-400 hover:bg-red-400/5 transition-all duration-200 group border border-transparent hover:border-red-400/20"
              >
                <LogOut className="w-5 h-5" />
                <span className="font-semibold text-sm">Logout</span>
              </button>
              
              <div className="text-[10px] text-center text-muted font-bold tracking-tight uppercase">
                © 2026 Vehicle Yellow Box Zone Monitoring
              </div>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
