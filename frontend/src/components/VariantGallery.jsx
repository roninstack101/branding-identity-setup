import { useState } from 'react';

// ── Archetype accent colors ───────────────────────────────────────────────────
// (populated via ARCHETYPE_MAP below)
const ARCHETYPE_MAP = [
  ['Interlocked Monogram', '#818cf8', 'rgba(129,140,248,0.22)', 'rgba(129,140,248,0.08)'],
  ['Ecosystem Orbit',      '#34d399', 'rgba(52,211,153,0.22)',  'rgba(52,211,153,0.08)' ],
  ['Growth Stack',         '#60a5fa', 'rgba(96,165,250,0.22)',  'rgba(96,165,250,0.08)' ],
  ['Bridge Arc',           '#fbbf24', 'rgba(251,191,36,0.22)',  'rgba(251,191,36,0.08)' ],
  ['Tri-form Overlap',     '#c084fc', 'rgba(192,132,252,0.22)', 'rgba(192,132,252,0.08)'],
  ['Network Nodes',        '#38bdf8', 'rgba(56,189,248,0.22)',  'rgba(56,189,248,0.08)' ],
  ['Dynamic Sweep',        '#fb923c', 'rgba(251,146,60,0.22)',  'rgba(251,146,60,0.08)' ],
  ['Digital Grid',         '#a3e635', 'rgba(163,230,53,0.22)',  'rgba(163,230,53,0.08)' ],
  ['Globe',                '#2dd4bf', 'rgba(45,212,191,0.22)',  'rgba(45,212,191,0.08)' ],
  ['Journey Swoosh',       '#f472b6', 'rgba(244,114,182,0.22)', 'rgba(244,114,182,0.08)'],
];

function getArchStyle(approach = '') {
  const lower = approach.toLowerCase();
  for (const [key, color, border, bg] of ARCHETYPE_MAP) {
    if (lower.includes(key.toLowerCase().split('/')[0].trim())) return { color, border, bg };
  }
  return { color: '#94a3b8', border: 'rgba(148,163,184,0.2)', bg: 'rgba(148,163,184,0.06)' };
}

