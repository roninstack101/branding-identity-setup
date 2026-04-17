import { useState, useRef, useEffect } from 'react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ── Per-concept accent colors (index-based) ────────────────────────────────────
const CONCEPT_COLORS = [
  ['#818cf8', 'rgba(129,140,248,0.22)', 'rgba(129,140,248,0.08)'],
  ['#34d399', 'rgba(52,211,153,0.22)',  'rgba(52,211,153,0.08)' ],
  ['#60a5fa', 'rgba(96,165,250,0.22)',  'rgba(96,165,250,0.08)' ],
  ['#fbbf24', 'rgba(251,191,36,0.22)',  'rgba(251,191,36,0.08)' ],
  ['#c084fc', 'rgba(192,132,252,0.22)', 'rgba(192,132,252,0.08)'],
  ['#38bdf8', 'rgba(56,189,248,0.22)',  'rgba(56,189,248,0.08)' ],
  ['#fb923c', 'rgba(251,146,60,0.22)',  'rgba(251,146,60,0.08)' ],
  ['#a3e635', 'rgba(163,230,53,0.22)',  'rgba(163,230,53,0.08)' ],
  ['#2dd4bf', 'rgba(45,212,191,0.22)',  'rgba(45,212,191,0.08)' ],
  ['#f472b6', 'rgba(244,114,182,0.22)', 'rgba(244,114,182,0.08)'],
];

function getConceptStyle(number = 1) {
  const [color, border, bg] = CONCEPT_COLORS[(number - 1) % CONCEPT_COLORS.length];
  return { color, border, bg };
}

// Generic style direction chips
const DESIGN_DIRECTIONS = [
  'Minimal', 'Geometric', 'Bold', 'Typographic', 'Organic',
  'Dynamic', 'Systematic', 'Monogram', 'Iconic', 'Abstract',
];

// ── Color helpers ─────────────────────────────────────────────────────────────
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
  return [0, 25, 170, 195, 330].map((off, i) =>
    hslToHex((base + off) % 360, s, [40, 55, 45, 60, 38][i])
  );
}

