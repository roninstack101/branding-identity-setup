import { useState, useRef, useEffect } from 'react';

// ── Archetype accent colors ───────────────────────────────────────────────────
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

// ── Color helpers (for palette generator) ────────────────────────────────────
function hslToHex(h, s, l) {
  s /= 100; l /= 100;
  const a = s * Math.min(l, 1 - l);
  const f = (n) => {
    const k = (n + h / 30) % 12;
    const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
    return Math.round(255 * color).toString(16).padStart(2, '0');
  };
  return `#${f(0)}${f(8)}${f(4)}`;
}

function generateHarmony() {
  const base = Math.random() * 360;
  const s    = 50 + Math.random() * 30;
  // 5 hues: triad + split complementary pattern
  const offsets = [0, 25, 170, 195, 330];
  const lights   = [40, 55, 45, 60, 38];
  return offsets.map((off, i) => hslToHex((base + off) % 360, s, lights[i]));
}

function isValidHex(str) {
  return /^#[0-9a-fA-F]{6}$/.test(str);
}

// Returns white or dark depending on the bg color luminance
function contrastColor(hex) {
  if (!isValidHex(hex)) return 'rgba(255,255,255,0.75)';
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  const lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return lum > 0.55 ? 'rgba(0,0,0,0.65)' : 'rgba(255,255,255,0.85)';
}

function contrastOverlay(hex) {
  if (!isValidHex(hex)) return 'rgba(0,0,0,0.18)';
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  const lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return lum > 0.55 ? 'rgba(0,0,0,0.12)' : 'rgba(0,0,0,0.22)';
}

