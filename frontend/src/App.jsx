import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { Reports } from './pages/Reports';
import { ZoneSetup } from './pages/ZoneSetup';
import { Landing } from './pages/Landing';
import { ViolationLogs } from './pages/ViolationLogs';
import { Login } from './pages/Login';
import { PrivateRoute } from './components/PrivateRoute';
import { Menu } from 'lucide-react';
import { Toaster } from 'react-hot-toast';

// Create a layout component to conditionally render Sidebar and Header
function AppLayout() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const location = useLocation();
  const isPublicPage = ['/', '/login'].includes(location.pathname);
  const showSidebarAndHeader = !isPublicPage;

  return (
    <div className="min-h-screen bg-background text-white selection:bg-accent/30 overflow-x-hidden">
      {showSidebarAndHeader && <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />}
      
      {/* Top Header with Toggle - Hide on Login and Landing */}
      {showSidebarAndHeader && (
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
      )}

      <main className={`${showSidebarAndHeader ? 'pt-24 p-8' : ''} transition-all duration-300`}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
          <Route path="/logs" element={<PrivateRoute><ViolationLogs /></PrivateRoute>} />
          <Route path="/reports" element={<PrivateRoute><Reports /></PrivateRoute>} />
          <Route path="/setup" element={<PrivateRoute><ZoneSetup /></PrivateRoute>} />
          <Route path="*" element={<Navigate to="/dashboard" />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Toaster position="top-right" toastOptions={{
        style: {
          background: '#18181b',
          color: '#fff',
          border: '1px solid rgba(255,255,255,0.1)',
        }
      }} />
      <AppLayout />
    </Router>
  );
}

export default App;
