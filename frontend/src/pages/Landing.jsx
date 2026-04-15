import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Shield, Eye, Database, Activity, ArrowRight, Camera } from 'lucide-react';

const features = [
  { icon: Shield, title: 'AI-Powered Detection', desc: 'Real-time vehicle identification using YOLOv8 advanced computer vision.' },
  { icon: Eye, title: 'Zone Monitoring', desc: 'Automated monitoring of yellow box intersections for parking violations.' },
  { icon: Database, title: 'Secure Evidence', desc: 'Every violation is captured with cryptographic timestamps and HD images.' },
  { icon: Activity, title: 'Live Analytics', desc: 'Dynamic charts and reporting for traffic management authorities.' }
];

export function Landing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background relative overflow-hidden flex flex-col items-center justify-center -ml-64 w-screen px-8">
      {/* Background Glows */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-accent/20 blur-[120px] rounded-full" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-primary/20 blur-[120px] rounded-full" />

      <motion.div 
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-4xl text-center space-y-8 relative z-10"
      >
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-2xl bg-white/5 border border-white/10 backdrop-blur mb-6">
           <Camera className="w-4 h-4 text-accent" />
           <span className="text-xs font-bold uppercase tracking-[0.2em]">Deployment v2.4.0</span>
        </div>

        <h1 className="text-6xl md:text-8xl font-black tracking-tighter leading-tight">
          Smart <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent to-primary">Monitoring</span><br />
          For Safer Roads
        </h1>

        <p className="text-xl text-muted max-w-2xl mx-auto leading-relaxed">
          The Vehicle Yellow Box Zone Monitoring System leverages state-of-the-art AI 
           to automate traffic enforcement and ensure smooth transport operations.
        </p>

        <div className="flex flex-col md:flex-row gap-4 justify-center items-center pt-8">
          <button 
            onClick={() => navigate('/dashboard')}
            className="px-10 py-5 bg-accent hover:bg-accent/90 text-white rounded-[2rem] font-bold text-lg transition-all shadow-xl shadow-accent/20 flex items-center gap-3 group"
          >
            Launch Dashboard
            <ArrowRight className="group-hover:translate-x-1 transition-transform" />
          </button>
          <button className="px-10 py-5 bg-white/5 hover:bg-white/10 text-white border border-white/10 rounded-[2rem] font-bold text-lg transition-all backdrop-blur">
            System Documentation
          </button>
        </div>
      </motion.div>

      {/* Feature Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto mt-32 relative z-10">
        {features.map((f, i) => (
          <motion.div
            key={f.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 * i }}
            className="glass p-8 rounded-[2rem] hover:border-white/20 transition-colors group"
          >
            <div className="w-12 h-12 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center text-accent mb-6 group-hover:scale-110 transition-transform">
               <f.icon className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold mb-3">{f.title}</h3>
            <p className="text-sm text-muted leading-relaxed">{f.desc}</p>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
