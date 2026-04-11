const COLOR_STYLES = [
  {
    node: 'from-blue-500 to-indigo-500',
    ring: 'ring-blue-300/40',
    line: 'from-blue-400 to-indigo-400',
    text: 'text-blue-200',
    glow: 'shadow-blue-500/35',
  },
  {
    node: 'from-fuchsia-500 to-violet-500',
    ring: 'ring-fuchsia-300/40',
    line: 'from-fuchsia-400 to-violet-400',
    text: 'text-fuchsia-200',
    glow: 'shadow-fuchsia-500/35',
  },
  {
    node: 'from-pink-500 to-rose-500',
    ring: 'ring-pink-300/40',
    line: 'from-pink-400 to-rose-400',
    text: 'text-pink-200',
    glow: 'shadow-pink-500/35',
  },
  {
    node: 'from-orange-500 to-red-500',
    ring: 'ring-orange-300/40',
    line: 'from-orange-400 to-red-400',
    text: 'text-orange-200',
    glow: 'shadow-orange-500/35',
  },
  {
    node: 'from-amber-500 to-orange-500',
    ring: 'ring-amber-300/40',
    line: 'from-amber-400 to-orange-400',
    text: 'text-amber-200',
    glow: 'shadow-amber-500/35',
  },
  {
    node: 'from-emerald-500 to-teal-500',
    ring: 'ring-emerald-300/40',
    line: 'from-emerald-400 to-teal-400',
    text: 'text-emerald-200',
    glow: 'shadow-emerald-500/35',
  },
  {
    node: 'from-cyan-500 to-sky-500',
    ring: 'ring-cyan-300/40',
    line: 'from-cyan-400 to-sky-400',
    text: 'text-cyan-200',
    glow: 'shadow-cyan-500/35',
  },
  {
    node: 'from-indigo-500 to-blue-600',
    ring: 'ring-indigo-300/40',
    line: 'from-indigo-400 to-blue-400',
    text: 'text-indigo-200',
    glow: 'shadow-indigo-500/35',
  },
  {
    node: 'from-slate-500 to-slate-700',
    ring: 'ring-slate-300/40',
    line: 'from-slate-400 to-slate-500',
    text: 'text-slate-200',
    glow: 'shadow-slate-500/35',
  },
];

export default function ProgressTimeline({ agents, labels, completed, expandedAgent, onExpandAgent }) {
  return (
    <div className="rounded-3xl border border-cyan-500/10 bg-slate-950/50 p-5 md:p-6 backdrop-blur-xl">
      <div className="flex items-center justify-between gap-4 mb-5">
        <div>
          <div className="text-[10px] uppercase font-black tracking-[0.22em] text-cyan-300/60">Pipeline Navigator</div>
          <div className="text-sm text-white/55 mt-1">Click any step dot to jump to that agent output.</div>
        </div>
        <div className="text-xs text-white/45 font-semibold">
          {completed.length} / {agents.length} completed
        </div>
      </div>

      <div className="overflow-x-auto -mx-2 px-2 pb-2">
        <div className="flex items-start gap-2 min-w-max">
          {agents.map((agentName, index) => {
            const isDone = completed.includes(agentName);
            const isActive = expandedAgent === agentName;
            const isLast = index === agents.length - 1;
            const meta = labels[agentName] || { icon: '•', label: agentName };
            const style = COLOR_STYLES[index % COLOR_STYLES.length];

            return (
              <div key={agentName} className="flex items-start gap-2">
                <button
                  onClick={() => onExpandAgent(expandedAgent === agentName ? null : agentName)}
                  className="group text-left flex-shrink-0 w-[126px]"
                  title={meta.label}
                >
                  <div className="relative flex justify-center mb-2">
                    {isDone && (
                      <div className={`absolute inset-0 m-auto w-16 h-16 rounded-full blur-xl opacity-55 ${style.glow}`} />
                    )}
                    <div
                      className={`relative z-10 w-14 h-14 rounded-full flex items-center justify-center text-lg font-bold border transition-all duration-300 ${
                        isDone
                          ? `bg-gradient-to-br ${style.node} text-white border-white/25 shadow-xl ${style.glow}`
                          : 'bg-slate-900 text-white/35 border-white/10 group-hover:bg-slate-800 group-hover:text-white/70'
                      } ${isActive ? `ring-4 ${style.ring}` : ''}`}
                    >
                      {meta.icon}
                    </div>
                    {isDone && <span className="absolute -right-1 -top-1 text-[11px]">✅</span>}
                  </div>

                  <div className="text-center">
                    <div className={`text-[11px] font-black uppercase tracking-[0.18em] ${isDone ? style.text : 'text-white/30'}`}>
                      Step {index + 1}
                    </div>
                    <div className={`text-xs leading-tight font-semibold mt-1 ${isDone ? 'text-white' : 'text-white/45'}`}>
                      {meta.label}
                    </div>
                    <div className="text-[10px] mt-1 text-white/30">
                      {isDone ? 'Completed' : 'Pending'}
                    </div>
                  </div>
                </button>

                {!isLast && (
                  <div className="w-10 pt-6 flex-shrink-0">
                    <div
                      className={`h-1.5 rounded-full transition-all duration-500 ${
                        isDone
                          ? `bg-gradient-to-r ${style.line} shadow-lg ${style.glow}`
                          : 'bg-white/10'
                      }`}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
