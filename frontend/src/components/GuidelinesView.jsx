import { useState } from 'react';

// ── Rule number accent colors ─────────────────────────────────────────────────
const RULE_COLORS = [
  ['#818cf8', 'rgba(129,140,248,0.15)', 'rgba(129,140,248,0.08)'],
  ['#34d399', 'rgba(52,211,153,0.15)',  'rgba(52,211,153,0.08)' ],
  ['#60a5fa', 'rgba(96,165,250,0.15)',  'rgba(96,165,250,0.08)' ],
  ['#fbbf24', 'rgba(251,191,36,0.15)',  'rgba(251,191,36,0.08)' ],
  ['#c084fc', 'rgba(192,132,252,0.15)', 'rgba(192,132,252,0.08)'],
  ['#fb923c', 'rgba(251,146,60,0.15)',  'rgba(251,146,60,0.08)' ],
];

function hexToRgb(hex) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `${r}, ${g}, ${b}`;
}

// ── Section wrapper ───────────────────────────────────────────────────────────
function Section({ title, icon, children }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-base">{icon}</span>
        <h3 className="text-sm font-black text-white/80 uppercase tracking-[0.12em]">{title}</h3>
      </div>
      {children}
    </div>
  );
}

// ── Tab: Brand Foundation ─────────────────────────────────────────────────────
function FoundationTab({ data }) {
  const overview = data.brand_overview || {};
  const values   = Array.isArray(overview.values) ? overview.values : [];
  return (
    <div className="space-y-4">
      {overview.mission && (
        <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-5">
          <div className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-300/70 mb-2">Mission</div>
          <p className="text-white/90 text-base font-medium leading-relaxed">{overview.mission}</p>
        </div>
      )}
      {overview.vision && (
        <div className="rounded-2xl border border-indigo-500/20 bg-indigo-500/5 p-5">
          <div className="text-[10px] font-black uppercase tracking-[0.2em] text-indigo-300/70 mb-2">Vision</div>
          <p className="text-white/90 text-base font-medium leading-relaxed">{overview.vision}</p>
        </div>
      )}
      {values.length > 0 && (
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 space-y-3">
          <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/35">Core Values</div>
          <div className="flex flex-wrap gap-2">
            {values.map((v, i) => (
              <span key={i} className="px-3 py-1.5 rounded-full border border-violet-400/25 bg-violet-400/8 text-violet-200 text-xs font-bold">
                {v}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Tab: Brand Rules ──────────────────────────────────────────────────────────
function RulesTab({ data }) {
  const rules = Array.isArray(data.brand_rules) ? data.brand_rules : [];
  if (rules.length === 0)
    return <p className="text-white/30 text-sm">No brand rules generated yet.</p>;

  return (
    <div className="space-y-3">
      {rules.map((r, i) => {
        const [color, border, bg] = RULE_COLORS[i % RULE_COLORS.length];
        return (
          <div key={i} className="rounded-2xl border overflow-hidden"
            style={{ borderColor: border, background: bg }}>
            <div className="flex items-start gap-4 p-5">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center text-sm font-black flex-shrink-0"
                style={{ background: border, color }}>
                {r.rule_number || i + 1}
              </div>
              <div className="flex-1 min-w-0 space-y-1">
                <div className="font-black text-white/90" style={{ color }}>{r.rule}</div>
                <p className="text-white/70 text-sm leading-relaxed">{r.description}</p>
                {r.why && (
                  <div className="flex gap-2 mt-2 pt-2 border-t border-white/5">
                    <span className="text-[9px] font-black uppercase tracking-[0.15em] text-white/25 flex-shrink-0 mt-0.5">Why →</span>
                    <p className="text-[11px] text-white/40 leading-relaxed italic">{r.why}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Tab: Colour System ────────────────────────────────────────────────────────
function ColorsTab({ data }) {
  const cg       = data.color_guidelines  || {};
  const rationale = data.color_rationale  || {};
  const primary  = Array.isArray(cg.primary_colors)   ? cg.primary_colors   : [];
  const secondary = Array.isArray(cg.secondary_colors) ? cg.secondary_colors : [];
  const combos   = Array.isArray(cg.color_combinations) ? cg.color_combinations : [];

  return (
    <div className="space-y-6">
      {/* Primary colours */}
      {primary.length > 0 && (
        <Section title="Primary Colours" icon="🎨">
          <div className="grid sm:grid-cols-2 gap-3">
            {primary.map((c, i) => (
              <div key={i} className="rounded-xl overflow-hidden border border-white/8">
                <div className="h-14 w-full" style={{ backgroundColor: c.hex || '#334155' }} />
                <div className="p-3 space-y-0.5 bg-white/[0.03]">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-black text-white/85">{c.name}</span>
                    <span className="text-[10px] font-mono text-white/45">{c.hex}</span>
                  </div>
                  <div className="text-[9px] text-white/30">RGB: {c.rgb || hexToRgb(c.hex || '#000000')}</div>
                  {c.usage && <p className="text-[10px] text-white/45 leading-snug mt-1">{c.usage}</p>}
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Secondary colours */}
      {secondary.length > 0 && (
        <Section title="Secondary Colours" icon="🖌️">
          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-3">
            {secondary.map((c, i) => (
              <div key={i} className="rounded-xl overflow-hidden border border-white/8">
                <div className="h-10 w-full" style={{ backgroundColor: c.hex || '#334155' }} />
                <div className="p-2.5 space-y-0.5 bg-white/[0.03]">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold text-white/80">{c.name}</span>
                    <span className="text-[9px] font-mono text-white/40">{c.hex}</span>
                  </div>
                  {c.usage && <p className="text-[9px] text-white/35 leading-snug">{c.usage}</p>}
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Rationale */}
      {(rationale.primary_reasoning || rationale.accent_reasoning || rationale.palette_harmony) && (
        <Section title="Why These Colours" icon="💡">
          <div className="space-y-3">
            {rationale.primary_reasoning && (
              <div className="rounded-xl border border-white/8 bg-white/[0.02] p-4">
                <div className="text-[9px] font-black uppercase tracking-[0.18em] text-amber-300/60 mb-1.5">Primary Colour Reasoning</div>
                <p className="text-sm text-white/65 leading-relaxed">{rationale.primary_reasoning}</p>
              </div>
            )}
            {rationale.accent_reasoning && (
              <div className="rounded-xl border border-white/8 bg-white/[0.02] p-4">
                <div className="text-[9px] font-black uppercase tracking-[0.18em] text-amber-300/60 mb-1.5">Accent Colour Reasoning</div>
                <p className="text-sm text-white/65 leading-relaxed">{rationale.accent_reasoning}</p>
              </div>
            )}
            {rationale.palette_harmony && (
              <div className="rounded-xl border border-white/8 bg-white/[0.02] p-4">
                <div className="text-[9px] font-black uppercase tracking-[0.18em] text-amber-300/60 mb-1.5">Palette Harmony</div>
                <p className="text-sm text-white/65 leading-relaxed">{rationale.palette_harmony}</p>
              </div>
            )}
          </div>
        </Section>
      )}

      {/* Safe combos */}
      {combos.length > 0 && (
        <Section title="Safe Colour Pairings" icon="✓">
          <div className="space-y-1.5">
            {combos.map((combo, i) => (
              <div key={i} className="flex items-center gap-2 text-[11px] text-white/55">
                <span className="text-emerald-400">✓</span>{combo}
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}

// ── Tab: Typography ───────────────────────────────────────────────────────────
function TypographyTab({ data }) {
  const tg        = data.typography_guidelines || {};
  const rationale = data.typography_rationale  || {};
  const hierarchy = tg.hierarchy               || {};

  return (
    <div className="space-y-6">
      {/* Typefaces */}
      {(tg.primary_typeface || tg.secondary_typeface) && (
        <Section title="Typefaces" icon="Aa">
          <div className="grid sm:grid-cols-2 gap-4">
            {tg.primary_typeface && (
              <div className="rounded-xl border border-indigo-400/20 bg-indigo-400/5 p-4">
                <div className="text-[9px] font-black uppercase tracking-[0.18em] text-indigo-300/60 mb-1">Heading / Display</div>
                <div className="text-lg font-black text-white/90">{tg.primary_typeface}</div>
              </div>
            )}
            {tg.secondary_typeface && (
              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <div className="text-[9px] font-black uppercase tracking-[0.18em] text-white/35 mb-1">Body / UI</div>
                <div className="text-lg font-medium text-white/80">{tg.secondary_typeface}</div>
              </div>
            )}
          </div>
        </Section>
      )}

      {/* Hierarchy */}
      {Object.keys(hierarchy).length > 0 && (
        <Section title="Typographic Scale" icon="↕">
          <div className="rounded-xl border border-white/8 bg-white/[0.02] p-4 space-y-2">
            {Object.entries(hierarchy).map(([level, spec]) => (
              <div key={level} className="flex items-baseline gap-3 py-1 border-b border-white/5 last:border-0">
                <span className="text-[9px] font-black uppercase tracking-[0.2em] text-white/30 w-10 flex-shrink-0">{level}</span>
                <span className="text-[11px] text-white/60 font-mono">{spec}</span>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Rationale */}
      {(rationale.heading_font_reason || rationale.body_font_reason || rationale.combination_logic) && (
        <Section title="Why These Fonts" icon="💡">
          <div className="space-y-3">
            {rationale.heading_font_reason && (
              <div className="rounded-xl border border-white/8 bg-white/[0.02] p-4">
                <div className="text-[9px] font-black uppercase tracking-[0.18em] text-indigo-300/60 mb-1.5">Heading Font — Why It Fits</div>
                <p className="text-sm text-white/65 leading-relaxed">{rationale.heading_font_reason}</p>
              </div>
            )}
            {rationale.body_font_reason && (
              <div className="rounded-xl border border-white/8 bg-white/[0.02] p-4">
                <div className="text-[9px] font-black uppercase tracking-[0.18em] text-indigo-300/60 mb-1.5">Body Font — Why It Fits</div>
                <p className="text-sm text-white/65 leading-relaxed">{rationale.body_font_reason}</p>
              </div>
            )}
            {rationale.combination_logic && (
              <div className="rounded-xl border border-white/8 bg-white/[0.02] p-4">
                <div className="text-[9px] font-black uppercase tracking-[0.18em] text-indigo-300/60 mb-1.5">Why They Work Together</div>
                <p className="text-sm text-white/65 leading-relaxed">{rationale.combination_logic}</p>
              </div>
            )}
          </div>
        </Section>
      )}
    </div>
  );
}

// ── Tab: Voice & Tone ─────────────────────────────────────────────────────────
function VoiceTab({ data }) {
  const vt = data.voice_and_tone || {};
  const dos    = Array.isArray(vt.dos)             ? vt.dos             : [];
  const donts  = Array.isArray(vt.donts)           ? vt.donts           : [];
  const phrases = Array.isArray(vt.example_phrases) ? vt.example_phrases : [];

  return (
    <div className="space-y-4">
      {vt.personality && (
        <div className="rounded-2xl border border-amber-400/20 bg-amber-400/5 p-5">
          <div className="text-[10px] font-black uppercase tracking-[0.2em] text-amber-300/70 mb-2">Brand Personality</div>
          <p className="text-white/85 leading-relaxed">{vt.personality}</p>
        </div>
      )}
      <div className="grid md:grid-cols-2 gap-4">
        {dos.length > 0 && (
          <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 space-y-2">
            <div className="text-[10px] font-black uppercase tracking-[0.18em] text-emerald-300/70">Do</div>
            {dos.map((d, i) => (
              <div key={i} className="flex gap-2 text-sm text-white/70">
                <span className="text-emerald-400 flex-shrink-0">✓</span>{d}
              </div>
            ))}
          </div>
        )}
        {donts.length > 0 && (
          <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4 space-y-2">
            <div className="text-[10px] font-black uppercase tracking-[0.18em] text-red-300/70">Don't</div>
            {donts.map((d, i) => (
              <div key={i} className="flex gap-2 text-sm text-white/65">
                <span className="text-red-400 flex-shrink-0">✕</span>{d}
              </div>
            ))}
          </div>
        )}
      </div>
      {phrases.length > 0 && (
        <div className="rounded-xl border border-white/8 bg-white/[0.02] p-4 space-y-2">
          <div className="text-[9px] font-black uppercase tracking-[0.18em] text-white/30">Example Phrases</div>
          {phrases.map((ph, i) => (
            <p key={i} className="text-sm text-white/65 italic border-l-2 border-white/10 pl-3">"{ph}"</p>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Tab: Application ──────────────────────────────────────────────────────────
function ApplicationTab({ data }) {
  const logo   = data.logo_usage         || {};
  const img    = data.imagery_guidelines || {};
  const digi   = data.digital_guidelines || {};
  const donts  = Array.isArray(logo.dont_rules) ? logo.dont_rules : [];

  return (
    <div className="space-y-6">
      {(logo.primary_usage || logo.minimum_size || logo.clear_space) && (
        <Section title="Logo Usage" icon="◻">
          <div className="rounded-xl border border-white/8 bg-white/[0.02] p-4 space-y-3">
            {logo.primary_usage  && <p className="text-sm text-white/70 leading-relaxed">{logo.primary_usage}</p>}
            <div className="flex gap-6 flex-wrap">
              {logo.minimum_size && (
                <div>
                  <div className="text-[9px] text-white/30 uppercase tracking-widest mb-0.5">Min Size</div>
                  <div className="text-xs font-bold text-white/65">{logo.minimum_size}</div>
                </div>
              )}
              {logo.clear_space && (
                <div>
                  <div className="text-[9px] text-white/30 uppercase tracking-widest mb-0.5">Clear Space</div>
                  <div className="text-xs font-bold text-white/65">{logo.clear_space}</div>
                </div>
              )}
            </div>
            {donts.length > 0 && (
              <div className="pt-2 border-t border-white/5 space-y-1">
                {donts.map((d, i) => (
                  <div key={i} className="flex gap-2 text-[11px] text-white/50">
                    <span className="text-red-400 flex-shrink-0">✕</span>{d}
                  </div>
                ))}
              </div>
            )}
          </div>
        </Section>
      )}

      {(img.photography_style || img.illustration_style || img.icon_style) && (
        <Section title="Imagery" icon="🖼">
          <div className="grid sm:grid-cols-3 gap-3">
            {[['Photography', img.photography_style], ['Illustration', img.illustration_style], ['Icons', img.icon_style]]
              .filter(([, v]) => v)
              .map(([label, val]) => (
                <div key={label} className="rounded-xl border border-white/8 bg-white/[0.02] p-3">
                  <div className="text-[9px] font-black uppercase tracking-[0.18em] text-white/30 mb-1">{label}</div>
                  <p className="text-[11px] text-white/60 leading-snug">{val}</p>
                </div>
              ))}
          </div>
        </Section>
      )}

      {(digi.website_style || digi.social_media || digi.email) && (
        <Section title="Digital" icon="💻">
          <div className="space-y-2">
            {[['Website / UI', digi.website_style], ['Social Media', digi.social_media], ['Email', digi.email]]
              .filter(([, v]) => v)
              .map(([label, val]) => (
                <div key={label} className="rounded-xl border border-white/8 bg-white/[0.02] p-3 flex gap-3">
                  <span className="text-[9px] font-black uppercase tracking-[0.18em] text-white/30 flex-shrink-0 mt-0.5 w-20">{label}</span>
                  <p className="text-[11px] text-white/60 leading-snug">{val}</p>
                </div>
              ))}
          </div>
        </Section>
      )}
    </div>
  );
}

// ── Main Export ───────────────────────────────────────────────────────────────
export default function GuidelinesView({ data }) {
  const [tab, setTab] = useState('foundation');

  if (!data) return null;

  const rules = Array.isArray(data.brand_rules) ? data.brand_rules : [];

  const tabs = [
    { key: 'foundation', label: 'Mission & Vision' },
    { key: 'rules',      label: `Brand Rules (${rules.length})` },
    { key: 'colors',     label: 'Colour System' },
    { key: 'typography', label: 'Typography' },
    { key: 'voice',      label: 'Voice & Tone' },
    { key: 'application', label: 'Application' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <h2 className="text-2xl font-black text-white uppercase tracking-tight">Brand Guidelines</h2>
          <span className="px-2 py-0.5 rounded-full bg-white/8 border border-white/10 text-[9px] font-black text-white/35 uppercase tracking-widest">
            v{data.guidelines_version || '1.0'}
          </span>
        </div>
        <p className="text-white/40 text-sm">The rulebook for your brand's visual and verbal identity</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 flex-wrap">
        {tabs.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`px-4 py-2 rounded-full text-[11px] font-black uppercase tracking-[0.12em] border transition-all ${
              tab === t.key
                ? 'bg-violet-500/20 border-violet-400/40 text-violet-200'
                : 'bg-white/5 border-white/10 text-white/50 hover:text-white/70'
            }`}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'foundation'   && <FoundationTab   data={data} />}
      {tab === 'rules'        && <RulesTab        data={data} />}
      {tab === 'colors'       && <ColorsTab       data={data} />}
      {tab === 'typography'   && <TypographyTab   data={data} />}
      {tab === 'voice'        && <VoiceTab        data={data} />}
      {tab === 'application'  && <ApplicationTab  data={data} />}
    </div>
  );
}
