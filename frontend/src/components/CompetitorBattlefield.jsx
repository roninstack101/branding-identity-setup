import { useState } from 'react';

const THREAT = {
  low:    { color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', dot: 'bg-emerald-400', label: 'Low Threat' },
  medium: { color: 'text-amber-400',   bg: 'bg-amber-500/10',   border: 'border-amber-500/30',   dot: 'bg-amber-400',   label: 'Medium Threat' },
  high:   { color: 'text-red-400',     bg: 'bg-red-500/10',     border: 'border-red-500/30',     dot: 'bg-red-400',     label: 'High Threat' },
};

export default function CompetitorBattlefield({ data }) {
  const [selected, setSelected] = useState(0);

  if (!data) return null;

  const direct   = Array.isArray(data.direct_competitors)   ? data.direct_competitors   : [];
  const indirect = Array.isArray(data.indirect_competitors) ? data.indirect_competitors : [];
  const threat   = THREAT[data.threat_level] || THREAT.medium;
  const comp     = direct[selected];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-2xl font-black text-white uppercase tracking-tight">Competitive Battlefield</h2>
          <p className="text-white/40 text-sm mt-1">Real-time competitor intelligence</p>
        </div>
        <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${threat.bg} ${threat.border} border`}>
          <span className={`w-2 h-2 rounded-full ${threat.dot} animate-pulse`} />
          <span className={`${threat.color} font-bold text-sm`}>{threat.label}</span>
        </div>
      </div>

      {/* Main two-column layout */}
      <div className="grid lg:grid-cols-5 gap-4">
        {/* Left sidebar: list */}
        <div className="lg:col-span-2 space-y-2">
          {direct.length > 0 && (
            <>
              <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30 px-1 pb-1">
                Direct Competitors ({direct.length})
              </div>
              {direct.map((c, i) => (
                <button
                  key={i}
                  onClick={() => setSelected(i)}
                  className={`w-full text-left rounded-xl border p-4 transition-all ${
                    selected === i
                      ? 'bg-blue-500/15 border-blue-400/40'
                      : 'bg-white/[0.03] border-white/10 hover:bg-white/[0.06]'
                  }`}
                >
                  <div className="font-bold text-white text-sm">{c.name}</div>
                  {c.estimated_market_share && (
                    <div className="text-[11px] text-white/40 mt-1">{c.estimated_market_share}</div>
                  )}
                </button>
              ))}
            </>
          )}

          {indirect.length > 0 && (
            <div className="pt-3">
              <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30 px-1 pb-1">
                Indirect ({indirect.length})
              </div>
              {indirect.map((c, i) => (
                <div key={i} className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3 mb-2">
                  <div className="text-sm font-semibold text-white/60">{c.name}</div>
                  {c.description && <div className="text-[11px] text-white/35 mt-1 leading-relaxed">{c.description}</div>}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right: competitor detail */}
        <div className="lg:col-span-3 space-y-4">
          {comp ? (
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 space-y-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="text-xl font-black text-white">{comp.name}</h3>
                  {comp.description && (
                    <p className="text-sm text-white/50 mt-2 leading-relaxed">{comp.description}</p>
                  )}
                </div>
                {comp.website && (
                  <a
                    href={comp.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-shrink-0 text-xs px-3 py-1.5 rounded-full border border-white/10 text-white/50 hover:text-white hover:border-white/30 transition-all"
                  >
                    Visit ↗
                  </a>
                )}
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                {/* Strengths */}
                <div className="rounded-xl bg-emerald-500/5 border border-emerald-500/20 p-4 space-y-2">
                  <div className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-300 mb-3">Strengths</div>
                  {(comp.strengths || []).map((s, i) => (
                    <div key={i} className="flex gap-2 text-sm text-white/75">
                      <span className="text-emerald-400 mt-0.5 flex-shrink-0">✓</span>
                      <span>{s}</span>
                    </div>
                  ))}
                </div>

                {/* Weaknesses */}
                <div className="rounded-xl bg-red-500/5 border border-red-500/20 p-4 space-y-2">
                  <div className="text-[10px] font-black uppercase tracking-[0.2em] text-red-300 mb-3">
                    Weaknesses ← exploit
                  </div>
                  {(comp.weaknesses || []).map((w, i) => (
                    <div key={i} className="flex gap-2 text-sm text-white/75">
                      <span className="text-red-400 mt-0.5 flex-shrink-0">✗</span>
                      <span>{w}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Design Trends */}
              {comp.design_trends && (
                <div className="rounded-xl border border-violet-500/20 bg-violet-500/5 p-4 space-y-3">
                  <div className="text-[10px] font-black uppercase tracking-[0.2em] text-violet-300">
                    Design Identity
                  </div>
                  <div className="grid sm:grid-cols-2 gap-3">
                    {comp.design_trends.color_palette && (
                      <div className="space-y-0.5">
                        <div className="text-[10px] font-bold uppercase tracking-wider text-white/30">Colors</div>
                        <div className="text-xs text-white/70 leading-relaxed">{comp.design_trends.color_palette}</div>
                      </div>
                    )}
                    {comp.design_trends.typography_style && (
                      <div className="space-y-0.5">
                        <div className="text-[10px] font-bold uppercase tracking-wider text-white/30">Typography</div>
                        <div className="text-xs text-white/70 leading-relaxed">{comp.design_trends.typography_style}</div>
                      </div>
                    )}
                    {comp.design_trends.logo_style && (
                      <div className="space-y-0.5">
                        <div className="text-[10px] font-bold uppercase tracking-wider text-white/30">Logo Style</div>
                        <div className="text-xs text-white/70 leading-relaxed">{comp.design_trends.logo_style}</div>
                      </div>
                    )}
                    {comp.design_trends.visual_language && (
                      <div className="space-y-0.5">
                        <div className="text-[10px] font-bold uppercase tracking-wider text-white/30">Visual Language</div>
                        <div className="text-xs text-white/70 leading-relaxed">{comp.design_trends.visual_language}</div>
                      </div>
                    )}
                  </div>
                  {comp.design_trends.design_differentiation && (
                    <div className="pt-2 border-t border-violet-500/10">
                      <div className="text-[10px] font-bold uppercase tracking-wider text-white/30 mb-1">What makes it stand out / feel dated</div>
                      <div className="text-xs text-white/60 leading-relaxed italic">{comp.design_trends.design_differentiation}</div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-8 text-center text-white/30">
              Select a competitor to view details
            </div>
          )}

          {/* Positioning gaps */}
          {data.market_positioning_gaps?.length > 0 && (
            <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-5 space-y-2">
              <div className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-300 mb-3">Your Opening</div>
              {data.market_positioning_gaps.map((gap, i) => (
                <div key={i} className="flex gap-2 text-sm text-white/80">
                  <span className="text-cyan-400 flex-shrink-0">→</span>
                  <span>{gap}</span>
                </div>
              ))}
            </div>
          )}

          {data.recommended_positioning && (
            <div className="rounded-xl border border-blue-500/20 bg-blue-500/5 p-5">
              <div className="text-[10px] font-black uppercase tracking-[0.2em] text-blue-300 mb-2">Recommended Positioning</div>
              <p className="text-white/80 text-sm leading-relaxed">{data.recommended_positioning}</p>
            </div>
          )}
        </div>
      </div>

      {/* Competitive advantages */}
      {data.competitive_advantages?.length > 0 && (
        <div className="space-y-3">
          <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30">Your Competitive Advantages</div>
          <div className="grid md:grid-cols-3 gap-3">
            {data.competitive_advantages.map((adv, i) => (
              <div key={i} className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-sm text-white/80 leading-relaxed">
                <span className="text-blue-400 mr-2">⚡</span>{adv}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Industry Design Trends */}
      {data.industry_design_trends && (
        <div className="rounded-2xl border border-pink-500/20 bg-gradient-to-br from-pink-500/5 to-violet-500/5 p-5 space-y-4">
          <div className="flex items-center gap-2">
            <span className="text-lg">🎨</span>
            <div>
              <div className="text-sm font-black text-white uppercase tracking-tight">Industry Design Trends</div>
              <div className="text-[11px] text-white/40 mt-0.5">What the whole industry looks like — and where the visual white space is</div>
            </div>
          </div>
          <div className="grid sm:grid-cols-2 gap-4">
            {data.industry_design_trends.dominant_styles?.length > 0 && (
              <div className="space-y-1.5">
                <div className="text-[10px] font-black uppercase tracking-[0.2em] text-pink-300">Dominant Styles</div>
                {data.industry_design_trends.dominant_styles.map((s, i) => (
                  <div key={i} className="flex gap-2 text-xs text-white/70">
                    <span className="text-pink-400 flex-shrink-0">▸</span>
                    <span>{s}</span>
                  </div>
                ))}
              </div>
            )}
            {data.industry_design_trends.color_trends && (
              <div className="space-y-1.5">
                <div className="text-[10px] font-black uppercase tracking-[0.2em] text-pink-300">Color Trends</div>
                <p className="text-xs text-white/70 leading-relaxed">{data.industry_design_trends.color_trends}</p>
              </div>
            )}
            {data.industry_design_trends.typography_trends && (
              <div className="space-y-1.5">
                <div className="text-[10px] font-black uppercase tracking-[0.2em] text-pink-300">Typography Trends</div>
                <p className="text-xs text-white/70 leading-relaxed">{data.industry_design_trends.typography_trends}</p>
              </div>
            )}
            {data.industry_design_trends.design_white_space && (
              <div className="rounded-xl border border-cyan-500/25 bg-cyan-500/5 p-3 space-y-1.5">
                <div className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-300">Visual White Space ← Your Opportunity</div>
                <p className="text-xs text-white/80 leading-relaxed">{data.industry_design_trends.design_white_space}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
