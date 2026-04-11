export default function MarketResearchView({ data }) {
  if (!data) return null;

  const trends      = Array.isArray(data.market_trends)      ? data.market_trends      : [];
  const gaps        = Array.isArray(data.market_gaps)        ? data.market_gaps        : [];
  const drivers     = Array.isArray(data.growth_drivers)     ? data.growth_drivers     : [];
  const sources     = Array.isArray(data.key_sources)        ? data.key_sources        : [];
  const competitors = Array.isArray(data.competitor_landscape) ? data.competitor_landscape : [];
  const demo        = data.target_demographics || {};
  const psycho      = Array.isArray(demo.psychographics)     ? demo.psychographics     : [];
  const behavior    = Array.isArray(demo.behavior_patterns)  ? demo.behavior_patterns  : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-black text-white uppercase tracking-tight">Market Research</h2>
        <p className="text-white/40 text-sm mt-1">Real-time market intelligence via Gemini + Google Search</p>
      </div>

      {/* Market size hero */}
      {data.market_size && (
        <div className="rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-emerald-500/10 to-teal-500/5 p-7">
          <div className="text-[10px] font-black uppercase tracking-[0.25em] text-emerald-300/70 mb-2">Total Addressable Market</div>
          <div className="text-2xl font-black text-white leading-snug">{data.market_size}</div>
        </div>
      )}

      {/* Trends + Gaps + Drivers */}
      <div className="grid md:grid-cols-3 gap-4">
        {trends.length > 0 && (
          <div className="rounded-xl border border-blue-500/15 bg-blue-500/5 p-5 space-y-3">
            <div className="text-[10px] font-black uppercase tracking-[0.2em] text-blue-300/70">Market Trends</div>
            {trends.map((t, i) => (
              <div key={i} className="flex gap-2 text-sm text-white/75">
                <span className="text-blue-400 flex-shrink-0">↑</span>{t}
              </div>
            ))}
          </div>
        )}
        {gaps.length > 0 && (
          <div className="rounded-xl border border-amber-500/15 bg-amber-500/5 p-5 space-y-3">
            <div className="text-[10px] font-black uppercase tracking-[0.2em] text-amber-300/70">Market Gaps</div>
            {gaps.map((g, i) => (
              <div key={i} className="flex gap-2 text-sm text-white/75">
                <span className="text-amber-400 flex-shrink-0">◆</span>{g}
              </div>
            ))}
          </div>
        )}
        {drivers.length > 0 && (
          <div className="rounded-xl border border-emerald-500/15 bg-emerald-500/5 p-5 space-y-3">
            <div className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-300/70">Growth Drivers</div>
            {drivers.map((d, i) => (
              <div key={i} className="flex gap-2 text-sm text-white/75">
                <span className="text-emerald-400 flex-shrink-0">⚡</span>{d}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Target demographics */}
      {(demo.primary_segment || psycho.length > 0 || behavior.length > 0) && (
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 space-y-4">
          <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40">Target Demographics</div>
          {demo.primary_segment && (
            <p className="text-white/80 text-sm leading-relaxed">{demo.primary_segment}</p>
          )}
          <div className="grid md:grid-cols-2 gap-4">
            {psycho.length > 0 && (
              <div className="space-y-2">
                <div className="text-[10px] font-black uppercase tracking-[0.18em] text-cyan-300/60">Psychographics</div>
                <div className="flex flex-wrap gap-2">
                  {psycho.map((p, i) => (
                    <span key={i} className="px-2.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-200 text-xs">
                      {p}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {behavior.length > 0 && (
              <div className="space-y-2">
                <div className="text-[10px] font-black uppercase tracking-[0.18em] text-violet-300/60">Behaviour Patterns</div>
                <div className="flex flex-wrap gap-2">
                  {behavior.map((b, i) => (
                    <span key={i} className="px-2.5 py-1 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-200 text-xs">
                      {b}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Competitor landscape */}
      {competitors.length > 0 && (
        <div className="space-y-3">
          <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30">Competitor Landscape</div>
          <div className="grid md:grid-cols-2 gap-3">
            {competitors.map((c, i) => (
              <div key={i} className="rounded-xl border border-white/10 bg-white/[0.03] p-4 space-y-2">
                <div className="flex items-center justify-between gap-3">
                  <div className="font-bold text-white text-sm">{c.name}</div>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${
                    c.market_share_vibe?.toLowerCase().includes('leader')
                      ? 'bg-red-500/15 text-red-300 border-red-500/25'
                      : c.market_share_vibe?.toLowerCase().includes('challenger')
                      ? 'bg-amber-500/15 text-amber-300 border-amber-500/25'
                      : 'bg-white/10 text-white/50 border-white/15'
                  }`}>
                    {c.market_share_vibe || 'Niche'}
                  </span>
                </div>
                {c.strength  && <div className="text-xs text-white/55"><span className="text-emerald-400">✓</span> {c.strength}</div>}
                {c.weakness  && <div className="text-xs text-white/55"><span className="text-red-400">✗</span> {c.weakness}</div>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sources */}
      {sources.length > 0 && (
        <details className="rounded-xl border border-white/10 bg-white/[0.02]">
          <summary className="px-5 py-3 cursor-pointer text-[11px] font-black uppercase tracking-[0.2em] text-white/30 hover:text-white/50 transition-colors">
            {sources.length} Key Sources
          </summary>
          <div className="px-5 pb-4 flex flex-col gap-2">
            {sources.map((s, i) => (
              <div key={i} className="text-xs text-white/50 flex gap-2">
                <span className="text-white/20">{i + 1}.</span>{s}
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
