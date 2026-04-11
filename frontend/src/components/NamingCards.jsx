import { useState } from 'react';

const STYLE_BADGE = {
  'Modern Abstract': 'bg-cyan-500/15 text-cyan-300 border-cyan-500/25',
  'Portmanteau':     'bg-violet-500/15 text-violet-300 border-violet-500/25',
  'Real Word':       'bg-emerald-500/15 text-emerald-300 border-emerald-500/25',
  'Latin/Greek Root':'bg-amber-500/15 text-amber-300 border-amber-500/25',
};

function styleBadgeClass(style = '') {
  for (const [key, cls] of Object.entries(STYLE_BADGE)) {
    if (style.toLowerCase().includes(key.toLowerCase())) return cls;
  }
  return 'bg-white/10 text-white/60 border-white/15';
}

export default function NamingCards({ data }) {
  const [expanded, setExpanded] = useState(null);

  if (!data) return null;

  const recommended = data.brand_name;
  const candidates = Array.isArray(data.name_candidates) ? data.name_candidates : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-1">
        <h2 className="text-2xl font-black text-white uppercase tracking-tight">Brand Names</h2>
        <p className="text-white/40 text-sm">
          {candidates.length} candidates generated · Strategy: {data.naming_strategy || '—'}
        </p>
      </div>

      {/* Recommended hero */}
      <div className="relative rounded-2xl border border-blue-500/30 bg-gradient-to-br from-blue-500/10 to-cyan-500/5 p-7 overflow-hidden">
        <div className="absolute top-4 right-4 px-3 py-1 rounded-full bg-blue-500/20 border border-blue-400/30 text-blue-300 text-[10px] font-black uppercase tracking-widest">
          ★ Recommended
        </div>
        <div className="text-5xl font-black text-white tracking-tight">{recommended}</div>
        {data.tagline && (
          <div className="mt-3 text-lg text-white/60 font-medium italic">"{data.tagline}"</div>
        )}
        {data.brand_story_hook && (
          <p className="mt-4 text-sm text-white/50 leading-relaxed max-w-xl">{data.brand_story_hook}</p>
        )}
      </div>

      {/* Candidate grid */}
      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
        {candidates.map((c, i) => {
          const isExpanded = expanded === i;
          const isRecommended = c.name === recommended;
          return (
            <div
              key={i}
              className={`rounded-2xl border transition-all ${
                isRecommended
                  ? 'border-blue-400/30 bg-blue-500/5'
                  : 'border-white/10 bg-white/[0.03] hover:bg-white/[0.05]'
              }`}
            >
              <button
                className="w-full text-left p-5 space-y-3"
                onClick={() => setExpanded(isExpanded ? null : i)}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-xl font-black text-white">{c.name}</div>
                    {c.domain_suggestion && (
                      <div className="text-xs text-white/40 mt-1 font-mono">{c.domain_suggestion}</div>
                    )}
                  </div>
                  <div className="flex flex-col items-end gap-2 flex-shrink-0">
                    {isRecommended && (
                      <span className="text-yellow-400 text-lg">★</span>
                    )}
                    <span className="text-white/30 text-sm">{isExpanded ? '▲' : '▼'}</span>
                  </div>
                </div>

                {c.style && (
                  <span className={`inline-block px-3 py-1 rounded-full text-[10px] font-bold border ${styleBadgeClass(c.style)}`}>
                    {c.style}
                  </span>
                )}
              </button>

              {isExpanded && c.rationale && (
                <div className="px-5 pb-5 border-t border-white/5 pt-4 animate-fade-in">
                  <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30 mb-2">Rationale</div>
                  <p className="text-sm text-white/70 leading-relaxed">{c.rationale}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
