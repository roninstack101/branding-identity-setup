import { useState, useRef, useEffect } from 'react';

// ── Color Utilities ───────────────────────────────────────────────────────────

function hexToHsl(hex) {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h = 0, s = 0;
  const l = (max + min) / 2;
  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
      case g: h = ((b - r) / d + 2) / 6; break;
      case b: h = ((r - g) / d + 4) / 6; break;
    }
  }
  return [Math.round(h * 360), Math.round(s * 100), Math.round(l * 100)];
}

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

function isLight(hex) {
  try {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return (r * 299 + g * 587 + b * 114) / 1000 > 140;
  } catch { return false; }
}

function clamp(v, min, max) {
  return Math.max(min, Math.min(max, v));
}

function generateHarmony(lockedColors, count) {
  const firstLocked = lockedColors.find(Boolean);
  const baseHue = firstLocked ? hexToHsl(firstLocked)[0] : Math.random() * 360;
  const rand = (range) => (Math.random() - 0.5) * range;

  const offsets       = [0, 30, 150, 180, 210, 270, 300, 330];
  const lightnessSteps = [50, 65, 40, 70, 35, 55, 45, 60];
  const satSteps       = [70, 55, 65, 45, 75, 60, 50, 65];

  const result = [];
  let slot = 0;
  for (let i = 0; i < count; i++) {
    if (lockedColors[i]) {
      result.push(lockedColors[i]);
    } else {
      const hue = (baseHue + offsets[slot % offsets.length] + rand(15) + 360) % 360;
      const sat = clamp(satSteps[slot % satSteps.length] + rand(15), 25, 90);
      const lig = clamp(lightnessSteps[slot % lightnessSteps.length] + rand(12), 22, 82);
      result.push(hslToHex(hue, sat, lig));
      slot++;
    }
  }
  return result;
}

