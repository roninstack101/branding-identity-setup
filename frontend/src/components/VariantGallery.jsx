import { useState, useEffect, useCallback } from 'react';
import { regenerateVariant } from '../services/api';
import ColorPalettePicker from './ColorPalettePicker';

// ── Google Fonts Catalog ──────────────────────────────────────────────────────
const GOOGLE_FONTS_CATALOG = {
  'Sans-Serif': [
    'Inter', 'Roboto', 'Open Sans', 'Montserrat', 'Poppins', 'Raleway',
    'Nunito', 'Work Sans', 'DM Sans', 'Space Grotesk', 'Outfit', 'Archivo',
    'Manrope', 'Plus Jakarta Sans', 'Figtree', 'Albert Sans', 'Urbanist',
    'Sora', 'Red Hat Display', 'Geist',
  ],
  'Serif': [
    'Playfair Display', 'Lora', 'Merriweather', 'Crimson Text', 'Source Serif 4',
    'Roboto Slab', 'DM Serif Display', 'Libre Baskerville', 'Cormorant Garamond',
    'EB Garamond', 'Bitter', 'Spectral', 'Vollkorn', 'Bodoni Moda',
    'Fraunces', 'Newsreader', 'Literata',
  ],
  'Display': [
    'Bebas Neue', 'Oswald', 'Anton', 'Abril Fatface', 'Righteous', 'Bungee',
    'Orbitron', 'Passion One', 'Black Ops One', 'Lilita One',
    'Fredoka One', 'Titan One', 'Staatliches',
  ],
  'Handwriting': [
    'Caveat', 'Pacifico', 'Dancing Script', 'Permanent Marker', 'Satisfy',
    'Great Vibes', 'Lobster', 'Sacramento', 'Amatic SC', 'Indie Flower',
    'Kalam', 'Architects Daughter',
  ],
  'Monospace': [
    'JetBrains Mono', 'Fira Code', 'Source Code Pro', 'IBM Plex Mono',
    'Space Mono', 'Roboto Mono', 'Ubuntu Mono',
  ],
};

const ALL_FONTS = Object.values(GOOGLE_FONTS_CATALOG).flat();

