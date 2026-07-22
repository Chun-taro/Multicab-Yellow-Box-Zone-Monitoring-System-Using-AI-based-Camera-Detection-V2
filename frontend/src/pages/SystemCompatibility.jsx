import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { 
  Cpu, 
  HardDrive, 
  Layers, 
  Monitor, 
  RefreshCw, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  Wrench, 
  Gauge, 
  Settings,
  ShieldCheck,
  Flame,
  Activity
} from 'lucide-react';
import toast from 'react-hot-toast';

const API_BASE = "http://localhost:5000";
const CACHE_KEY = "yellowbox_compatibility_scan";

export function SystemCompatibility() {
  const [scanResult, setScanResult] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [scanStep, setScanStep] = useState(0);
  const [progress, setProgress] = useState(0);

  const scanSteps = [
    "Initializing Hardware Scanner...",
    "Analyzing Operating System & Architecture...",
    "Scanning CPU Processor Cores & Speed...",
    "Detecting Graphics Cards & CUDA Engines...",
    "Measuring RAM Capacity & Drive Storage...",
    "Compiling System Performance Score..."
  ];

  // Load cached scan on mount
  useEffect(() => {
    const cached = localStorage.getItem(CACHE_KEY);
    if (cached) {
      try {
        setScanResult(JSON.parse(cached));
      } catch (e) {
        console.error("Failed to parse cached scan results:", e);
      }
    } else {
      // Auto scan if no cache exists
      performScan();
    }
  }, []);

  // Simulated scan progress
  const performScan = async () => {
    setScanning(true);
    setScanResult(null);
    setScanStep(0);
    setProgress(0);

    const stepInterval = 400; // Duration per step in ms
    let currentStep = 0;

    const timer = setInterval(() => {
      currentStep++;
      if (currentStep < scanSteps.length) {
        setScanStep(currentStep);
        setProgress((currentStep / scanSteps.length) * 100);
      } else {
        clearInterval(timer);
        setProgress(100);
      }
    }, stepInterval);

    try {
      const response = await axios.get(`${API_BASE}/api/hardware/scan`);
      
      // Wait for progress animation to hit 100%
      await new Promise(resolve => setTimeout(resolve, stepInterval * 1.5));
      
      setScanResult(response.data);
      localStorage.setItem(CACHE_KEY, JSON.stringify(response.data));
      toast.success("System scan completed successfully!");
    } catch (error) {
      console.error("Hardware scan error:", error);
      toast.error("Failed to retrieve hardware details. Please ensure the backend server is running.");
      
      // Load fallback mock data so page doesn't crash if server is offline
      const fallbackData = getFallbackMockData();
      setScanResult(fallbackData);
    } finally {
      clearInterval(timer);
      setScanning(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Recommended':
      case 'Pass':
        return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
      case 'Minimum':
        return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
      case 'Fail':
        return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
      default:
        return 'text-slate-400 bg-slate-500/10 border-slate-500/20';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'Recommended':
      case 'Pass':
        return <CheckCircle2 className="w-5 h-5 text-emerald-400" />;
      case 'Minimum':
        return <AlertTriangle className="w-5 h-5 text-amber-400" />;
      case 'Fail':
        return <XCircle className="w-5 h-5 text-rose-400" />;
      default:
        return <CheckCircle2 className="w-5 h-5 text-slate-400" />;
    }
  };

  const getOverallResultDetails = (result) => {
    switch (result) {
      case 'Fully Compatible':
        return {
          title: "Fully Compatible",
          desc: "Your computer exceeds the recommended requirements. Real-time AI models will run at peak performance using hardware acceleration.",
          color: "border-emerald-500/30 bg-emerald-950/20 shadow-emerald-500/5",
          icon: <ShieldCheck className="w-12 h-12 text-emerald-400" />
        };
      case 'Meets Minimum Requirements':
        return {
          title: "Meets Minimum Requirements",
          desc: "The system is compatible but might run AI inference on the CPU, causing lower processing frame rates. Closing background programs is advised.",
          color: "border-amber-500/30 bg-amber-950/20 shadow-amber-500/5",
          icon: <AlertTriangle className="w-12 h-12 text-amber-400" />
        };
      case 'Does Not Meet Requirements':
      default:
        return {
          title: "Does Not Meet Requirements",
          desc: "Critical hardware specifications do not meet the minimum requirements. YellowBox AI Monitor may crash, hang, or execute extremely slowly.",
          color: "border-rose-500/30 bg-rose-950/20 shadow-rose-500/5",
          icon: <XCircle className="w-12 h-12 text-rose-400" />
        };
    }
  };

  const getFallbackMockData = () => {
    return {
      cpu: {
        model: "Unknown CPU (Offline)",
        cores: 4,
        threads: 8,
        clock_speed_ghz: 2.5,
        status: "Minimum",
        message: "Unable to reach server. Displaying cached or generic offline CPU parameters."
      },
      gpu: {
        devices: [
          { name: "Generic Video Controller", type: "Integrated", vram_gb: "Shared", is_active_ai: false }
        ],
        status: "Minimum",
        message: "No active GPU API connected."
      },
      ram: {
        total_gb: 8.0,
        status: "Minimum",
        message: "Generic 8 GB total RAM assumed."
      },
      storage: {
        total_gb: 256.0,
        free_gb: 10.0,
        status: "Minimum",
        message: "Storage stats unavailable."
      },
      os: {
        name: "Windows Desktop",
        version: "10.0",
        architecture: "64-bit",
        status: "Pass",
        message: "Assuming 64-bit architecture."
      },
      apis: {
        cuda_available: false,
        cuda_version: "N/A",
        directx: "DirectX 12 (Assumed)",
        opengl: "OpenGL 4.0+ (Assumed)",
        vulkan: "Vulkan (Assumed)"
      },
      compatibility: {
        score: 55,
        result: "Meets Minimum Requirements",
        suggestions: [
          "Ensure Flask backend is started to obtain accurate machine diagnostics.",
          "Check system logs to debug connection issues."
        ]
      }
    };
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/5 pb-6">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white via-white/90 to-white/60 bg-clip-text text-transparent">
            Hardware Scanner
          </h1>
          <p className="text-sm text-muted mt-2">
            Verify system specifications to ensure smooth camera feeds, YOLOv8 tracking, and EasyOCR recognition.
          </p>
        </div>
        <button
          onClick={performScan}
          disabled={scanning}
          className="flex items-center justify-center gap-2 bg-accent hover:bg-accent/90 disabled:bg-accent/50 text-white font-semibold px-5 py-3 rounded-2xl transition-all shadow-lg shadow-accent/20 active:scale-[0.98] w-full md:w-auto"
        >
          <RefreshCw className={`w-4 h-4 ${scanning ? 'animate-spin' : ''}`} />
          {scanning ? "Scanning..." : "Scan Hardware"}
        </button>
      </div>

      <AnimatePresence mode="wait">
        {/* Scanning State */}
        {scanning && (
          <motion.div
            key="scanning"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.98 }}
            className="glass-card border border-white/10 rounded-3xl p-12 text-center flex flex-col items-center justify-center min-h-[400px] relative overflow-hidden"
          >
            {/* Background grid design */}
            <div className="absolute inset-0 bg-grid opacity-10 pointer-events-none" />
            
            <div className="relative w-24 h-24 mb-8">
              <div className="absolute inset-0 rounded-full border-4 border-white/5 animate-pulse" />
              <div className="absolute inset-0 rounded-full border-4 border-t-accent border-r-transparent border-b-transparent border-l-transparent animate-spin" />
              <div className="absolute inset-4 rounded-full bg-accent/10 flex items-center justify-center">
                <Gauge className="w-8 h-8 text-accent animate-pulse" />
              </div>
            </div>

            <h3 className="text-xl font-bold tracking-tight text-white/90">Analyzing System Hardware</h3>
            <p className="text-sm text-muted max-w-md mt-2 h-10">
              {scanSteps[scanStep]}
            </p>

            {/* Progress Bar */}
            <div className="w-full max-w-md bg-white/5 border border-white/10 rounded-full h-3 overflow-hidden mt-6 shadow-inner">
              <motion.div 
                className="bg-accent h-full shadow-[0_0_12px_rgba(20,110,245,0.6)]"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.2 }}
              />
            </div>
            <span className="text-[11px] font-bold text-accent tracking-wider uppercase mt-3">
              Progress: {Math.round(progress)}%
            </span>
          </motion.div>
        )}

        {/* Scan Completed Results */}
        {!scanning && scanResult && (
          <motion.div
            key="results"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4 }}
            className="space-y-8"
          >
            {/* Top Compatibility Status Box */}
            {(() => {
              const details = getOverallResultDetails(scanResult.compatibility.result);
              return (
                <div className={`border rounded-3xl p-6 md:p-8 flex flex-col md:flex-row items-center gap-6 shadow-xl transition-all ${details.color}`}>
                  <div className="flex-shrink-0 flex items-center justify-center p-4 bg-white/5 rounded-2xl border border-white/10 shadow-lg">
                    {details.icon}
                  </div>
                  <div className="flex-grow text-center md:text-left space-y-2">
                    <div className="flex flex-col md:flex-row md:items-center justify-center md:justify-start gap-3">
                      <h2 className="text-2xl font-black text-white">{details.title}</h2>
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold border ${getStatusColor(scanResult.compatibility.result === 'Fully Compatible' ? 'Recommended' : scanResult.compatibility.result === 'Meets Minimum Requirements' ? 'Minimum' : 'Fail')}`}>
                        Score: {scanResult.compatibility.score}/100
                      </span>
                    </div>
                    <p className="text-sm text-muted max-w-2xl">
                      {details.desc}
                    </p>
                  </div>
                </div>
              );
            })()}

            {/* Grid for main components */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* CPU Card */}
              <motion.div 
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="glass-card border border-white/5 hover:border-white/10 rounded-3xl p-6 flex flex-col justify-between shadow-lg"
              >
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-white/5 pb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-blue-500/10 border border-blue-500/20 rounded-xl flex items-center justify-center">
                        <Cpu className="w-5 h-5 text-blue-400" />
                      </div>
                      <div>
                        <h3 className="font-bold text-white text-base">CPU (Processor)</h3>
                        <p className="text-xs text-muted">Core operations & tracker</p>
                      </div>
                    </div>
                    <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${getStatusColor(scanResult.cpu.status)}`}>
                      {scanResult.cpu.status === 'Recommended' ? 'Pass' : scanResult.cpu.status}
                    </span>
                  </div>
                  
                  <div className="space-y-2.5">
                    <p className="text-sm font-semibold text-white/90">{scanResult.cpu.model}</p>
                    <div className="grid grid-cols-3 gap-2 pt-2 text-center">
                      <div className="bg-white/5 rounded-xl p-2 border border-white/5">
                        <span className="text-[10px] text-muted block uppercase font-bold">Cores</span>
                        <span className="text-sm font-extrabold text-white">{scanResult.cpu.cores}</span>
                      </div>
                      <div className="bg-white/5 rounded-xl p-2 border border-white/5">
                        <span className="text-[10px] text-muted block uppercase font-bold">Threads</span>
                        <span className="text-sm font-extrabold text-white">{scanResult.cpu.threads}</span>
                      </div>
                      <div className="bg-white/5 rounded-xl p-2 border border-white/5">
                        <span className="text-[10px] text-muted block uppercase font-bold">Frequency</span>
                        <span className="text-sm font-extrabold text-white">{scanResult.cpu.clock_speed_ghz} GHz</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex items-start gap-2 text-xs text-muted mt-5 pt-3 border-t border-white/5">
                  <div className="mt-0.5">{getStatusIcon(scanResult.cpu.status)}</div>
                  <span>{scanResult.cpu.message}</span>
                </div>
              </motion.div>

              {/* GPU Card */}
              <motion.div 
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 }}
                className="glass-card border border-white/5 hover:border-white/10 rounded-3xl p-6 flex flex-col justify-between shadow-lg"
              >
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-white/5 pb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-indigo-500/10 border border-indigo-500/20 rounded-xl flex items-center justify-center">
                        <Flame className="w-5 h-5 text-indigo-400" />
                      </div>
                      <div>
                        <h3 className="font-bold text-white text-base">Graphics Card (GPU)</h3>
                        <p className="text-xs text-muted">AI inference & detection</p>
                      </div>
                    </div>
                    <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${getStatusColor(scanResult.gpu.status)}`}>
                      {scanResult.gpu.status === 'Recommended' ? 'Pass' : scanResult.gpu.status}
                    </span>
                  </div>

                  <div className="space-y-3 max-h-[120px] overflow-y-auto custom-scrollbar">
                    {scanResult.gpu.devices.map((device, idx) => (
                      <div key={idx} className="flex justify-between items-center bg-white/5 rounded-2xl p-3 border border-white/5">
                        <div className="min-w-0 flex-1 pr-2">
                          <div className="flex items-center gap-2">
                            <p className="text-xs font-semibold text-white/90 truncate">{device.name}</p>
                            {device.is_active_ai && (
                              <span className="flex-shrink-0 text-[9px] bg-accent/20 border border-accent/30 text-accent font-bold px-1.5 py-0.2 rounded-full uppercase tracking-wider">
                                Active AI
                              </span>
                            )}
                          </div>
                          <p className="text-[10px] text-muted mt-0.5">{device.type} Card</p>
                        </div>
                        <span className="text-xs font-bold text-white bg-white/5 px-2.5 py-1 rounded-lg">
                          VRAM: {typeof device.vram_gb === 'number' ? `${device.vram_gb} GB` : device.vram_gb}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex items-start gap-2 text-xs text-muted mt-5 pt-3 border-t border-white/5">
                  <div className="mt-0.5">{getStatusIcon(scanResult.gpu.status)}</div>
                  <span>{scanResult.gpu.message}</span>
                </div>
              </motion.div>

              {/* RAM Card */}
              <motion.div 
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="glass-card border border-white/5 hover:border-white/10 rounded-3xl p-6 flex flex-col justify-between shadow-lg"
              >
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-white/5 pb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center justify-center">
                        <Layers className="w-5 h-5 text-emerald-400" />
                      </div>
                      <div>
                        <h3 className="font-bold text-white text-base">System Memory (RAM)</h3>
                        <p className="text-xs text-muted">Application runtime buffers</p>
                      </div>
                    </div>
                    <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${getStatusColor(scanResult.ram.status)}`}>
                      {scanResult.ram.status === 'Recommended' ? 'Pass' : scanResult.ram.status}
                    </span>
                  </div>

                  <div className="flex items-center justify-between bg-white/5 border border-white/5 rounded-2xl p-4">
                    <div>
                      <span className="text-xs text-muted block uppercase font-bold">Total RAM Installed</span>
                      <span className="text-xl font-black text-white">{scanResult.ram.total_gb} GB</span>
                    </div>
                    <div className="w-16 h-1.5 bg-white/10 rounded-full overflow-hidden">
                      <div 
                        className={`h-full ${scanResult.ram.status === 'Fail' ? 'bg-rose-500' : scanResult.ram.status === 'Minimum' ? 'bg-amber-500' : 'bg-emerald-500'}`} 
                        style={{ width: `${Math.min((scanResult.ram.total_gb / 16) * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>

                <div className="flex items-start gap-2 text-xs text-muted mt-5 pt-3 border-t border-white/5">
                  <div className="mt-0.5">{getStatusIcon(scanResult.ram.status)}</div>
                  <span>{scanResult.ram.message}</span>
                </div>
              </motion.div>

              {/* Storage Card */}
              <motion.div 
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.25 }}
                className="glass-card border border-white/5 hover:border-white/10 rounded-3xl p-6 flex flex-col justify-between shadow-lg"
              >
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-white/5 pb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-center justify-center">
                        <HardDrive className="w-5 h-5 text-amber-400" />
                      </div>
                      <div>
                        <h3 className="font-bold text-white text-base">Disk Space (Storage)</h3>
                        <p className="text-xs text-muted">Screenshots & logs database</p>
                      </div>
                    </div>
                    <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${getStatusColor(scanResult.storage.status)}`}>
                      {scanResult.storage.status === 'Recommended' ? 'Pass' : scanResult.storage.status}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white/5 border border-white/5 rounded-2xl p-3">
                      <span className="text-[10px] text-muted block uppercase font-bold">Total Space</span>
                      <span className="text-sm font-bold text-white">{scanResult.storage.total_gb} GB</span>
                    </div>
                    <div className="bg-white/5 border border-white/5 rounded-2xl p-3">
                      <span className="text-[10px] text-muted block uppercase font-bold">Available Free</span>
                      <span className="text-sm font-bold text-white">{scanResult.storage.free_gb} GB</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-start gap-2 text-xs text-muted mt-5 pt-3 border-t border-white/5">
                  <div className="mt-0.5">{getStatusIcon(scanResult.storage.status)}</div>
                  <span>{scanResult.storage.message}</span>
                </div>
              </motion.div>
            </div>

            {/* Bottom Row - OS, APIs & Recommendations */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* OS details card */}
              <div className="glass-card border border-white/5 hover:border-white/10 rounded-3xl p-6 space-y-4">
                <h3 className="font-bold text-white border-b border-white/5 pb-2 text-sm flex items-center gap-2">
                  <Monitor className="w-4 h-4 text-accent" />
                  Operating System
                </h3>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-muted">Platform:</span>
                    <span className="font-semibold text-white">{scanResult.os.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted">Version:</span>
                    <span className="font-semibold text-white">{scanResult.os.version}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted">Architecture:</span>
                    <span className="font-semibold text-white">{scanResult.os.architecture}</span>
                  </div>
                  <div className="pt-2 text-[10px] text-emerald-400 bg-emerald-500/5 rounded-lg p-2 border border-emerald-500/10 text-center font-semibold">
                    ✓ OS Architecture Supported
                  </div>
                </div>
              </div>

              {/* Graphics APIs card */}
              <div className="glass-card border border-white/5 hover:border-white/10 rounded-3xl p-6 space-y-4">
                <h3 className="font-bold text-white border-b border-white/5 pb-2 text-sm flex items-center gap-2">
                  <Settings className="w-4 h-4 text-purple-400" />
                  Graphics Libraries
                </h3>
                <div className="space-y-2.5 text-xs">
                  <div className="flex justify-between items-center">
                    <span className="text-muted">DirectX Support:</span>
                    <span className="font-bold text-white">{scanResult.apis.directx}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-muted">OpenGL Version:</span>
                    <span className="font-bold text-white">{scanResult.apis.opengl}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-muted">Vulkan Driver:</span>
                    <span className="font-bold text-white">{scanResult.apis.vulkan}</span>
                  </div>
                  <div className="flex justify-between items-center border-t border-white/5 pt-2 mt-2">
                    <span className="text-muted">PyTorch CUDA:</span>
                    <span className={`px-2 py-0.5 rounded font-extrabold text-[10px] uppercase ${scanResult.apis.cuda_available ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
                      {scanResult.apis.cuda_available ? 'CUDA Active' : 'No CUDA Device'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Suggestions card */}
              <div className="glass-card border border-white/5 hover:border-white/10 rounded-3xl p-6 space-y-4 md:col-span-1">
                <h3 className="font-bold text-white border-b border-white/5 pb-2 text-sm flex items-center gap-2">
                  <Wrench className="w-4 h-4 text-amber-400" />
                  Upgrade Recommendations
                </h3>
                <div className="space-y-3 max-h-[140px] overflow-y-auto custom-scrollbar">
                  {scanResult.compatibility.suggestions.length === 0 ? (
                    <div className="text-xs text-emerald-400 bg-emerald-500/5 rounded-2xl p-4 border border-emerald-500/10 text-center font-semibold h-full flex items-center justify-center">
                      Your system specifications are optimized. No hardware upgrades needed!
                    </div>
                  ) : (
                    scanResult.compatibility.suggestions.map((suggestion, idx) => (
                      <div key={idx} className="flex gap-2 bg-amber-500/5 border border-amber-500/10 p-2.5 rounded-xl text-[11px] text-amber-300">
                        <Wrench className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                        <span>{suggestion}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