function parseCoolorsInput(input) {
  const match = input.match(/([0-9a-fA-F]{6}(?:-[0-9a-fA-F]{6})+)/);
  if (!match) return null;
  const colors = match[1].split('-').map((h) => `#${h.toLowerCase()}`);
  return colors.length >= 2 ? colors : null;
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function ColorPalettePicker({ palette, onChange }) {
  const [locked, setLocked]         = useState(() => palette.map(() => false));
  const [copied, setCopied]         = useState(null);
  const [showImport, setShowImport] = useState(false);
  const [importInput, setImportInput] = useState('');
  const [importError, setImportError] = useState('');
  const colorRefs = useRef([]);

  useEffect(() => {
    setLocked((prev) => palette.map((_, i) => prev[i] ?? false));
  }, [palette.length]);

  const updateColor = (i, hex) => {
    const next = [...palette];
    next[i] = hex;
    onChange(next);
  };

  const toggleLock = (i) =>
    setLocked((prev) => prev.map((v, idx) => (idx === i ? !v : v)));

  const copyHex = (hex, i) => {
    navigator.clipboard.writeText(hex).catch(() => {});
    setCopied(i);
    setTimeout(() => setCopied(null), 1400);
  };

  const addColor = () => {
    if (palette.length >= 8) return;
    const [h, s] = hexToHsl(palette[palette.length - 1] || '#808080');
    onChange([...palette, hslToHex((h + 40) % 360, s, 55)]);
  };

  const removeColor = (i) => {
    if (palette.length <= 2) return;
    onChange(palette.filter((_, idx) => idx !== i));
    setLocked((prev) => prev.filter((_, idx) => idx !== i));
  };

  const generate = () => {
    const lockedColors = palette.map((c, i) => (locked[i] ? c : null));
    onChange(generateHarmony(lockedColors, palette.length));
  };

  const openInCoolors = () => {
    const codes = palette.map((h) => h.replace('#', '')).join('-');
    window.open(`https://coolors.co/${codes}`, '_blank');
  };

  const handleImport = () => {
    const parsed = parseCoolorsInput(importInput);
    if (!parsed) {
      setImportError('No valid colors found. Example: 264653-2a9d8f-e9c46a-f4a261-e76f51');
      return;
    }
    onChange(parsed);
    setLocked(parsed.map(() => false));
    setImportInput('');
    setImportError('');
    setShowImport(false);
  };

  return (
    <div>
      {/* ── Coolors-style columns ─────────────────────────────────────── */}
      <div className="flex rounded-xl overflow-hidden border border-white/10" style={{ height: 160 }}>
        {palette.map((hex, i) => {
          const light  = isLight(hex);
          const txtClr = light ? 'rgba(0,0,0,0.75)' : 'rgba(255,255,255,0.9)';
          const btnBg  = light ? 'rgba(0,0,0,0.12)'  : 'rgba(255,255,255,0.15)';

          return (
            <div
              key={i}
              className="relative flex-1 flex flex-col items-center justify-between py-3 group transition-all duration-150"
              style={{ backgroundColor: hex, minWidth: 0 }}
            >
              {/* Top controls */}
              <div className="flex flex-col items-center gap-1.5 relative z-10">
                {/* Lock button */}
                <button
                  onClick={(e) => { e.stopPropagation(); toggleLock(i); }}
                  title={locked[i] ? 'Unlock' : 'Lock'}
                  className="w-7 h-7 rounded-full flex items-center justify-center text-xs transition-all"
                  style={{
                    background: btnBg,
                    color: txtClr,
                    opacity: locked[i] ? 1 : 0,
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.opacity = '1')}
                  onMouseLeave={(e) => { if (!locked[i]) e.currentTarget.style.opacity = '0'; }}
                >
                  {locked[i] ? '🔒' : '🔓'}
                </button>

                {/* Remove button */}
                {palette.length > 2 && (
                  <button
                    onClick={(e) => { e.stopPropagation(); removeColor(i); }}
                    title="Remove"
                    className="w-7 h-7 rounded-full items-center justify-center text-xs transition-all opacity-0 group-hover:opacity-100 hidden group-hover:flex"
                    style={{ background: btnBg, color: txtClr }}
                  >
                    ✕
                  </button>
                )}
              </div>

              {/* Transparent click overlay → opens color picker */}
              <button
                className="absolute inset-0 w-full h-full cursor-pointer"
                style={{ background: 'transparent', zIndex: 1 }}
                onClick={() => colorRefs.current[i]?.click()}
                title="Click to edit"
              />
              <input
                ref={(el) => { colorRefs.current[i] = el; }}
                type="color"
                value={hex}
                onChange={(e) => updateColor(i, e.target.value)}
                className="sr-only"
              />

              {/* Hex badge */}
              <button
                onClick={(e) => { e.stopPropagation(); copyHex(hex, i); }}
                title="Copy"
                className="relative z-10 text-[10px] font-mono px-2 py-1 rounded-lg transition-all"
                style={{ background: btnBg, color: txtClr, backdropFilter: 'blur(4px)' }}
              >
                {copied === i ? '✓ Copied' : hex.toUpperCase()}
              </button>
            </div>
          );
        })}

        {/* Add color */}
        {palette.length < 8 && (
          <button
            onClick={addColor}
            title="Add color"
            className="flex items-center justify-center flex-shrink-0 text-xl transition-all hover:bg-violet-500/10"
            style={{
              width: 36,
              background: 'rgba(139,92,246,0.06)',
              borderLeft: '1px dashed rgba(139,92,246,0.3)',
              color: '#a78bfa',
            }}
          >
            +
          </button>
        )}
      </div>

      {/* ── Action bar ───────────────────────────────────────────────── */}
      <div className="flex items-center gap-2 mt-3 flex-wrap">
        <button
          onClick={generate}
          className="text-xs px-4 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all hover:opacity-90"
          style={{
            background: 'linear-gradient(135deg, rgba(139,92,246,0.15), rgba(59,130,246,0.15))',
            border: '1px solid rgba(139,92,246,0.3)',
            color: '#a78bfa',
          }}
        >
          🎲 Generate New
        </button>

        <button
          onClick={openInCoolors}
          className="text-xs px-3 py-2 rounded-lg flex items-center gap-1.5 transition-all hover:opacity-80"
          style={{
            background: 'rgba(16,185,129,0.1)',
            border: '1px solid rgba(16,185,129,0.25)',
            color: '#10b981',
          }}
        >
          🌈 Open in Coolors
        </button>

        <button
          onClick={() => { setShowImport(!showImport); setImportError(''); }}
          className="text-xs px-3 py-2 rounded-lg transition-all hover:opacity-90"
          style={{
            background: showImport ? 'rgba(245,158,11,0.15)' : 'rgba(245,158,11,0.08)',
            border: '1px solid rgba(245,158,11,0.25)',
            color: '#f59e0b',
          }}
        >
          📥 Import URL
        </button>

        <span className="text-[10px] text-white/30 ml-auto hidden sm:block">
          Click swatch to edit · 🔒 lock to keep on generate
        </span>
      </div>

      {/* ── Import bar ───────────────────────────────────────────────── */}
      {showImport && (
        <div
          className="mt-3 p-3 rounded-xl"
          style={{
            background: 'rgba(245,158,11,0.05)',
            border: '1px solid rgba(245,158,11,0.2)',
          }}
        >
          <p className="text-xs font-semibold mb-2" style={{ color: '#f59e0b' }}>
            Import from Coolors
          </p>
          <div className="flex gap-2">
            <input
              type="text"
              value={importInput}
              onChange={(e) => { setImportInput(e.target.value); setImportError(''); }}
              onKeyDown={(e) => e.key === 'Enter' && handleImport()}
              placeholder="https://coolors.co/264653-2a9d8f-e9c46a-f4a261-e76f51"
              autoFocus
              className="flex-1 text-xs bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-white/70 placeholder-white/20 focus:outline-none focus:border-amber-400/40"
            />
            <button
              onClick={handleImport}
              className="text-xs px-4 py-1.5 rounded-lg flex-shrink-0 font-semibold transition-all hover:opacity-90"
              style={{
                background: 'rgba(245,158,11,0.2)',
                border: '1px solid rgba(245,158,11,0.35)',
                color: '#f59e0b',
              }}
            >
              Import
            </button>
          </div>
          {importError && (
            <p className="text-[10px] mt-1.5 text-red-400">{importError}</p>
          )}
          <p className="text-[10px] mt-1.5 text-white/30">
            Paste a Coolors URL or bare hex codes, e.g.{' '}
            <span className="font-mono text-white/50">264653-2a9d8f-e9c46a</span>
          </p>
        </div>
      )}
    </div>
  );
}