// ── SVG → data URL ────────────────────────────────────────────────────────────
function svgToDataUrl(svg) {
  if (!svg) return '';
  try {
    let s = svg.includes('xmlns=') ? svg : svg.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"');
    const wMatch = s.match(/width="(\d+)"/);
    const hMatch = s.match(/height="(\d+)"/);
    if (wMatch && hMatch && !s.includes('viewBox')) {
      s = s.replace('<svg', `<svg viewBox="0 0 ${wMatch[1]} ${hMatch[1]}"`);
    }
    return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(s)}`;
  } catch {
    return '';
  }
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
  const style    = getArchStyle(concept.approach || '');
  const hasSVG   = Boolean(concept.svg) && !concept.svg.includes('SVG pending');
  const filename = `concept-${concept.number}-${(concept.name || '').toLowerCase().replace(/\s+/g, '-')}.svg`;

  return (
    <div
      className="rounded-2xl border overflow-hidden flex flex-col transition-all hover:scale-[1.01] cursor-pointer"
      style={{ borderColor: style.border, background: 'rgba(255,255,255,0.015)' }}
      onClick={() => onClick(concept)}
    >
      {/* SVG preview — padding-top trick for reliable 1:1 aspect ratio */}
      <div className="relative w-full bg-white" style={{ paddingTop: '100%' }}>
        <div className="absolute inset-0 flex items-center justify-center overflow-hidden">
          {concept.svg ? (
            <img
              src={svgToDataUrl(concept.svg)}
              alt={concept.name}
              className="w-full h-full object-contain"
              onError={(e) => { e.target.style.display = 'none'; }}
            />
          ) : (
            <div className="flex flex-col items-center justify-center gap-1">
              <div className="text-3xl opacity-15">◻</div>
              <div className="text-black/20 text-xs">No SVG</div>
            </div>
          )}
        </div>
      </div>

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
              onClick={(e) => { e.stopPropagation(); e.preventDefault(); downloadSVG(concept.svg, filename); }}
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

// ── Color version configs for modal tabs ─────────────────────────────────────
const COLOR_VERSIONS = [
  { label: 'Full Colour', bg: '#ffffff', imgFilter: 'none',                        dark: false },
  { label: 'Monochrome',  bg: '#ffffff', imgFilter: 'grayscale(1) contrast(1.15)', dark: false },
  { label: 'Dark',        bg: '#0f172a', imgFilter: 'invert(1)',                   dark: true  },
];

// ── Full-screen concept modal ─────────────────────────────────────────────────
function ConceptModal({ concept, onClose }) {
  const [versionIdx, setVersionIdx] = useState(0);
  const style    = getArchStyle(concept.approach || '');
  const hasSVG   = Boolean(concept.svg) && !concept.svg.includes('SVG pending');
  const filename = `concept-${concept.number}-${(concept.name || '').toLowerCase().replace(/\s+/g, '-')}.svg`;
  const ver      = COLOR_VERSIONS[versionIdx];

  // Concept-level palette (from AI) or empty
  const palette = Array.isArray(concept.palette) ? concept.palette.filter(Boolean) : [];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-2xl bg-slate-950 border border-white/10 rounded-3xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white/60 hover:text-white transition-all"
        >✕</button>

        {/* Version tabs */}
        <div className="flex gap-1 px-5 pt-5 pb-3 flex-shrink-0">
          {COLOR_VERSIONS.map((v, i) => (
            <button
              key={v.label}
              onClick={() => setVersionIdx(i)}
              className="px-3 py-1.5 rounded-lg text-[11px] font-bold transition-all border"
              style={
                i === versionIdx
                  ? { background: style.border, borderColor: style.color, color: style.color }
                  : { background: 'rgba(255,255,255,0.03)', borderColor: 'rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.4)' }
              }
            >
              {v.label}
            </button>
          ))}
          <div className="flex-1" />
          {hasSVG && (
            <button
              onClick={() => downloadSVG(concept.svg, filename)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-bold transition-all"
              style={{ background: style.border, color: style.color }}
            >
              ↓ SVG
            </button>
          )}
        </div>

        {/* SVG preview */}
        <div className="w-full transition-colors duration-200 flex-shrink-0" style={{ backgroundColor: ver.bg }}>
          {concept.svg ? (
            <img
              src={svgToDataUrl(concept.svg)}
              alt={concept.name}
              className="w-full"
              style={{ filter: ver.imgFilter, transition: 'filter 0.2s' }}
            />
          ) : (
            <div className="h-48 flex items-center justify-center text-black/20 text-sm">No SVG generated</div>
          )}
        </div>

        {/* Details — scrollable */}
        <div className="p-5 space-y-4 overflow-y-auto">
          {/* Header */}
          <div>
            <div
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold mb-2"
              style={{ background: style.bg, border: `1px solid ${style.border}`, color: style.color }}
            >
              Concept {concept.number} — {concept.approach}
            </div>
            <h2 className="text-xl font-black text-white">{concept.name}</h2>
            {concept.typography && (
              <div className="text-[10px] text-white/30 mt-0.5">Typography: {concept.typography}</div>
            )}
          </div>

          {/* Direction */}
          {concept.direction && (
            <div className="rounded-xl px-4 py-3 bg-white/[0.02] border border-white/6">
              <div className="text-[9px] font-black uppercase tracking-[0.2em] mb-1 text-white/30">Design Direction</div>
              <p className="text-sm text-white/60 leading-relaxed">{concept.direction}</p>
            </div>
          )}

          {/* Rationale */}
          {concept.rationale && (
            <div
              className="rounded-xl px-4 py-3"
              style={{ background: style.bg, border: `1px solid ${style.border}` }}
            >
              <div className="text-[9px] font-black uppercase tracking-[0.2em] mb-1" style={{ color: style.color }}>
                Creative Rationale
              </div>
              <p className="text-sm text-white/65 leading-relaxed">{concept.rationale}</p>
            </div>
          )}

          {/* Concept palette */}
          {palette.length > 0 && (
            <div className="space-y-1.5">
              <div className="text-[9px] font-black uppercase tracking-[0.2em] text-white/30">Colour Palette</div>
              <div className="flex gap-2 flex-wrap">
                {palette.map((hex, i) => (
                  <div key={i} className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-white/8 bg-white/[0.02]">
                    <div className="w-3.5 h-3.5 rounded-full border border-white/20" style={{ backgroundColor: hex }} />
                    <span className="text-[10px] font-mono text-white/50">{hex}</span>
                  </div>
                ))}
              </div>
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

// ── Coolors-style color palette ───────────────────────────────────────────────
function ColorSwatch({ hex, locked, index, onColorChange, onToggleLock }) {
  const inputRef  = useRef(null);
  const textRef   = useRef(null);
  const [hovered, setHovered] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draft,   setDraft]   = useState(hex.toUpperCase());
  const [copied,  setCopied]  = useState(false);

  // Keep draft in sync when hex changes externally
  useEffect(() => { if (!editing) setDraft(hex.toUpperCase()); }, [hex, editing]);

  const fg      = contrastColor(hex);
  const overlay = contrastOverlay(hex);

  const copyHex = (e) => {
    e.stopPropagation();
    navigator.clipboard?.writeText(hex.toUpperCase()).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 1400);
  };

  const commitDraft = () => {
    setEditing(false);
    const val = draft.startsWith('#') ? draft : `#${draft}`;
    if (isValidHex(val)) onColorChange(index, val.toLowerCase());
    else setDraft(hex.toUpperCase());
  };

  return (
    <div
      className="relative flex-1 flex flex-col justify-between select-none transition-all duration-150"
      style={{ backgroundColor: hex, minWidth: 0 }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Native color picker — triggered programmatically */}
      <input
        ref={inputRef}
        type="color"
        value={hex}
        onChange={(e) => { onColorChange(index, e.target.value); }}
        className="absolute opacity-0 pointer-events-none w-0 h-0"
        tabIndex={-1}
      />

      {/* Top row: copy + lock */}
      <div
        className="flex justify-between items-center p-2 transition-opacity duration-150"
        style={{ opacity: hovered || locked ? 1 : 0 }}
      >
        {/* Copy */}
        <button
          onClick={copyHex}
          className="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold transition-all hover:scale-110"
          style={{ background: overlay, color: fg }}
          title="Copy hex"
        >
          {copied ? '✓' : '⎘'}
        </button>
        {/* Lock */}
        <button
          onClick={(e) => { e.stopPropagation(); onToggleLock(index); }}
          className="w-7 h-7 rounded-lg flex items-center justify-center text-xs transition-all hover:scale-110"
          style={{ background: overlay, color: fg }}
          title={locked ? 'Unlock color' : 'Lock color'}
        >
          {locked ? '🔒' : '🔓'}
        </button>
      </div>

      {/* Center: pencil icon on hover */}
      <div
        className="flex-1 flex items-center justify-center cursor-pointer transition-opacity duration-150"
        style={{ opacity: hovered ? 1 : 0 }}
        onClick={() => inputRef.current?.click()}
        title="Edit color"
      >
        <div
          className="w-9 h-9 rounded-full flex items-center justify-center text-base transition-transform hover:scale-110"
          style={{ background: overlay, color: fg }}
        >
          ✎
        </div>
      </div>

      {/* Bottom: hex label / inline edit */}
      <div className="pb-3 pt-1 px-1 flex flex-col items-center gap-1">
        {editing ? (
          <input
            ref={textRef}
            value={draft}
            maxLength={7}
            onChange={(e) => setDraft(e.target.value.toUpperCase())}
            onBlur={commitDraft}
            onKeyDown={(e) => { if (e.key === 'Enter') commitDraft(); if (e.key === 'Escape') { setEditing(false); setDraft(hex.toUpperCase()); } }}
            className="w-full text-center text-[11px] font-mono font-bold bg-black/20 rounded px-1 py-0.5 focus:outline-none focus:ring-1 focus:ring-white/40"
            style={{ color: fg }}
            onClick={(e) => e.stopPropagation()}
          />
        ) : (
          <button
            className="text-[11px] font-mono font-bold tracking-wider px-1 py-0.5 rounded transition-all hover:bg-black/10"
            style={{ color: fg }}
            onClick={(e) => { e.stopPropagation(); setEditing(true); setTimeout(() => textRef.current?.select(), 30); }}
            title="Edit hex"
          >
            {hex.toUpperCase()}
          </button>
        )}
      </div>
    </div>
  );
}

