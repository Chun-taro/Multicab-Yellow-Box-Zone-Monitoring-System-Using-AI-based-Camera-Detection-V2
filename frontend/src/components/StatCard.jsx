import { motion } from 'framer-motion';

export function StatCard({ title, value, icon: Icon, trend, color = "accent" }) {
  const colorMap = {
    accent: "text-accent bg-accent/10 border-accent/20",
    primary: "text-primary bg-primary/10 border-primary/20",
    danger: "text-red-400 bg-red-400/10 border-red-400/20",
    warning: "text-amber-400 bg-amber-400/10 border-amber-400/20",
    success: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass p-4 rounded-2xl flex flex-col gap-2 overflow-hidden group hover:border-white/20 transition-colors relative"
    >
      <div className="flex justify-between items-center">
        <div className={`p-2 rounded-xl border ${colorMap[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
        {trend && (
          <div className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${trend > 0 ? 'bg-emerald-400/10 text-emerald-400' : 'bg-red-400/10 text-red-400'}`}>
            {trend > 0 ? '+' : ''}{trend}%
          </div>
        )}
      </div>
      <div>
        <p className="text-muted text-[10px] uppercase tracking-wider font-bold">{title}</p>
        <h3 className="text-2xl font-black mt-0.5 tracking-tight">{value}</h3>
      </div>
      
      {/* Subtle background decoration */}
      <div className="absolute -bottom-6 -right-6 opacity-[0.03] group-hover:scale-110 transition-transform duration-500">
        <Icon className="w-24 h-24" />
      </div>
    </motion.div>
  );
}