// ── Download SVG ──────────────────────────────────────────────────────────────
function downloadSVG(svg, filename) {
  const blob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ── SVG Concept Card ──────────────────────────────────────────────────────────
function ConceptCard({ concept, onClick }) {
  const style   = getArchStyle(concept.approach || '');
  const hasSVG  = Boolean(concept.svg) && !concept.svg.includes('SVG pending');
  const filename = `concept-${concept.number}-${(concept.name || '').toLowerCase().replace(/\s+/g, '-')}.svg`;

  return (
    <div
      className="rounded-2xl border overflow-hidden flex flex-col transition-all hover:scale-[1.01]"
      style={{ borderColor: style.border, background: 'rgba(255,255,255,0.015)' }}
    >
      {/* SVG preview — click to open full-screen */}
      <button
        onClick={() => onClick(concept)}
        className="w-full bg-white overflow-hidden flex items-center justify-center"
        style={{ aspectRatio: '1 / 1' }}
        title="Click to expand"
      >
        {concept.svg ? (
          <div
            className="w-full h-full"
            dangerouslySetInnerHTML={{ __html: concept.svg }}
            style={{ lineHeight: 0 }}
          />
        ) : (
          <div className="text-black/20 text-xs">Generating…</div>
        )}
      </button>

      {/* Card footer */}
      <div className="p-3 space-y-2" style={{ background: style.bg }}>
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <div className="text-sm font-black leading-tight truncate" style={{ color: style.color }}>
              {concept.number}. {concept.name}
            </div>
            <div className="text-[10px] text-white/40 mt-0.5 truncate">{concept.approach}</div>
          </div>

          {hasSVG && (
            <button
              onClick={(e) => { e.stopPropagation(); downloadSVG(concept.svg, filename); }}
              className="flex-shrink-0 flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all hover:opacity-90"
              style={{ background: style.border, color: style.color }}
              title="Download SVG"
            >
              ↓ SVG
            </button>
          )}
        </div>

        {concept.rationale && (
          <p className="text-[10px] text-white/40 leading-snug line-clamp-2">{concept.rationale}</p>
        )}
      </div>
    </div>
  );
}

// ── Full-screen concept modal ─────────────────────────────────────────────────
function ConceptModal({ concept, onClose, primaryColor, accentColor }) {
  const style    = getArchStyle(concept.approach || '');
  const hasSVG   = Boolean(concept.svg) && !concept.svg.includes('SVG pending');
  const filename = `concept-${concept.number}-${(concept.name || '').toLowerCase().replace(/\s+/g, '-')}.svg`;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-2xl bg-slate-950 border border-white/10 rounded-3xl shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white/60 hover:text-white transition-all"
        >✕</button>

        {/* SVG full preview */}
        <div className="bg-white w-full">
          {concept.svg ? (
            <div
              className="w-full"
              dangerouslySetInnerHTML={{ __html: concept.svg }}
              style={{ lineHeight: 0 }}
            />
          ) : (
            <div className="h-64 flex items-center justify-center text-black/20 text-sm">No SVG</div>
          )}
        </div>

        {/* Details */}
        <div className="p-6 space-y-4">
          {/* Header */}
          <div className="flex items-start justify-between gap-3">
            <div>
              <div
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold mb-2"
                style={{ background: style.bg, border: `1px solid ${style.border}`, color: style.color }}
              >
                Concept {concept.number} — {concept.approach}
              </div>
              <h2 className="text-xl font-black text-white">{concept.name}</h2>
            </div>
            {hasSVG && (
              <button
                onClick={() => downloadSVG(concept.svg, filename)}
                className="flex-shrink-0 flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all"
                style={{ background: style.border, color: style.color }}
              >
                ↓ Download SVG
              </button>
            )}
          </div>

          {/* Rationale */}
          {concept.rationale && (
            <div
              className="rounded-xl px-4 py-3"
              style={{ background: style.bg, border: `1px solid ${style.border}` }}
            >
              <div className="text-[9px] font-black uppercase tracking-[0.2em] mb-1" style={{ color: style.color }}>
                Design Rationale
              </div>
              <p className="text-sm text-white/65 leading-relaxed">{concept.rationale}</p>
            </div>
          )}

          {/* Color tokens */}
          {(primaryColor || accentColor) && (
            <div className="flex gap-3">
              {primaryColor && (
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-white/8 bg-white/[0.02]">
                  <div className="w-4 h-4 rounded-full border border-white/20" style={{ backgroundColor: primaryColor }} />
                  <span className="text-[11px] font-mono text-white/50">{primaryColor}</span>
                </div>
              )}
              {accentColor && (
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-white/8 bg-white/[0.02]">
                  <div className="w-4 h-4 rounded-full border border-white/20" style={{ backgroundColor: accentColor }} />
                  <span className="text-[11px] font-mono text-white/50">{accentColor}</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Design Brief panel ────────────────────────────────────────────────────────
function DesignBriefPanel({ briefText, competitorNotes, primaryColor, accentColor, font }) {
  const [open, setOpen] = useState(false);
  if (!briefText) return null;

  const renderBrief = (text) =>
    text.split('\n').map((line, i) => {
      if (line.match(/^━+/) || line.match(/^#{1,3}\s/)) {
        const title = line.replace(/^[━#\s]+/, '').trim();
        return title ? (
          <div key={i} className="text-[10px] font-black uppercase tracking-[0.18em] text-white/35 mt-5 mb-2 pt-3 border-t border-white/5">
            {title}
          </div>
        ) : null;
      }
      if (line.startsWith('•') || line.startsWith('-') || line.match(/^\d+\./)) {
        return <div key={i} className="text-[11px] text-white/45 leading-relaxed pl-3">{line}</div>;
      }
      if (!line.trim()) return <div key={i} className="h-1.5" />;
      return <div key={i} className="text-[11px] text-white/50 leading-relaxed">{line}</div>;
    });

  return (
    <div className="rounded-2xl border border-white/8 overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-white/[0.02] transition-colors"
        style={{ background: 'rgba(255,255,255,0.015)' }}
      >
        <div className="flex items-center gap-3">
          <span className="text-base">📋</span>
          <div>
            <div className="text-sm font-black text-white/80">Full Design Brief</div>
            <div className="text-[10px] text-white/30 mt-0.5">Gemini research + 10-concept strategy</div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex gap-2">
            {primaryColor && (
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full border border-white/20" style={{ backgroundColor: primaryColor }} />
                <span className="text-[9px] font-mono text-white/25">{primaryColor}</span>
              </div>
            )}
            {accentColor && (
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full border border-white/20" style={{ backgroundColor: accentColor }} />
                <span className="text-[9px] font-mono text-white/25">{accentColor}</span>
              </div>
            )}
            {font && <span className="text-[9px] text-white/25">{font}</span>}
          </div>
          <span className="text-white/25 text-xs">{open ? '▲' : '▼'}</span>
        </div>
      </button>

      {open && (
        <div className="px-5 pb-5 space-y-1">
          {competitorNotes && (
            <div className="my-3 p-3 rounded-xl bg-amber-500/5 border border-amber-500/15">
              <div className="text-[9px] font-black uppercase tracking-[0.2em] text-amber-400/60 mb-1">Competitor Visual Research</div>
              <p className="text-[11px] text-amber-100/50 leading-relaxed">{competitorNotes}</p>
            </div>
          )}
          <div>{renderBrief(briefText)}</div>
        </div>
      )}
    </div>
  );
}

// ── Download all as individual files ─────────────────────────────────────────
function downloadAll(concepts, brandName) {
  concepts.forEach((c, i) => {
    if (!c.svg) return;
    setTimeout(() => {
      const name = `${brandName.toLowerCase().replace(/\s+/g, '-')}-concept-${c.number}-${(c.name || '').toLowerCase().replace(/\s+/g, '-')}.svg`;
      downloadSVG(c.svg, name);
    }, i * 200); // stagger downloads 200ms apart
  });
}

// ── Main Export ───────────────────────────────────────────────────────────────
export default function VariantGallery({ data, onRegenerate }) {
  const [selected, setSelected] = useState(null);

  if (!data) return null;

  const concepts       = Array.isArray(data.design_concepts) ? data.design_concepts : [];
  const briefText      = data.logo_design_brief   || '';
  const primaryColor   = data.primary_color       || '';
  const accentColor    = data.accent_color        || '';
  const font           = data.font                || '';
  const compNotes      = data.competitor_visual_notes || '';

  const hasSVGs = concepts.some((c) => c.svg && !c.svg.includes('SVG pending'));

  if (concepts.length === 0 && !briefText) {
    return (
      <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-8 text-center space-y-3">
        <div className="text-3xl opacity-40">⚠️</div>
        <div className="text-white/60 font-bold">Visual Identity data is empty</div>
        <div className="text-white/35 text-sm leading-relaxed max-w-md mx-auto">
          Check that <span className="text-amber-300/80">GEMINI_API_KEY</span> is set in the backend{' '}
          <code className="bg-white/10 px-1 rounded">.env</code> (must start with <code className="bg-white/10 px-1 rounded">AIza</code>).
        </div>
        {onRegenerate && (
          <button
            onClick={() => onRegenerate('visual_identity_agent', 'regenerate visual identity')}
            className="mt-2 px-5 py-2 rounded-xl bg-white/5 border border-white/15 text-white/60 hover:text-white hover:bg-white/10 text-sm font-bold transition-all"
          >
            Retry
          </button>
        )}
      </div>
    );
  }

  const svgCount = concepts.filter((c) => c.svg && !c.svg.includes('SVG pending')).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-2xl font-black text-white uppercase tracking-tight">Logo Concepts</h2>
          <p className="text-white/40 text-sm mt-1">
            {concepts.length} visual directions · {svgCount} SVGs ready ·{' '}
            Researched by Gemini, rendered as scalable vector
          </p>
        </div>
        <div className="flex gap-2 flex-wrap">
          {hasSVGs && (
            <button
              onClick={() => downloadAll(concepts.filter((c) => c.svg), data.design_style || 'brand')}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 text-white/70 hover:text-white transition-all text-sm font-semibold"
            >
              ↓ Download All SVGs
            </button>
          )}
          {onRegenerate && (
            <button
              onClick={() => onRegenerate('visual_identity_agent', 'regenerate logo concepts with fresh visual directions')}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 text-white/70 hover:text-white transition-all text-sm font-semibold"
            >
              Regenerate
            </button>
          )}
        </div>
      </div>

      {/* Info callout */}
      <div className="flex items-start gap-3 p-4 rounded-2xl bg-indigo-500/5 border border-indigo-500/15">
        <span className="text-indigo-400 text-lg flex-shrink-0">✦</span>
        <div className="text-xs text-white/45 leading-relaxed">
          <span className="text-indigo-300 font-bold">Gemini</span> researched your competitors online and generated
          10 distinct logo concepts. Each is a <span className="text-emerald-300 font-bold">self-contained SVG</span> file
          — scalable to any size, editable in Figma / Illustrator, ready for your designer to refine.
          Click any concept to expand, then download.
        </div>
      </div>

      {/* Design tokens */}
      {(primaryColor || accentColor || font) && (
        <div className="flex flex-wrap gap-3 items-center">
          {primaryColor && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-white/8 bg-white/[0.02]">
              <div className="w-4 h-4 rounded-full border border-white/20" style={{ backgroundColor: primaryColor }} />
              <span className="text-[11px] font-mono text-white/50">{primaryColor}</span>
              <span className="text-[10px] text-white/25">Primary</span>
            </div>
          )}
          {accentColor && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-white/8 bg-white/[0.02]">
              <div className="w-4 h-4 rounded-full border border-white/20" style={{ backgroundColor: accentColor }} />
              <span className="text-[11px] font-mono text-white/50">{accentColor}</span>
              <span className="text-[10px] text-white/25">Accent</span>
            </div>
          )}
          {font && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-white/8 bg-white/[0.02]">
              <span className="text-[11px] text-white/50">Aa</span>
              <span className="text-[11px] text-white/50">{font}</span>
            </div>
          )}
        </div>
      )}

      {/* SVG Grid — 2 cols on mobile, 3 on md, 5 on xl */}
      {concepts.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">
          {concepts.map((c) => (
            <ConceptCard key={c.number} concept={c} onClick={setSelected} />
          ))}
        </div>
      )}

      {/* Design Brief */}
      <DesignBriefPanel
        briefText={briefText}
        competitorNotes={compNotes}
        primaryColor={primaryColor}
        accentColor={accentColor}
        font={font}
      />

      {/* Concept modal */}
      {selected && (
        <ConceptModal
          concept={selected}
          primaryColor={primaryColor}
          accentColor={accentColor}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}
