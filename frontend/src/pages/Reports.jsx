import { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  AreaChart, Area, PieChart, Pie, Cell 
} from 'recharts';
import { StatCard } from '../components/StatCard';
import { TrendingUp, PieChart as PieIcon, Calendar, Download, FileSpreadsheet, Eye } from 'lucide-react';
import axios from 'axios';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = "http://localhost:5000";
const COLORS = ['#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#10b981'];

export function Reports() {
  const [stats, setStats] = useState(null);
  const [violations, setViolations] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Date Range Export States
  const [showRangeModal, setShowRangeModal] = useState(false);
  const [pendingExportType, setPendingExportType] = useState(null); // 'PDF' or 'CSV'
  const [dateRange, setDateRange] = useState({
    start: new Date().toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0]
  });
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sRes, vRes] = await Promise.all([
          axios.get(`${API_BASE}/api/stats`),
          axios.get(`${API_BASE}/api/violations`)
        ]);
        setStats(sRes.data);
        setViolations(vRes.data);
        setLoading(false);
      } catch (err) {
        console.error("Error fetching reports data:", err);
      }
    };
    fetchData();
  }, []);

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const response = await axios.get(`${API_BASE}/api/violations`, {
        params: { start: dateRange.start, end: dateRange.end }
      });
      const data = response.data;
      
      if (pendingExportType === 'PDF') {
        generatePDF(data);
      } else {
        generateCSV(data);
      }
      setShowRangeModal(false);
    } catch (err) {
      console.error("Export failed:", err);
    } finally {
      setIsExporting(false);
    }
  };

  const generatePDF = (data) => {
    const doc = new jsPDF();
    const timestamp = new Date().toLocaleString();
    
    // Header
    doc.setFontSize(22);
    doc.setTextColor(59, 130, 246); 
    doc.text("Yellow Box Zone Monitoring System", 14, 22);
    
    doc.setFontSize(12);
    doc.setTextColor(100);
    doc.text(`Official Violation Report | Period: ${dateRange.start} to ${dateRange.end}`, 14, 32);
    doc.text(`Generated: ${timestamp}`, 14, 38);
    
    // Summary Section
    doc.setFontSize(16);
    doc.setTextColor(0);
    doc.text("Report Summary", 14, 52);
    
    doc.setFontSize(11);
    doc.text(`Total Violations in Period: ${data.length}`, 14, 62);
    doc.text(`Current Top Violation: ${pieData[0]?.name || "N/A"}`, 14, 69);
    
    // Violation List Table
    autoTable(doc, {
      startY: 85,
      head: [['ID', 'Vehicle', 'Timestamp', 'Stop Duration', 'Status']],
      body: data.map(v => [
        v.id,
        v.label,
        new Date(v.timestamp || v.violation_timestamp).toLocaleString(),
        `${v.stop_duration}s`,
        v.status || 'recorded'
      ]),
      headStyles: { fillColor: [59, 130, 246] },
      alternateRowStyles: { fillColor: [240, 245, 255] },
      margin: { top: 85 }
    });
    
    doc.save(`Violation_Report_${dateRange.start}_to_${dateRange.end}.pdf`);
  };

  const generateCSV = (data) => {
    const headers = ["ID", "Vehicle", "Timestamp", "Stop Duration", "Status", "Confidence", "Image Path"];
    const rows = data.map(v => [
      v.id,
      v.label,
      v.timestamp || v.violation_timestamp,
      v.stop_duration,
      v.status,
      v.confidence,
      v.image_path
    ]);

    const content = [headers, ...rows].map(e => e.join(",")).join("\n");
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `Violations_${dateRange.start}_to_${dateRange.end}.csv`;
    link.click();
  };

  if (loading || !stats) return (
    <div className="flex items-center justify-center h-[60vh]">
      <div className="w-12 h-12 border-4 border-accent border-t-transparent rounded-full animate-spin" />
    </div>
  );

  // Format data for charts with safety checks
  const trendData = (stats?.trend || []).map((item) => ({
    name: item.date,
    violations: item.count
  }));

  const pieData = Object.entries(stats?.by_type || {}).map(([key, value]) => ({
    name: key,
    value: value
  })).sort((a, b) => b.value - a.value);

  return (
    <div className="space-y-8 max-w-[1400px] mx-auto pb-12">
      <header className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Analytics & Reports</h2>
          <p className="text-muted mt-1">Detailed breakdown of traffic violations and trends</p>
        </div>
        <div className="flex gap-4">
          <button 
            onClick={() => {
              setPendingExportType('CSV');
              setShowRangeModal(true);
            }}
            className="flex items-center gap-2 px-6 py-2.5 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors text-sm font-bold"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
            Export CSV
          </button>
          <button 
            onClick={() => {
              setPendingExportType('PDF');
              setShowRangeModal(true);
            }}
            className="btn-primary px-6 py-2.5 rounded-2xl flex items-center gap-2 text-sm font-bold"
          >
            <Download className="w-4 h-4" />
            Export PDF Report
          </button>
        </div>
      </header>

      {/* Date Range Modal */}
      <AnimatePresence>
        {showRangeModal && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowRangeModal(false)}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            />
            <motion.div
              initial={{ scale: 0.95, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 20 }}
              className="relative w-full max-w-md glass p-8 rounded-[2.5rem] shadow-2xl border border-white/10"
            >
              <h3 className="text-2xl font-bold mb-2">Select Export Period</h3>
              <p className="text-muted text-sm mb-8">Choose the date range for your {pendingExportType} report.</p>
              
              <div className="space-y-6">
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-muted uppercase tracking-widest ml-1">Start Date</label>
                  <input 
                    type="date" 
                    value={dateRange.start}
                    onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                    className="w-full bg-white/5 border border-white/10 rounded-2xl px-5 py-4 text-sm outline-none focus:border-accent/50 transition-colors"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-muted uppercase tracking-widest ml-1">End Date</label>
                  <input 
                    type="date" 
                    value={dateRange.end}
                    onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                    className="w-full bg-white/5 border border-white/10 rounded-2xl px-5 py-4 text-sm outline-none focus:border-accent/50 transition-colors"
                  />
                </div>
              </div>

              <div className="mt-10 flex gap-4">
                <button 
                  onClick={() => setShowRangeModal(false)}
                  className="flex-1 py-4 rounded-2xl bg-white/5 hover:bg-white/10 font-bold transition-all text-sm"
                >
                  Cancel
                </button>
                <button 
                  onClick={handleExport}
                  disabled={isExporting}
                  className="flex-1 py-4 rounded-2xl bg-accent hover:bg-accent/90 shadow-lg shadow-accent/20 font-bold transition-all text-sm disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {isExporting ? (
                     <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                  ) : null}
                  {isExporting ? 'Generating...' : `Export ${pendingExportType}`}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard title="Daily Peak" value={`${trendData.reduce((max, p) => p.violations > max ? p.violations : max, 0)} Violations`} icon={TrendingUp} color="primary" trend={5} />
        <StatCard title="Most Common" value={pieData[0]?.name || "N/A"} icon={PieIcon} color="warning" />
        <StatCard title="Reporting Period" value="Last 7 Days" icon={Calendar} color="accent" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Main Trend Chart */}
        <div className="lg:col-span-8 glass p-8 rounded-[2.5rem] min-h-[450px]">
          <div className="flex justify-between items-center mb-10">
            <h3 className="text-xl font-bold">Violation Frequency</h3>
            <select className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm outline-none">
               <option>Last 7 Days</option>
            </select>
          </div>
          
          <div className="h-[350px] w-full min-h-[350px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="colorViolations" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                <XAxis 
                  dataKey="name" 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{fill: '#94a3b8', fontSize: 12}} 
                  dy={10}
                />
                <YAxis 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{fill: '#94a3b8', fontSize: 12}} 
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Area 
                  type="monotone" 
                  dataKey="violations" 
                  stroke="#3b82f6" 
                  strokeWidth={3}
                  fillOpacity={1} 
                  fill="url(#colorViolations)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Distribution Pie Chart */}
        <div className="lg:col-span-4 glass p-8 rounded-[2.5rem] flex flex-col justify-between">
          <h3 className="text-xl font-bold mb-6">Type Distribution</h3>
          
          <div className="h-[250px] w-full min-h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={8}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} cornerRadius={10} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="space-y-3 mt-6">
            {pieData.slice(0, 4).map((entry, index) => (
              <div key={entry.name} className="flex justify-between items-center p-3 rounded-2xl bg-white/5 border border-white/5">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
                  <span className="text-sm font-medium">{entry.name}</span>
                </div>
                <span className="text-sm font-bold">{entry.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* New Violation Records Table - "Document List" */}
      <div className="glass p-10 rounded-[2.5rem]">
        <div className="flex justify-between items-center mb-10">
          <div>
            <h3 className="text-2xl font-bold text-white/90">Violation Records</h3>
            <p className="text-muted text-sm mt-1">Full documentary list of recorded infractions</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="text-muted text-xs uppercase tracking-widest border-b border-white/5">
                <th className="pb-6 px-4">ID</th>
                <th className="pb-6 px-4">Vehicle Type</th>
                <th className="pb-6 px-4">Timestamp</th>
                <th className="pb-6 px-4">Stop Duration</th>
                <th className="pb-6 px-4">Status</th>
                <th className="pb-6 px-4">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {violations.map((v) => (
                <tr key={v.id} className="group hover:bg-white/[0.02] transition-colors">
                  <td className="py-6 px-4 text-sm font-medium text-muted">#{v.id}</td>
                  <td className="py-6 px-4">
                    <span className="capitalize font-bold text-white">{v.label}</span>
                  </td>
                  <td className="py-6 px-4 text-sm text-neutral-400">
                    {new Date(v.timestamp || v.violation_timestamp).toLocaleString()}
                  </td>
                  <td className="py-6 px-4 text-sm">
                    <span className="px-3 py-1 bg-accent/10 text-accent rounded-full font-bold">
                      {v.stop_duration}s
                    </span>
                  </td>
                  <td className="py-6 px-4 text-sm">
                    <span className="flex items-center gap-2">
                       <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-lg shadow-emerald-500/50" />
                       <span className="font-medium">Recorded</span>
                    </span>
                  </td>
                  <td className="py-6 px-4">
                    <button className="p-2 hover:bg-accent/10 rounded-xl transition-all group-hover:scale-110">
                      <Eye className="w-5 h-5 text-accent" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
