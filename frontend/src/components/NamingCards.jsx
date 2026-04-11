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

export default function NamingCards({ data, originalName }) {
  const [expanded, setExpanded] = useState(null);
  const [usingOriginal, setUsingOriginal] = useState(false);

  if (!data) return null;

  const recommended = data.brand_name;
  const candidates  = Array.isArray(data.name_candidates) ? data.name_candidates : [];
  const activeName  = usingOriginal ? originalName : recommended;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-1">
        <h2 className="text-2xl font-black text-white uppercase tracking-tight">Brand Names</h2>
        <p className="text-white/40 text-sm">
          {candidates.length} candidates generated · Strategy: {data.naming_strategy || '—'}
        </p>
      </div>

      {/* Original name banner — only shown if user provided one */}
      {originalName && (
        <div className={`relative rounded-2xl border p-5 flex items-center justify-between gap-4 transition-all ${
          usingOriginal
            ? 'border-emerald-400/40 bg-emerald-500/10'
            : 'border-white/10 bg-white/[0.03]'
        }`}>
          <div className="flex items-center gap-4 min-w-0">
            <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-white/10 flex items-center justify-center text-lg">
              ✍️
            </div>
            <div className="min-w-0">
              <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40 mb-0.5">
                Your Original Name
              </div>
              <div className="text-2xl font-black text-white truncate">{originalName}</div>
            </div>
          </div>
          <button
            onClick={() => setUsingOriginal(!usingOriginal)}
            className={`flex-shrink-0 px-4 py-2 rounded-xl text-xs font-black transition-all border ${
              usingOriginal
                ? 'bg-emerald-500/20 border-emerald-400/40 text-emerald-300'
                : 'bg-white/5 border-white/10 text-white/50 hover:text-white hover:bg-white/10'
            }`}
          >
            {usingOriginal ? '✓ Using Original' : 'Use Original Name'}
          </button>
        </div>
      )}

      {/* Active name hero */}
      <div className={`relative rounded-2xl border p-7 overflow-hidden transition-all ${
        usingOriginal
          ? 'border-emerald-500/30 bg-gradient-to-br from-emerald-500/10 to-teal-500/5'
          : 'border-blue-500/30 bg-gradient-to-br from-blue-500/10 to-cyan-500/5'
      }`}>
        <div className={`absolute top-4 right-4 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border ${
          usingOriginal
            ? 'bg-emerald-500/20 border-emerald-400/30 text-emerald-300'
            : 'bg-blue-500/20 border-blue-400/30 text-blue-300'
        }`}>
          {usingOriginal ? '✍️ Your Name' : '★ Recommended'}
        </div>
        <div className="text-5xl font-black text-white tracking-tight">{activeName}</div>
        {!usingOriginal && data.tagline && (
          <div className="mt-3 text-lg text-white/60 font-medium italic">"{data.tagline}"</div>
        )}
        {!usingOriginal && data.brand_story_hook && (
          <p className="mt-4 text-sm text-white/50 leading-relaxed max-w-xl">{data.brand_story_hook}</p>
        )}
        {usingOriginal && (
          <p className="mt-3 text-sm text-white/50 leading-relaxed max-w-xl">
            Using your original brand name. The AI-recommended name and all candidates are still available below.
          </p>
        )}
      </div>

      {/* Candidate grid */}
      <div>
        <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30 mb-3">
          AI-Generated Candidates
        </div>
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
          {candidates.map((c, i) => {
            const isExpanded    = expanded === i;
            const isRecommended = c.name === recommended;
            return (
              <div
                key={i}
                className={`rounded-2xl border transition-all ${
                  isRecommended && !usingOriginal
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
    </div>
  );
}