function ColorPalettePanel({ palette, locked, onColorChange, onToggleLock, onNewPalette }) {
  return (
    <div className="space-y-2">
      {/* Strips */}
      <div
        className="flex rounded-2xl overflow-hidden border border-white/10"
        style={{ height: '200px', gap: '2px' }}
      >
        {palette.map((hex, i) => (
          <ColorSwatch
            key={i}
            hex={hex}
            locked={locked[i]}
            index={i}
            onColorChange={onColorChange}
            onToggleLock={onToggleLock}
          />
        ))}
      </div>

      {/* Shuffle + hint */}
      <div className="flex items-center justify-between">
        <p className="text-[9px] text-white/25">
          Click ✎ to pick · click hex to type · 🔒 to keep on shuffle
        </p>
        <button
          onClick={onNewPalette}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 text-white/60 hover:text-white text-[10px] font-bold transition-all"
        >
          ⟳ Generate New
        </button>
      </div>
    </div>
  );
}

// ── Regenerate Panel (chat + directions + colors) ─────────────────────────────
function RegeneratePanel({ onRegenerate, seedColors }) {
  const [palette, setPalette] = useState(() => {
    // Try to seed from AI-chosen colors, filling the rest with harmony
    const harmony = generateHarmony();
    const seeds   = (seedColors || []).filter(isValidHex);
    return harmony.map((c, i) => seeds[i] || c);
  });
  const [locked,    setLocked]    = useState([false, false, false, false, false]);
  const [chat,      setChat]      = useState('');
  const [selected,  setSelected]  = useState([]);
  const [loading,   setLoading]   = useState(false);

  const toggleLock  = (i) => setLocked((l) => l.map((v, idx) => idx === i ? !v : v));
  const updateColor = (i, hex) => setPalette((p) => p.map((v, idx) => idx === i ? hex : v));
  const newPalette  = () => {
    const fresh = generateHarmony();
    setPalette((p) => p.map((v, i) => locked[i] ? v : fresh[i]));
  };

  const toggleDir = (name) =>
    setSelected((d) => d.includes(name) ? d.filter((n) => n !== name) : [...d, name]);

  const handleRegenerate = async () => {
    if (!onRegenerate) return;
    setLoading(true);
    try {
      const parts = [];
      if (chat.trim()) parts.push(`User instructions: ${chat.trim()}.`);
      if (selected.length > 0) parts.push(`Focus on these design directions: ${selected.join(', ')}.`);
      parts.push(`Use this color palette: ${palette.join(', ')}.`);
      await onRegenerate('visual_identity_agent', parts.join(' '));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-2xl border border-white/8 overflow-hidden" style={{ background: 'rgba(255,255,255,0.012)' }}>
      {/* Header */}
      <div className="px-5 py-4 border-b border-white/6">
        <div className="flex items-center gap-2.5">
          <span className="text-base">🎨</span>
          <div>
            <div className="text-sm font-black text-white/85">Customize & Regenerate</div>
            <div className="text-[10px] text-white/30 mt-0.5">Set your colors, pick design directions, and give the AI instructions</div>
          </div>
        </div>
      </div>

      <div className="p-5 space-y-6">
        {/* Color palette */}
        <div className="space-y-2">
          <div className="text-[10px] font-black uppercase tracking-[0.15em] text-white/35">Color Palette</div>
          <ColorPalettePanel
            palette={palette}
            locked={locked}
            onColorChange={updateColor}
            onToggleLock={toggleLock}
            onNewPalette={newPalette}
          />
        </div>

        {/* Design direction chips */}
        <div className="space-y-2">
          <div className="text-[10px] font-black uppercase tracking-[0.15em] text-white/35">
            Design Direction
            <span className="ml-2 text-white/20 normal-case font-normal tracking-normal">
              {selected.length === 0 ? '— all styles (leave blank for variety)' : `— ${selected.length} selected`}
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {ARCHETYPE_MAP.map(([name, color, border, bg]) => {
              const active = selected.includes(name);
              return (
                <button
                  key={name}
                  onClick={() => toggleDir(name)}
                  className="px-3 py-1.5 rounded-full text-[10px] font-bold border transition-all"
                  style={
                    active
                      ? { background: border, borderColor: color, color }
                      : { background: bg, borderColor: border, color: 'rgba(255,255,255,0.35)' }
                  }
                >
                  {name}
                </button>
              );
            })}
          </div>
        </div>

        {/* Chat / instruction box */}
        <div className="space-y-2">
          <div className="text-[10px] font-black uppercase tracking-[0.15em] text-white/35">Instructions for AI</div>
          <textarea
            value={chat}
            onChange={(e) => setChat(e.target.value)}
            placeholder="Describe what you want to change…&#10;e.g. Make it feel more premium and minimal, avoid circles, use geometric letterforms"
            rows={3}
            className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-sm text-white/80 placeholder-white/20 focus:outline-none focus:border-white/25 focus:bg-white/[0.05] transition-all resize-none leading-relaxed"
          />
        </div>

        {/* Regenerate CTA */}
        <div className="flex items-center justify-between gap-4 pt-1">
          <p className="text-[10px] text-white/25 leading-relaxed max-w-xs">
            AI will use your colors &amp; instructions to regenerate all 10 logo concepts
          </p>
          <button
            onClick={handleRegenerate}
            disabled={loading || !onRegenerate}
            className="flex-shrink-0 flex items-center gap-2 px-6 py-2.5 rounded-xl font-black text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              background: loading ? 'rgba(99,102,241,0.3)' : 'rgba(99,102,241,0.85)',
              color: '#fff',
              boxShadow: loading ? 'none' : '0 0 20px rgba(99,102,241,0.35)',
            }}
          >
            {loading ? (
              <>
                <span className="inline-block w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Generating…
              </>
            ) : (
              <>✦ Regenerate Logos</>
            )}
          </button>
        </div>
      </div>
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
    }, i * 200);
  });
}

// ── Main Export ───────────────────────────────────────────────────────────────
export default function VariantGallery({ data, onRegenerate }) {
  const [selected, setSelected] = useState(null);

  if (!data) return null;

  const concepts     = Array.isArray(data.design_concepts) ? data.design_concepts : [];
  const briefText    = data.logo_design_brief        || '';
  const primaryColor = data.primary_color            || '';
  const accentColor  = data.accent_color             || '';
  const font         = data.font                     || '';
  const compNotes    = data.competitor_visual_notes  || '';

  // Seed colors from AI output for the palette panel
  const seedColors = [primaryColor, accentColor].filter(Boolean);

  const hasSVGs   = concepts.some((c) => c.svg && !c.svg.includes('SVG pending'));
  const svgCount  = concepts.filter((c) => c.svg && !c.svg.includes('SVG pending')).length;

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

      {/* SVG Grid — 2 cols mobile, 3 md, 5 xl */}
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

      {/* Regenerate panel — chat + color picker + direction selector */}
      {onRegenerate && (
        <RegeneratePanel onRegenerate={onRegenerate} seedColors={seedColors} />
      )}

      {/* Concept modal */}
      {selected && (
        <ConceptModal
          concept={selected}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}
