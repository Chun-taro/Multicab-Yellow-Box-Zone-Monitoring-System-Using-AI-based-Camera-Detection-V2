import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { Reports } from './pages/Reports';
import { ZoneSetup } from './pages/ZoneSetup';
import { Landing } from './pages/Landing';
import { ViolationLogs } from './pages/ViolationLogs';
import { Menu } from 'lucide-react';

function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  return (
    <Router>
      <div className="min-h-screen bg-background text-white selection:bg-accent/30 overflow-x-hidden">
        <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
        
        {/* Top Header with Toggle */}
        <header className="fixed top-0 left-0 right-0 h-16 glass-header flex items-center px-6 z-40">
          <button 
            onClick={() => setIsSidebarOpen(true)}
            className="p-2 hover:bg-white/5 rounded-xl transition-colors group"
          >
            <Menu className="w-6 h-6 text-muted group-hover:text-white" />
          </button>
          <div className="ml-4 h-6 w-[1px] bg-white/10" />
          <h2 className="ml-4 font-bold tracking-tight text-white/90">Vehicle Monitor</h2>
        </header>

        <main className="pt-24 p-8 transition-all duration-300">
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/logs" element={<ViolationLogs />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/setup" element={<ZoneSetup />} />
            <Route path="*" element={<Navigate to="/dashboard" />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