function isValidHex(str) { return /^#[0-9a-fA-F]{6}$/.test(str); }

function contrastColor(hex) {
  if (!isValidHex(hex)) return 'rgba(255,255,255,0.75)';
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.55
    ? 'rgba(0,0,0,0.65)' : 'rgba(255,255,255,0.85)';
}

function contrastOverlay(hex) {
  if (!isValidHex(hex)) return 'rgba(0,0,0,0.18)';
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.55
    ? 'rgba(0,0,0,0.12)' : 'rgba(0,0,0,0.22)';
}

// ── Coolors-style color swatch ────────────────────────────────────────────────
function ColorSwatch({ hex, locked, index, onColorChange, onToggleLock }) {
  const inputRef = useRef(null);
  const textRef  = useRef(null);
  const [hovered, setHovered] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draft,   setDraft]   = useState(hex.toUpperCase());
  const [copied,  setCopied]  = useState(false);

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
      <input ref={inputRef} type="color" value={hex}
        onChange={(e) => onColorChange(index, e.target.value)}
        className="absolute opacity-0 pointer-events-none w-0 h-0" tabIndex={-1} />

      <div className="flex justify-between items-center p-2 transition-opacity duration-150"
        style={{ opacity: hovered || locked ? 1 : 0 }}>
        <button onClick={copyHex}
          className="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold transition-all hover:scale-110"
          style={{ background: overlay, color: fg }} title="Copy hex">
          {copied ? '✓' : '⎘'}
        </button>
        <button onClick={(e) => { e.stopPropagation(); onToggleLock(index); }}
          className="w-7 h-7 rounded-lg flex items-center justify-center text-xs transition-all hover:scale-110"
          style={{ background: overlay, color: fg }} title={locked ? 'Unlock' : 'Lock'}>
          {locked ? '🔒' : '🔓'}
        </button>
      </div>

      <div className="flex-1 flex items-center justify-center cursor-pointer transition-opacity duration-150"
        style={{ opacity: hovered ? 1 : 0 }} onClick={() => inputRef.current?.click()}>
        <div className="w-9 h-9 rounded-full flex items-center justify-center text-base transition-transform hover:scale-110"
          style={{ background: overlay, color: fg }}>✎</div>
      </div>

      <div className="pb-3 pt-1 px-1 flex flex-col items-center gap-1">
        {editing ? (
          <input ref={textRef} value={draft} maxLength={7}
            onChange={(e) => setDraft(e.target.value.toUpperCase())}
            onBlur={commitDraft}
            onKeyDown={(e) => { if (e.key === 'Enter') commitDraft(); if (e.key === 'Escape') { setEditing(false); setDraft(hex.toUpperCase()); } }}
            className="w-full text-center text-[11px] font-mono font-bold bg-black/20 rounded px-1 py-0.5 focus:outline-none focus:ring-1 focus:ring-white/40"
            style={{ color: fg }} onClick={(e) => e.stopPropagation()} />
        ) : (
          <button className="text-[11px] font-mono font-bold tracking-wider px-1 py-0.5 rounded transition-all hover:bg-black/10"
            style={{ color: fg }}
            onClick={(e) => { e.stopPropagation(); setEditing(true); setTimeout(() => textRef.current?.select(), 30); }}>
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
      <div className="flex rounded-2xl overflow-hidden border border-white/10" style={{ height: '200px', gap: '2px' }}>
        {palette.map((hex, i) => (
          <ColorSwatch key={i} hex={hex} locked={locked[i]} index={i}
            onColorChange={onColorChange} onToggleLock={onToggleLock} />
        ))}
      </div>
      <div className="flex items-center justify-between">
        <p className="text-[9px] text-white/25">Click ✎ to pick · click hex to type · 🔒 to keep on shuffle</p>
        <button onClick={onNewPalette}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 text-white/60 hover:text-white text-[10px] font-bold transition-all">
          ⟳ Generate New
        </button>
      </div>
    </div>
  );
}

// ── Concept card (text-only, no SVG) ─────────────────────────────────────────
function ConceptCard({ concept, selected, onClick }) {
  const style   = getConceptStyle(concept.number || 1);
  const palette = Array.isArray(concept.palette) ? concept.palette.filter(Boolean) : [];

  return (
    <div
      onClick={() => onClick(concept)}
      className="rounded-2xl border overflow-hidden flex flex-col cursor-pointer transition-all hover:scale-[1.01]"
      style={{
        borderColor: selected ? style.color : style.border,
        background:  selected ? style.bg : 'rgba(255,255,255,0.015)',
        boxShadow:   selected ? `0 0 0 2px ${style.color}` : 'none',
      }}
    >
      {/* Colour stripe */}
      <div className="h-2 w-full flex">
        {palette.length > 0
          ? palette.map((hex, i) => <div key={i} className="flex-1" style={{ backgroundColor: hex }} />)
          : <div className="flex-1" style={{ backgroundColor: style.color }} />
        }
      </div>

      <div className="p-3 space-y-2 flex-1 flex flex-col">
        <div className="flex items-center gap-1.5">
          <div className="w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-black flex-shrink-0"
            style={{ background: style.border, color: style.color }}>
            {concept.number}
          </div>
          <div className="text-xs font-black leading-tight truncate" style={{ color: style.color }}>
            {concept.name}
          </div>
        </div>

        {concept.visual_concept && (
          <p className="text-[10px] text-white/45 leading-snug line-clamp-3 flex-1">
            {concept.visual_concept}
          </p>
        )}

        {concept.rationale && (
          <p className="text-[9px] text-white/30 leading-snug line-clamp-2 italic">
            {concept.rationale}
          </p>
        )}
      </div>
    </div>
  );
}

// ── Logo Generator Panel ──────────────────────────────────────────────────────
function LogoGeneratorPanel({ concepts, projectId, seedColors }) {
  const [selectedConcept, setSelectedConcept] = useState(1);
  const [refUrl,     setRefUrl]     = useState('');
  const [urlValid,   setUrlValid]   = useState(null); // null | true | false
  const [userPrompt, setUserPrompt] = useState('');
  const [palette,    setPalette]    = useState(() => {
    const harmony = generateHarmony();
    const seeds   = (seedColors || []).filter(isValidHex);
    return harmony.map((c, i) => seeds[i] || c);
  });
  const [locked,     setLocked]     = useState([false, false, false, false, false]);
  const [directions, setDirections] = useState([]);
  const [loading,    setLoading]    = useState(false);
  const [result,     setResult]     = useState(null); // { b64_json, model, concept }
  const [error,      setError]      = useState('');

  const toggleLock  = (i) => setLocked((l) => l.map((v, idx) => idx === i ? !v : v));
  const updateColor = (i, hex) => setPalette((p) => p.map((v, idx) => idx === i ? hex : v));
  const newPalette  = () => {
    const fresh = generateHarmony();
    setPalette((p) => p.map((v, i) => locked[i] ? v : fresh[i]));
  };
  const toggleDir = (d) => setDirections((ds) => ds.includes(d) ? ds.filter(x => x !== d) : [...ds, d]);

  // Validate reference URL on change
  useEffect(() => {
    if (!refUrl.trim()) { setUrlValid(null); return; }
    try { new URL(refUrl); setUrlValid(true); } catch { setUrlValid(false); }
  }, [refUrl]);

  const generate = async () => {
    if (!projectId) return;
    setLoading(true);
    setError('');
    setResult(null);

    // Build user_prompt from palette + directions + free text
    const parts = [];
    if (userPrompt.trim()) parts.push(userPrompt.trim());
    if (directions.length) parts.push(`Style directions: ${directions.join(', ')}.`);
    parts.push(`Use these brand colours: ${palette.join(', ')}.`);
    const combinedPrompt = parts.join(' ');

    try {
      const res = await fetch(`${API}/api/logo/generate`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id:     projectId,
          concept_number: selectedConcept,
          reference_url:  urlValid && refUrl.trim() ? refUrl.trim() : null,
          user_prompt:    combinedPrompt,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setResult(data);
    } catch (e) {
      setError(e.message || 'Generation failed');
    } finally {
      setLoading(false);
    }
  };

  const downloadResult = () => {
    if (!result?.b64_json) return;
    const a = document.createElement('a');
    a.href     = `data:image/png;base64,${result.b64_json}`;
    a.download = `logo-concept-${selectedConcept}.png`;
    a.click();
  };


  return (
    <div className="rounded-2xl border border-white/8 overflow-hidden" style={{ background: 'rgba(255,255,255,0.012)' }}>
      {/* Header */}
      <div className="px-5 py-4 border-b border-white/6">
        <div className="flex items-center gap-2.5">
          <span className="text-base">✦</span>
          <div>
            <div className="text-sm font-black text-white/85">Logo Generator</div>
            <div className="text-[10px] text-white/30 mt-0.5">
              Paste a reference image link → AI redesigns it for your brand
            </div>
          </div>
        </div>
      </div>

      <div className="p-5 space-y-6">

        {/* Concept selector */}
        <div className="space-y-2">
          <div className="text-[10px] font-black uppercase tracking-[0.15em] text-white/35">
            Based on concept
          </div>
          <div className="flex flex-wrap gap-2">
            {concepts.map((c) => {
              const s = getConceptStyle(c.number || 1);
              const active = selectedConcept === c.number;
              return (
                <button key={c.number} onClick={() => setSelectedConcept(c.number)}
                  className="px-3 py-1.5 rounded-full text-[10px] font-bold border transition-all"
                  style={active
                    ? { background: s.border, borderColor: s.color, color: s.color }
                    : { background: 'rgba(255,255,255,0.03)', borderColor: 'rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.35)' }
                  }
                  title={c.name}
                >
                  {c.number}. {c.name?.split(' ').slice(0, 2).join(' ')}
                </button>
              );
            })}
          </div>
        </div>

        {/* Reference URL */}
        <div className="space-y-2">
          <div className="text-[10px] font-black uppercase tracking-[0.15em] text-white/35">
            Reference Image URL
            <span className="ml-2 normal-case font-normal tracking-normal text-white/20">
              — logo, image, or design you want to use as style reference
            </span>
          </div>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <input
                value={refUrl}
                onChange={(e) => setRefUrl(e.target.value)}
                placeholder="https://example.com/logo.png"
                className="w-full bg-white/[0.03] border rounded-xl px-4 py-2.5 text-sm text-white/80 placeholder-white/20 focus:outline-none focus:border-white/25 transition-all"
                style={{
                  borderColor: urlValid === false ? 'rgba(239,68,68,0.4)' :
                               urlValid === true  ? 'rgba(52,211,153,0.4)' : 'rgba(255,255,255,0.1)'
                }}
              />
              {urlValid !== null && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2 text-sm">
                  {urlValid ? '✓' : '✕'}
                </div>
              )}
            </div>
          </div>
          {/* Reference preview */}
          {urlValid && refUrl && (
            <div className="flex items-center gap-3">
              <img src={refUrl} alt="Reference preview"
                className="w-20 h-20 object-contain rounded-xl border border-white/10 bg-white/5"
                onError={(e) => { e.target.style.display = 'none'; setUrlValid(false); }}
              />
              <p className="text-[10px] text-white/30 leading-relaxed">
                The AI will study this image's style, composition, and quality,<br />
                then completely redesign it for your brand.
              </p>
            </div>
          )}
        </div>

        {/* Color palette */}
        <div className="space-y-2">
          <div className="text-[10px] font-black uppercase tracking-[0.15em] text-white/35">Brand Colours</div>
          <ColorPalettePanel palette={palette} locked={locked}
            onColorChange={updateColor} onToggleLock={toggleLock} onNewPalette={newPalette} />
        </div>

        {/* Style direction chips */}
        <div className="space-y-2">
          <div className="text-[10px] font-black uppercase tracking-[0.15em] text-white/35">
            Style Direction
            <span className="ml-2 normal-case font-normal tracking-normal text-white/20">
              {directions.length === 0 ? '— optional' : `— ${directions.join(', ')}`}
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {DESIGN_DIRECTIONS.map((name, i) => {
              const [color, border] = CONCEPT_COLORS[i % CONCEPT_COLORS.length];
              const active = directions.includes(name);
              return (
                <button key={name} onClick={() => toggleDir(name)}
                  className="px-3 py-1.5 rounded-full text-[10px] font-bold border transition-all"
                  style={active
                    ? { background: border, borderColor: color, color }
                    : { background: 'rgba(255,255,255,0.03)', borderColor: 'rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.35)' }
                  }
                >
                  {name}
                </button>
              );
            })}
          </div>
        </div>

        {/* Free-text prompt */}
        <div className="space-y-2">
          <div className="text-[10px] font-black uppercase tracking-[0.15em] text-white/35">
            Additional Instructions
          </div>
          <textarea
            value={userPrompt}
            onChange={(e) => setUserPrompt(e.target.value)}
            placeholder="Describe any specific changes…&#10;e.g. Make it feel more premium and minimal, use sharp angles, no circles"
            rows={3}
            className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-sm text-white/80 placeholder-white/20 focus:outline-none focus:border-white/25 focus:bg-white/[0.05] transition-all resize-none leading-relaxed"
          />
        </div>

        {/* Generate button */}
        <div className="flex items-center justify-between gap-4 pt-1">
          <p className="text-[10px] text-white/25 leading-relaxed max-w-xs">
            {urlValid
              ? 'Reference image detected — AI will style-transfer it to your brand'
              : 'No reference — AI will generate from the visual concept description'}
          </p>
          <button
            onClick={generate}
            disabled={loading || !projectId}
            className="flex-shrink-0 flex items-center gap-2 px-6 py-2.5 rounded-xl font-black text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              background:  loading ? 'rgba(99,102,241,0.3)' : 'rgba(99,102,241,0.85)',
              color:       '#fff',
              boxShadow:   loading ? 'none' : '0 0 20px rgba(99,102,241,0.35)',
            }}
          >
            {loading ? (
              <><span className="inline-block w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Generating…</>
            ) : (
              <>✦ Generate Logo</>
            )}
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-xl px-4 py-3 bg-red-500/8 border border-red-500/20">
            <p className="text-[11px] text-red-300/80">{error}</p>
          </div>
        )}

        {/* Result */}
        {result?.b64_json && (
          <div className="space-y-3">
            <div className="text-[10px] font-black uppercase tracking-[0.15em] text-white/35 flex items-center gap-2">
              Generated Logo
              <span className="normal-case font-normal tracking-normal text-white/20">
                via {result.model}
              </span>
            </div>
            <div className="relative rounded-2xl overflow-hidden border border-white/10 bg-white">
              <img
                src={`data:image/png;base64,${result.b64_json}`}
                alt="Generated logo"
                className="w-full"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={downloadResult}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 text-white/70 hover:text-white text-sm font-bold transition-all"
              >
                ↓ Download PNG
              </button>
              <button
                onClick={() => { setResult(null); setError(''); }}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/[0.03] border border-white/8 hover:bg-white/8 text-white/40 hover:text-white/70 text-sm transition-all"
              >
                Clear
              </button>
            </div>
          </div>
        )}
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
      if (line.startsWith('•') || line.startsWith('-') || line.match(/^\d+\./))
        return <div key={i} className="text-[11px] text-white/45 leading-relaxed pl-3">{line}</div>;
      if (!line.trim()) return <div key={i} className="h-1.5" />;
      return <div key={i} className="text-[11px] text-white/50 leading-relaxed">{line}</div>;
    });

  return (
    <div className="rounded-2xl border border-white/8 overflow-hidden">
      <button onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-white/[0.02] transition-colors"
        style={{ background: 'rgba(255,255,255,0.015)' }}>
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

// ── Concept detail modal ──────────────────────────────────────────────────────
function ConceptModal({ concept, onClose }) {
  const style   = getConceptStyle(concept.number || 1);
  const palette = Array.isArray(concept.palette) ? concept.palette.filter(Boolean) : [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
      onClick={onClose}>
      <div className="relative w-full max-w-lg bg-slate-950 border border-white/10 rounded-3xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}>
        <button onClick={onClose}
          className="absolute top-4 right-4 z-10 w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white/60 hover:text-white transition-all">
          ✕
        </button>

        {/* Colour stripe */}
        <div className="h-2 w-full flex flex-shrink-0">
          {palette.length > 0
            ? palette.map((hex, i) => <div key={i} className="flex-1" style={{ backgroundColor: hex }} />)
            : <div className="flex-1" style={{ backgroundColor: style.color }} />
          }
        </div>

        <div className="p-6 space-y-4 overflow-y-auto">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold mb-2"
              style={{ background: style.bg, border: `1px solid ${style.border}`, color: style.color }}>
              Concept {concept.number}
            </div>
            <h2 className="text-xl font-black text-white">{concept.name}</h2>
            {concept.typography && (
              <div className="text-[10px] text-white/30 mt-0.5">Typography: {concept.typography}</div>
            )}
          </div>

          {concept.visual_concept && (
            <div className="rounded-xl px-4 py-3 bg-white/[0.02] border border-white/6">
              <div className="text-[9px] font-black uppercase tracking-[0.2em] mb-2 text-white/30">Visual Concept</div>
              <p className="text-sm text-white/65 leading-relaxed">{concept.visual_concept}</p>
            </div>
          )}

          {concept.rationale && (
            <div className="rounded-xl px-4 py-3" style={{ background: style.bg, border: `1px solid ${style.border}` }}>
              <div className="text-[9px] font-black uppercase tracking-[0.2em] mb-1" style={{ color: style.color }}>
                Creative Rationale
              </div>
              <p className="text-sm text-white/65 leading-relaxed">{concept.rationale}</p>
            </div>
          )}

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

// ── Main Export ───────────────────────────────────────────────────────────────
export default function VariantGallery({ data, projectId, onRegenerate }) {
  const [selected, setSelected] = useState(null);

  if (!data) return null;

  const concepts     = Array.isArray(data.design_concepts) ? data.design_concepts : [];
  const briefText    = data.logo_design_brief       || '';
  const primaryColor = data.primary_color           || '';
  const accentColor  = data.accent_color            || '';
  const font         = data.font                    || '';
  const compNotes    = data.competitor_visual_notes || '';
  const seedColors   = [primaryColor, accentColor].filter(Boolean);

  if (concepts.length === 0 && !briefText) {
    return (
      <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-8 text-center space-y-3">
        <div className="text-3xl opacity-40">⚠️</div>
        <div className="text-white/60 font-bold">Visual Identity data is empty</div>
        <div className="text-white/35 text-sm leading-relaxed max-w-md mx-auto">
          Check that <span className="text-amber-300/80">GEMINI_API_KEY</span> is set in the backend{' '}
          <code className="bg-white/10 px-1 rounded">.env</code>.
        </div>
        {onRegenerate && (
          <button onClick={() => onRegenerate('visual_identity_agent', 'regenerate visual identity')}
            className="mt-2 px-5 py-2 rounded-xl bg-white/5 border border-white/15 text-white/60 hover:text-white hover:bg-white/10 text-sm font-bold transition-all">
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
            {concepts.length} visual directions · Researched by Gemini · Generate images below
          </p>
        </div>
      </div>

      {/* Info callout */}
      <div className="flex items-start gap-3 p-4 rounded-2xl bg-indigo-500/5 border border-indigo-500/15">
        <span className="text-indigo-400 text-lg flex-shrink-0">✦</span>
        <div className="text-xs text-white/45 leading-relaxed">
          <span className="text-indigo-300 font-bold">Gemini</span> researched your competitors and created{' '}
          10 original logo concepts. Select a concept, paste a reference image link, and click{' '}
          <span className="text-emerald-300 font-bold">Generate Logo</span> to produce a brand-specific image.
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

      {/* Concept grid */}
      {concepts.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">
          {concepts.map((c) => (
            <ConceptCard key={c.number} concept={c} selected={false} onClick={setSelected} />
          ))}
        </div>
      )}

      {/* Design Brief */}
      <DesignBriefPanel briefText={briefText} competitorNotes={compNotes}
        primaryColor={primaryColor} accentColor={accentColor} font={font} />

      {/* Logo Generator */}
      <LogoGeneratorPanel concepts={concepts} projectId={projectId} seedColors={seedColors} />

      {/* Regenerate (brief only) */}
      {onRegenerate && (
        <div className="flex justify-end">
          <button
            onClick={() => onRegenerate('visual_identity_agent', 'Regenerate logo concepts with fresh ideas')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 text-white/50 hover:text-white text-xs font-bold transition-all"
          >
            ↻ Regenerate All Concepts
          </button>
        </div>
      )}

      {/* Concept modal */}
      {selected && <ConceptModal concept={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
