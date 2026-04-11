export default function BrandStrategyView({ data }) {
  if (!data) return null;

  const personality = data.brand_personality || {};
  const segments    = Array.isArray(data.target_segments) ? data.target_segments : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-black text-white uppercase tracking-tight">Brand Strategy</h2>
        <p className="text-white/40 text-sm mt-1">The soul and competitive foundation of the brand</p>
      </div>

      {/* Archetype hero */}
      {personality.archetype && (
        <div className="rounded-2xl border border-blue-500/20 bg-gradient-to-br from-blue-500/10 to-indigo-500/5 p-7 flex flex-col md:flex-row items-start gap-6">
          <div className="w-20 h-20 rounded-2xl bg-blue-500/20 border border-blue-400/30 flex items-center justify-center text-4xl flex-shrink-0">
            🎭
          </div>
          <div className="space-y-2">
            <div className="text-[10px] font-black uppercase tracking-[0.25em] text-blue-300/70">Brand Archetype</div>
            <div className="text-3xl font-black text-white">{personality.archetype}</div>
            {personality.tone_of_voice && (
              <div className="text-white/60 text-sm font-medium italic">"{personality.tone_of_voice}"</div>
            )}
            {Array.isArray(personality.traits) && personality.traits.length > 0 && (
              <div className="flex flex-wrap gap-2 pt-2">
                {personality.traits.map((t, i) => (
                  <span key={i} className="px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-200 text-xs font-semibold">
                    {t}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Mission / Vision / Promise */}
      <div className="grid md:grid-cols-3 gap-4">
        {[
          { label: 'Mission', value: data.brand_mission, accent: 'border-cyan-500/20 bg-cyan-500/5 text-cyan-300/70' },
          { label: 'Vision', value: data.brand_vision, accent: 'border-violet-500/20 bg-violet-500/5 text-violet-300/70' },
          { label: 'Brand Promise', value: data.brand_promise, accent: 'border-amber-500/20 bg-amber-500/5 text-amber-300/70' },
        ].filter((c) => c.value).map((card) => (
          <div key={card.label} className={`rounded-2xl border p-5 space-y-2 ${card.accent}`}>
            <div className="text-[10px] font-black uppercase tracking-[0.2em]">{card.label}</div>
            <p className="text-white/85 text-sm leading-relaxed">{card.value}</p>
          </div>
        ))}
      </div>

      {/* USP */}
      {data.unique_selling_proposition && (
        <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-6">
          <div className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-300/70 mb-2">Unique Selling Proposition</div>
          <p className="text-white/90 text-lg leading-relaxed font-medium">{data.unique_selling_proposition}</p>
        </div>
      )}

      {/* Positioning statement */}
      {data.positioning_statement && (
        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5">
          <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40 mb-2">Positioning Statement</div>
          <p className="text-white/75 text-sm leading-relaxed italic">{data.positioning_statement}</p>
        </div>
      )}

      {/* Values */}
      {Array.isArray(data.brand_values) && data.brand_values.length > 0 && (
        <div className="space-y-3">
          <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30">Brand Values</div>
          <div className="flex flex-wrap gap-3">
            {data.brand_values.map((v, i) => (
              <span key={i} className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white/80 font-semibold text-sm">
                {v}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Benefits */}
      <div className="grid md:grid-cols-2 gap-4">
        {data.emotional_benefits?.length > 0 && (
          <div className="rounded-xl border border-rose-500/15 bg-rose-500/5 p-5 space-y-2">
            <div className="text-[10px] font-black uppercase tracking-[0.2em] text-rose-300/70 mb-3">Emotional Benefits</div>
            {data.emotional_benefits.map((b, i) => (
              <div key={i} className="flex gap-2 text-sm text-white/75">
                <span className="text-rose-400 flex-shrink-0">♥</span>{b}
              </div>
            ))}
          </div>
        )}
        {data.functional_benefits?.length > 0 && (
          <div className="rounded-xl border border-sky-500/15 bg-sky-500/5 p-5 space-y-2">
            <div className="text-[10px] font-black uppercase tracking-[0.2em] text-sky-300/70 mb-3">Functional Benefits</div>
            {data.functional_benefits.map((b, i) => (
              <div key={i} className="flex gap-2 text-sm text-white/75">
                <span className="text-sky-400 flex-shrink-0">⚙</span>{b}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Target segments */}
      {segments.length > 0 && (
        <div className="space-y-3">
          <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30">Target Segments</div>
          <div className="grid md:grid-cols-2 gap-4">
            {segments.map((seg, i) => (
              <div key={i} className="rounded-xl border border-white/10 bg-white/[0.03] p-5 space-y-2">
                <div className="flex items-center justify-between gap-3">
                  <div className="font-bold text-white">{seg.segment_name}</div>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${
                    seg.priority === 'primary'
                      ? 'bg-blue-500/20 text-blue-300 border-blue-500/30'
                      : 'bg-white/10 text-white/50 border-white/15'
                  }`}>
                    {seg.priority}
                  </span>
                </div>
                <p className="text-sm text-white/60 leading-relaxed">{seg.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