// ── Logo type badges ──────────────────────────────────────────────────────────
const LOGO_TYPE_BADGE = {
  wordmark:         { color: 'bg-blue-500/20 text-blue-300 border-blue-500/30',       label: 'Wordmark' },
  lettermark:       { color: 'bg-violet-500/20 text-violet-300 border-violet-500/30', label: 'Lettermark' },
  icon_mark:        { color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30', label: 'Icon Mark' },
  combination_mark: { color: 'bg-amber-500/20 text-amber-300 border-amber-500/30',    label: 'Combination' },
  emblem:           { color: 'bg-rose-500/20 text-rose-300 border-rose-500/30',       label: 'Emblem' },
  abstract_mark:    { color: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',       label: 'Abstract' },
  mascot:           { color: 'bg-orange-500/20 text-orange-300 border-orange-500/30', label: 'Mascot' },
};

// ── Font loader ───────────────────────────────────────────────────────────────
function loadFont(fontName) {
  if (!fontName) return;
  const id = `gfont-${fontName.replace(/\s+/g, '-').toLowerCase()}`;
  if (document.getElementById(id)) return;
  const link = document.createElement('link');
  link.id = id;
  link.rel = 'stylesheet';
  link.href = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(fontName)}:wght@400;500;600;700;800&display=swap`;
  document.head.appendChild(link);
}

function useGoogleFont(fontName) {
  useEffect(() => { loadFont(fontName); }, [fontName]);
}

function loadGoogleFonts(fonts) {
  fonts.filter(Boolean).forEach(loadFont);
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).catch(() => {});
}

function downloadSVG(variant) {
  let svg = variant.logo_svg;
  if (!svg && variant.logo_url?.startsWith('data:image/svg+xml;base64,')) {
    svg = atob(variant.logo_url.split(',')[1]);
  }
  if (!svg) return;
  const blob = new Blob([svg], { type: 'image/svg+xml' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${(variant.variant_name || 'logo').replace(/\s+/g, '-').toLowerCase()}.svg`;
  a.click();
  URL.revokeObjectURL(url);
}

// ── Logo Preview ──────────────────────────────────────────────────────────────
function LogoPreview({ variant, bgColor }) {
  if (variant.logo_url) {
    return (
      <img
        src={variant.logo_url}
        alt={variant.variant_name}
        className="w-full h-64 object-contain"
        style={{ background: bgColor || variant.color_palette?.[4] || '#f8f8f8' }}
      />
    );
  }
  return (
    <div className="w-full h-64 flex items-center justify-center bg-white/5 border border-white/10">
      <span className="text-white/20 text-sm">No SVG</span>
    </div>
  );
}

// ── Font Picker Modal ─────────────────────────────────────────────────────────
function FontPickerModal({ type, currentFont, onSelect, onClose }) {
  const [search, setSearch] = useState('');

  const filtered = search.trim()
    ? { 'Search Results': ALL_FONTS.filter((f) => f.toLowerCase().includes(search.toLowerCase())) }
    : GOOGLE_FONTS_CATALOG;

  // Preload visible fonts
  useEffect(() => {
    ALL_FONTS.forEach(loadFont);
  }, []);

  return (
    <div
      className="fixed inset-0 z-[60] flex items-end md:items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl bg-slate-950 border border-white/10 rounded-3xl shadow-2xl flex flex-col"
        style={{ maxHeight: '80vh' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b border-white/10 flex-shrink-0">
          <div>
            <h3 className="text-white font-black text-lg">
              {type === 'heading' ? 'Heading' : 'Body'} Font
            </h3>
            <p className="text-white/40 text-xs mt-0.5">Google Fonts — click to apply</p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white/60 hover:text-white transition-all"
          >✕</button>
        </div>

        {/* Search */}
        <div className="px-6 py-3 flex-shrink-0">
          <input
            type="text"
            autoFocus
            placeholder="Search fonts…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-white/25 focus:outline-none focus:border-white/30"
          />
        </div>

        {/* Font grid */}
        <div className="overflow-y-auto flex-1 px-6 pb-6 space-y-6">
          {Object.entries(filtered).map(([category, fonts]) =>
            fonts.length === 0 ? null : (
              <div key={category}>
                <div className="text-[10px] font-black uppercase tracking-[0.2em] text-violet-400/70 mb-3">{category}</div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {fonts.map((font) => {
                    const isActive = currentFont === font;
                    return (
                      <button
                        key={font}
                        onClick={() => onSelect(font)}
                        className="p-3 rounded-xl text-left transition-all hover:border-white/25"
                        style={{
                          background: isActive ? 'rgba(59,130,246,0.15)' : 'rgba(255,255,255,0.02)',
                          border: isActive ? '1px solid rgba(59,130,246,0.4)' : '1px solid rgba(255,255,255,0.07)',
                        }}
                      >
                        <span
                          className="block text-sm mb-1 text-white truncate"
                          style={{
                            fontFamily: `'${font}', sans-serif`,
                            fontWeight: type === 'heading' ? 700 : 400,
                          }}
                        >
                          {font}
                        </span>
                        <span className="text-[10px] text-white/35" style={{ fontFamily: `'${font}', sans-serif` }}>
                          Aa Bb 123
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}

// ── Variant Modal ─────────────────────────────────────────────────────────────
function VariantModal({ variant, variantIndex, projectId, onClose, onUpdated }) {
  const [editedColors,  setEditedColors]  = useState([...(variant.color_palette || [])]);
  const [headingFont,   setHeadingFont]   = useState(variant.heading_font || '');
  const [bodyFont,      setBodyFont]      = useState(variant.body_font    || '');
  const [fontPicker,    setFontPicker]    = useState(null); // 'heading' | 'body' | null
  const [regenerating,  setRegenerating]  = useState(false);
  const [regenError,    setRegenError]    = useState('');
  const [copiedPrompt,  setCopiedPrompt]  = useState(false);
  const [localVariant,  setLocalVariant]  = useState(variant);

  useGoogleFont(headingFont);
  useGoogleFont(bodyFont);

  const badge = LOGO_TYPE_BADGE[variant.logo_type] || LOGO_TYPE_BADGE.abstract_mark;

  const colorsChanged = editedColors.some((c, i) => c !== (variant.color_palette || [])[i]);
  const headingChanged = headingFont !== (variant.heading_font || '');
  const bodyChanged    = bodyFont    !== (variant.body_font    || '');
  const anyChanged = colorsChanged || headingChanged || bodyChanged;

  const handleRegenerate = async () => {
    setRegenerating(true);
    setRegenError('');
    try {
      const res = await regenerateVariant(
        projectId, variantIndex, editedColors,
        headingChanged ? headingFont : undefined,
        bodyChanged    ? bodyFont    : undefined,
      );
      const updated = res.data.variant;
      setLocalVariant(updated);
      setEditedColors([...(updated.color_palette || [])]);
      setHeadingFont(updated.heading_font || '');
      setBodyFont(updated.body_font    || '');
      onUpdated(variantIndex, updated);
    } catch (err) {
      setRegenError(err.response?.data?.detail || 'Regeneration failed');
    } finally {
      setRegenerating(false);
    }
  };

  const handleReset = () => {
    setEditedColors([...(variant.color_palette || [])]);
    setHeadingFont(variant.heading_font || '');
    setBodyFont(variant.body_font    || '');
  };

  const handleCopyPrompt = () => {
    copyToClipboard(localVariant.ideogram_prompt || '');
    setCopiedPrompt(true);
    setTimeout(() => setCopiedPrompt(false), 2000);
  };

  return (
    <>
      <div
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
        onClick={onClose}
      >
        <div
          className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto bg-slate-950 border border-white/10 rounded-3xl shadow-2xl"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Close */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 z-10 w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white/60 hover:text-white transition-all"
          >✕</button>

          <div className="p-8 space-y-6">
            {/* Header */}
            <div>
              <h2 className="text-2xl font-black text-white">{localVariant.variant_name}</h2>
              <span className={`inline-block mt-2 px-3 py-1 rounded-full text-[11px] font-bold border ${badge.color}`}>
                {badge.label}
              </span>
            </div>

            {/* Logo preview — light + dark */}
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-2xl overflow-hidden border border-white/10">
                {regenerating ? (
                  <div className="w-full h-40 flex flex-col items-center justify-center gap-2 bg-white/5">
                    <div className="w-7 h-7 border-2 border-white/20 border-t-white/70 rounded-full animate-spin" />
                    <span className="text-white/30 text-xs">Regenerating…</span>
                  </div>
                ) : (
                  <LogoPreview variant={localVariant} bgColor={editedColors[4] || '#f5f5f5'} />
                )}
              </div>
              <div className="rounded-2xl overflow-hidden border border-white/10">
                {regenerating ? (
                  <div className="w-full h-40 flex items-center justify-center bg-slate-900">
                    <div className="w-7 h-7 border-2 border-white/10 border-t-white/50 rounded-full animate-spin" />
                  </div>
                ) : (
                  <LogoPreview variant={localVariant} bgColor="#0f172a" />
                )}
              </div>
            </div>

            {/* ── Color Palette ── */}
            <div className="space-y-2">
              <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40">Color Palette</div>
              <ColorPalettePicker palette={editedColors} onChange={setEditedColors} />
            </div>

            {/* Color Roles */}
            {localVariant.color_roles && (
              <div className="space-y-1.5">
                <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30">Color Roles</div>
                {Object.entries(localVariant.color_roles).map(([role, desc]) => (
                  <div key={role} className="flex gap-3 items-start text-xs">
                    <span className="font-black uppercase tracking-widest text-white/30 w-24 flex-shrink-0 pt-0.5">{role}</span>
                    <span className="text-white/60 leading-relaxed">{desc}</span>
                  </div>
                ))}
              </div>
            )}

            {/* ── Typography ── */}
            <div className="space-y-3">
              <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40">Typography</div>
              <div className="grid grid-cols-2 gap-4">
                {/* Heading font */}
                <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-300/70">Heading</div>
                    <button
                      onClick={() => setFontPicker('heading')}
                      className="text-[10px] px-2 py-0.5 rounded-lg transition-all"
                      style={{
                        background: headingChanged ? 'rgba(59,130,246,0.2)' : 'rgba(255,255,255,0.05)',
                        border: headingChanged ? '1px solid rgba(59,130,246,0.4)' : '1px solid rgba(255,255,255,0.1)',
                        color: headingChanged ? '#93c5fd' : 'rgba(255,255,255,0.4)',
                      }}
                    >
                      {headingChanged ? '✓ Changed' : 'Change'}
                    </button>
                  </div>
                  <div className="text-white/40 text-[10px] font-mono truncate">{headingFont}</div>
                  <div className="text-white text-xl font-bold leading-tight" style={{ fontFamily: `'${headingFont}', sans-serif` }}>
                    Aa Bb Cc 123
                  </div>
                  <div className="text-white/50 text-xs" style={{ fontFamily: `'${headingFont}', sans-serif` }}>
                    The quick brown fox jumps.
                  </div>
                </div>

                {/* Body font */}
                <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="text-[10px] font-black uppercase tracking-[0.2em] text-violet-300/70">Body</div>
                    <button
                      onClick={() => setFontPicker('body')}
                      className="text-[10px] px-2 py-0.5 rounded-lg transition-all"
                      style={{
                        background: bodyChanged ? 'rgba(139,92,246,0.2)' : 'rgba(255,255,255,0.05)',
                        border: bodyChanged ? '1px solid rgba(139,92,246,0.4)' : '1px solid rgba(255,255,255,0.1)',
                        color: bodyChanged ? '#c4b5fd' : 'rgba(255,255,255,0.4)',
                      }}
                    >
                      {bodyChanged ? '✓ Changed' : 'Change'}
                    </button>
                  </div>
                  <div className="text-white/40 text-[10px] font-mono truncate">{bodyFont}</div>
                  <div className="text-white text-base leading-relaxed" style={{ fontFamily: `'${bodyFont}', sans-serif` }}>
                    Aa Bb Cc 123
                  </div>
                  <div className="text-white/50 text-xs leading-relaxed" style={{ fontFamily: `'${bodyFont}', sans-serif` }}>
                    The quick brown fox jumps.
                  </div>
                </div>
              </div>
              {localVariant.font_pairing_rationale && (
                <p className="text-xs text-white/35 leading-relaxed">{localVariant.font_pairing_rationale}</p>
              )}
            </div>

            {/* ── Changed banner ── */}
            {anyChanged && (
              <div className="flex gap-3 p-4 rounded-2xl border border-blue-500/20 bg-blue-500/5">
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-bold text-blue-300">
                    {[colorsChanged && 'palette', headingChanged && 'heading font', bodyChanged && 'body font']
                      .filter(Boolean).join(' + ')} changed
                  </div>
                  <div className="text-xs text-white/40 mt-0.5">
                    Regenerate to rebuild the SVG logo with your customisations
                  </div>
                </div>
                <button
                  onClick={handleReset}
                  className="flex-shrink-0 px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white/50 hover:text-white text-xs font-bold transition-all"
                >
                  Reset
                </button>
                <button
                  onClick={handleRegenerate}
                  disabled={regenerating}
                  className="flex-shrink-0 flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-black transition-all"
                >
                  {regenerating
                    ? <><span className="w-3 h-3 border border-white/40 border-t-white rounded-full animate-spin" />Regenerating…</>
                    : '✦ Regenerate'}
                </button>
              </div>
            )}

            {regenError && (
              <div className="text-sm text-red-300 bg-red-500/10 border border-red-500/20 rounded-xl p-3">⚠ {regenError}</div>
            )}

            {/* ── Ideogram prompt ── */}
            {localVariant.ideogram_prompt && (
              <div
                className="rounded-xl p-4 space-y-3"
                style={{
                  background: 'linear-gradient(135deg, rgba(99,102,241,0.08), rgba(168,85,247,0.08))',
                  border: '1px solid rgba(99,102,241,0.25)',
                }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm">✨</span>
                    <span className="text-xs font-bold" style={{ color: '#818cf8' }}>Ideogram AI Prompt</span>
                    <span className="text-[9px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: 'rgba(99,102,241,0.15)', color: '#818cf8' }}>
                      AI Image Gen
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={handleCopyPrompt}
                      className="text-[10px] px-2.5 py-1 rounded-lg font-medium transition-all"
                      style={{
                        background: copiedPrompt ? 'rgba(16,185,129,0.15)' : 'rgba(99,102,241,0.15)',
                        border: `1px solid ${copiedPrompt ? 'rgba(16,185,129,0.3)' : 'rgba(99,102,241,0.3)'}`,
                        color: copiedPrompt ? '#10b981' : '#818cf8',
                      }}
                    >
                      {copiedPrompt ? '✓ Copied!' : 'Copy Prompt'}
                    </button>
                    <a
                      href="https://ideogram.ai/t/explore"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[10px] px-2.5 py-1 rounded-lg font-medium no-underline"
                      style={{ background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.3)', color: '#818cf8' }}
                    >
                      Open Ideogram ↗
                    </a>
                  </div>
                </div>
                <p className="text-xs text-white/50 leading-relaxed italic">{localVariant.ideogram_prompt}</p>
              </div>
            )}

            {/* ── Actions ── */}
            <div className="flex gap-3 pt-2 border-t border-white/10">
              {localVariant.logo_svg && (
                <button
                  onClick={() => downloadSVG(localVariant)}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-white text-slate-900 font-bold hover:bg-white/90 transition-all text-sm"
                >
                  ↓ Download SVG
                </button>
              )}
              <button
                onClick={handleCopyPrompt}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-300 font-bold hover:bg-indigo-600/30 transition-all text-sm"
              >
                Copy Ideogram Prompt
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Font picker rendered outside the scrollable modal */}
      {fontPicker && (
        <FontPickerModal
          type={fontPicker}
          currentFont={fontPicker === 'heading' ? headingFont : bodyFont}
          onSelect={(font) => {
            fontPicker === 'heading' ? setHeadingFont(font) : setBodyFont(font);
            setFontPicker(null);
          }}
          onClose={() => setFontPicker(null)}
        />
      )}
    </>
  );
}

// ── Gallery Card ──────────────────────────────────────────────────────────────
function GalleryCard({ variant, onClick }) {
  useEffect(() => {
    loadGoogleFonts([variant.heading_font, variant.body_font]);
  }, [variant]);

  const badge = LOGO_TYPE_BADGE[variant.logo_type] || LOGO_TYPE_BADGE.abstract_mark;

  return (
    <button
      onClick={onClick}
      className="group text-left rounded-2xl border border-white/10 bg-white/[0.03] hover:bg-white/[0.06] hover:border-white/20 transition-all overflow-hidden"
    >
      <div
        className="w-full h-32 flex items-center justify-center border-b border-white/5"
        style={{ background: variant.color_palette?.[4] || '#f5f5f5' }}
      >
        {variant.logo_url
          ? <img src={variant.logo_url} alt={variant.variant_name} className="w-full h-full object-contain p-3" />
          : <span className="text-4xl opacity-30">🎨</span>}
      </div>

      <div className="p-3 space-y-2">
        <div className="flex items-start justify-between gap-1">
          <div className="text-xs font-bold text-white leading-tight">{variant.variant_name}</div>
          <span className="text-white/20 group-hover:text-white/50 transition-colors text-xs flex-shrink-0">↗</span>
        </div>

        <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold border ${badge.color}`}>
          {badge.label}
        </span>

        {/* Palette bar */}
        <div className="flex gap-0.5 rounded overflow-hidden h-4">
          {(variant.color_palette || []).map((hex, i) => (
            <div key={i} className="flex-1" style={{ backgroundColor: hex }} />
          ))}
        </div>

        {/* Font in its own face */}
        <div
          className="text-[10px] text-white/50 truncate"
          style={{ fontFamily: `'${variant.heading_font}', sans-serif` }}
        >
          {variant.heading_font}
        </div>
      </div>
    </button>
  );
}

// ── Main Export ───────────────────────────────────────────────────────────────
export default function VariantGallery({ data, projectId, onRegenerate }) {
  const [localVariants, setLocalVariants] = useState([]);
  const [selected, setSelected]           = useState(null);
  const [filter, setFilter]               = useState('all');

  useEffect(() => {
    const variants = Array.isArray(data?.variants) ? data.variants : [];
    setLocalVariants(variants);
    loadGoogleFonts(variants.flatMap((v) => [v.heading_font, v.body_font]));
  }, [data]);

  const handleVariantUpdated = useCallback((index, updatedVariant) => {
    setLocalVariants((prev) => {
      const next = [...prev];
      next[index] = updatedVariant;
      return next;
    });
    setSelected({ variant: updatedVariant, index });
  }, []);

  if (!data || localVariants.length === 0) return null;

  const logoTypes = ['all', ...new Set(localVariants.map((v) => v.logo_type).filter(Boolean))];
  const filtered  = filter === 'all' ? localVariants : localVariants.filter((v) => v.logo_type === filter);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-2xl font-black text-white uppercase tracking-tight">Brand Variants</h2>
          <p className="text-white/40 text-sm mt-1">
            {localVariants.length} variants · {localVariants.filter((v) => v.logo_svg).length} with SVG logos
          </p>
        </div>
        {onRegenerate && (
          <button
            onClick={() => onRegenerate('visual_identity_agent', 'regenerate all brand variants with fresh creative directions')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 text-white/70 hover:text-white transition-all text-sm font-semibold"
          >
            🔄 Regenerate All
          </button>
        )}
      </div>

      {/* Logo type filter */}
      <div className="flex gap-2 flex-wrap">
        {logoTypes.map((type) => {
          const badge = LOGO_TYPE_BADGE[type];
          return (
            <button
              key={type}
              onClick={() => setFilter(type)}
              className={`px-3 py-1.5 rounded-full text-[11px] font-bold border transition-all ${
                filter === type
                  ? (badge ? badge.color : 'bg-white/20 text-white border-white/30')
                  : 'bg-white/5 border-white/10 text-white/50 hover:text-white/70'
              }`}
            >
              {badge ? badge.label : 'All'}
            </button>
          );
        })}
      </div>

      {/* Gallery grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">
        {filtered.map((variant) => {
          const realIndex = localVariants.indexOf(variant);
          return (
            <GalleryCard
              key={realIndex}
              variant={variant}
              onClick={() => setSelected({ variant, index: realIndex })}
            />
          );
        })}
      </div>

      {/* Modal */}
      {selected && (
        <VariantModal
          variant={selected.variant}
          variantIndex={selected.index}
          projectId={projectId}
          onClose={() => setSelected(null)}
          onUpdated={handleVariantUpdated}
        />
      )}
    </div>
  );
}
