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
function useCopy(timeout = 2000) {
  const [copied, setCopied] = useState(false);
  const copy = (text) => {
    navigator.clipboard.writeText(text).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), timeout);
  };
  return [copied, copy];
}

// ── Prompt Block ──────────────────────────────────────────────────────────────
function PromptBlock({ label, icon, accentColor, borderColor, prompt }) {
  const [copiedMj,  copyMj]  = useCopy();
  const [copiedIdeo, copyIdeo] = useCopy();

  if (!prompt) return null;

  const { concept, midjourney_prompt, ideogram_prompt, designer_brief } = prompt;

  return (
    <div
      className="rounded-2xl p-5 space-y-4"
      style={{
        background: `linear-gradient(135deg, ${accentColor}10, ${accentColor}06)`,
        border: `1px solid ${borderColor}`,
      }}
    >
      {/* Header */}
      <div className="flex items-center gap-2">
        <span className="text-base">{icon}</span>
        <span className="text-sm font-black tracking-wide" style={{ color: accentColor }}>{label}</span>
      </div>

      {/* Concept */}
      {concept && (
        <div className="space-y-1">
          <div className="text-[10px] font-black uppercase tracking-[0.18em] text-white/30">Concept</div>
          <p className="text-xs text-white/60 leading-relaxed">{concept}</p>
        </div>
      )}

      {/* Midjourney / DALL-E prompt */}
      {midjourney_prompt && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="text-[10px] font-black uppercase tracking-[0.18em] text-white/30">Midjourney / DALL-E</div>
            <button
              onClick={() => copyMj(midjourney_prompt)}
              className="text-[10px] px-2.5 py-1 rounded-lg font-bold transition-all"
              style={{
                background: copiedMj ? 'rgba(16,185,129,0.15)' : 'rgba(255,255,255,0.05)',
                border: `1px solid ${copiedMj ? 'rgba(16,185,129,0.4)' : 'rgba(255,255,255,0.12)'}`,
                color: copiedMj ? '#10b981' : 'rgba(255,255,255,0.5)',
              }}
            >
              {copiedMj ? '✓ Copied' : 'Copy'}
            </button>
          </div>
          <p className="text-xs text-white/50 leading-relaxed font-mono bg-white/[0.03] rounded-lg p-3 border border-white/[0.06]">
            {midjourney_prompt}
          </p>
        </div>
      )}

      {/* Ideogram prompt */}
      {ideogram_prompt && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="text-[10px] font-black uppercase tracking-[0.18em] text-white/30">Ideogram AI</div>
            <div className="flex gap-2">
              <button
                onClick={() => copyIdeo(ideogram_prompt)}
                className="text-[10px] px-2.5 py-1 rounded-lg font-bold transition-all"
                style={{
                  background: copiedIdeo ? 'rgba(16,185,129,0.15)' : `${accentColor}18`,
                  border: `1px solid ${copiedIdeo ? 'rgba(16,185,129,0.4)' : borderColor}`,
                  color: copiedIdeo ? '#10b981' : accentColor,
                }}
              >
                {copiedIdeo ? '✓ Copied' : 'Copy'}
              </button>
              <a
                href="https://ideogram.ai/t/explore"
                target="_blank"
                rel="noopener noreferrer"
                className="text-[10px] px-2.5 py-1 rounded-lg font-bold no-underline transition-all"
                style={{ background: `${accentColor}18`, border: `1px solid ${borderColor}`, color: accentColor }}
              >
                Open ↗
              </a>
            </div>
          </div>
          <p className="text-xs text-white/50 leading-relaxed italic bg-white/[0.03] rounded-lg p-3 border border-white/[0.06]">
            {ideogram_prompt}
          </p>
        </div>
      )}

      {/* Designer brief */}
      {designer_brief && (
        <div className="space-y-1">
          <div className="text-[10px] font-black uppercase tracking-[0.18em] text-white/25">Designer Brief</div>
          <p className="text-xs text-white/40 leading-relaxed">{designer_brief}</p>
        </div>
      )}
    </div>
  );
}

// ── Font Picker Modal ─────────────────────────────────────────────────────────
function FontPickerModal({ type, currentFont, onSelect, onClose }) {
  const [search, setSearch] = useState('');

  const filtered = search.trim()
    ? { 'Search Results': ALL_FONTS.filter((f) => f.toLowerCase().includes(search.toLowerCase())) }
    : GOOGLE_FONTS_CATALOG;

  useEffect(() => { ALL_FONTS.forEach(loadFont); }, []);

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
                          style={{ fontFamily: `'${font}', sans-serif`, fontWeight: type === 'heading' ? 700 : 400 }}
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
  const [editedColors, setEditedColors] = useState([...(variant.color_palette || [])]);
  const [headingFont,  setHeadingFont]  = useState(variant.heading_font || '');
  const [bodyFont,     setBodyFont]     = useState(variant.body_font    || '');
  const [fontPicker,   setFontPicker]   = useState(null);
  const [regenerating, setRegenerating] = useState(false);
  const [regenError,   setRegenError]   = useState('');
  const [localVariant, setLocalVariant] = useState(variant);

  useGoogleFont(headingFont);
  useGoogleFont(bodyFont);

  const colorsChanged  = editedColors.some((c, i) => c !== (variant.color_palette || [])[i]);
  const headingChanged = headingFont !== (variant.heading_font || '');
  const bodyChanged    = bodyFont    !== (variant.body_font    || '');
  const anyChanged     = colorsChanged || headingChanged || bodyChanged;

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

  const primary   = editedColors[0] || '#6366f1';
  const secondary = editedColors[1] || '#8b5cf6';
  const bgColor   = editedColors[4] || '#f5f5f5';

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
            {/* ── Header ── */}
            <div>
              <h2
                className="text-2xl font-black text-white"
                style={{ fontFamily: `'${headingFont}', sans-serif` }}
              >
                {localVariant.variant_name}
              </h2>
              {localVariant.visual_strategy && (
                <p className="text-sm text-white/45 leading-relaxed mt-2">{localVariant.visual_strategy}</p>
              )}
            </div>

            {/* ── Brand Preview Strip ── */}
            <div
              className="rounded-2xl overflow-hidden border border-white/10"
              style={{ background: bgColor }}
            >
              <div className="px-8 py-10 flex flex-col items-center justify-center gap-2 min-h-[120px]">
                <div
                  className="text-3xl font-black tracking-tight leading-none"
                  style={{ fontFamily: `'${headingFont}', sans-serif`, color: primary }}
                >
                  {localVariant.variant_name}
                </div>
                <div
                  className="text-xs tracking-widest uppercase"
                  style={{ fontFamily: `'${bodyFont}', sans-serif`, color: secondary, opacity: 0.8 }}
                >
                  Brand Identity Preview
                </div>
                {/* Mini palette bar */}
                <div className="flex gap-1 mt-3">
                  {editedColors.map((hex, i) => (
                    <div key={i} className="w-6 h-6 rounded-full border-2 border-white/20" style={{ backgroundColor: hex }} />
                  ))}
                </div>
              </div>
            </div>

            {/* ── Logo Motivation ── */}
            {localVariant.logo_motivation && (
              <div className="rounded-xl p-4 bg-amber-500/5 border border-amber-500/20 space-y-1">
                <div className="text-[10px] font-black uppercase tracking-[0.18em] text-amber-400/70">Logo Motivation</div>
                <p className="text-xs text-white/55 leading-relaxed">{localVariant.logo_motivation}</p>
              </div>
            )}

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
                    Apply to update hex codes in all logo prompts
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
                    ? <><span className="w-3 h-3 border border-white/40 border-t-white rounded-full animate-spin" />Applying…</>
                    : '✦ Apply Changes'}
                </button>
              </div>
            )}

            {regenError && (
              <div className="text-sm text-red-300 bg-red-500/10 border border-red-500/20 rounded-xl p-3">⚠ {regenError}</div>
            )}

            {/* ── Wordmark Prompt ── */}
            <PromptBlock
              label="Wordmark Logo Prompt"
              icon="✍️"
              accentColor="#818cf8"
              borderColor="rgba(99,102,241,0.25)"
              prompt={localVariant.wordmark_prompt}
            />

            {/* ── Logomark Prompt ── */}
            <PromptBlock
              label="Logomark / Symbol Prompt"
              icon="◈"
              accentColor="#34d399"
              borderColor="rgba(52,211,153,0.25)"
              prompt={localVariant.logomark_prompt}
            />
          </div>
        </div>
      </div>

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

  const primary = variant.color_palette?.[0] || '#6366f1';
  const bg      = variant.color_palette?.[4] || '#f5f5f5';

  return (
    <button
      onClick={onClick}
      className="group text-left rounded-2xl border border-white/10 bg-white/[0.03] hover:bg-white/[0.06] hover:border-white/20 transition-all overflow-hidden"
    >
      {/* Brand preview area */}
      <div
        className="w-full h-32 flex flex-col items-center justify-center border-b border-white/5 gap-1 px-3"
        style={{ background: bg }}
      >
        <div
          className="text-base font-black tracking-tight text-center leading-tight truncate w-full text-center"
          style={{ fontFamily: `'${variant.heading_font}', sans-serif`, color: primary }}
        >
          {variant.variant_name}
        </div>
        <div className="flex gap-0.5 mt-1">
          {(variant.color_palette || []).slice(0, 4).map((hex, i) => (
            <div key={i} className="w-4 h-4 rounded-full border border-white/20" style={{ backgroundColor: hex }} />
          ))}
        </div>
      </div>

      <div className="p-3 space-y-2">
        <div className="flex items-start justify-between gap-1">
          <div className="text-xs font-bold text-white leading-tight">{variant.variant_name}</div>
          <span className="text-white/20 group-hover:text-white/50 transition-colors text-xs flex-shrink-0">↗</span>
        </div>

        {/* Palette bar */}
        <div className="flex gap-0.5 rounded overflow-hidden h-3">
          {(variant.color_palette || []).map((hex, i) => (
            <div key={i} className="flex-1" style={{ backgroundColor: hex }} />
          ))}
        </div>

        {/* Fonts */}
        <div className="flex gap-1.5 flex-wrap">
          {variant.heading_font && (
            <span
              className="text-[9px] px-1.5 py-0.5 rounded-md bg-cyan-500/10 border border-cyan-500/20 text-cyan-300/70 truncate max-w-[80px]"
              style={{ fontFamily: `'${variant.heading_font}', sans-serif` }}
            >
              {variant.heading_font}
            </span>
          )}
          {variant.body_font && (
            <span
              className="text-[9px] px-1.5 py-0.5 rounded-md bg-violet-500/10 border border-violet-500/20 text-violet-300/70 truncate max-w-[80px]"
              style={{ fontFamily: `'${variant.body_font}', sans-serif` }}
            >
              {variant.body_font}
            </span>
          )}
        </div>

        {/* Prompt indicators */}
        <div className="flex gap-1">
          {variant.wordmark_prompt && (
            <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300/70">
              ✍ Wordmark
            </span>
          )}
          {variant.logomark_prompt && (
            <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-300/70">
              ◈ Logomark
            </span>
          )}
        </div>
      </div>
    </button>
  );
}

// ── Main Export ───────────────────────────────────────────────────────────────
export default function VariantGallery({ data, projectId, onRegenerate }) {
  const [localVariants, setLocalVariants] = useState([]);
  const [selected, setSelected]           = useState(null);

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

  const withWordmark  = localVariants.filter((v) => v.wordmark_prompt).length;
  const withLogomark  = localVariants.filter((v) => v.logomark_prompt).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-2xl font-black text-white uppercase tracking-tight">Brand Variants</h2>
          <p className="text-white/40 text-sm mt-1">
            {localVariants.length} variants · {withWordmark} wordmark prompts · {withLogomark} logomark prompts
          </p>
        </div>
        {onRegenerate && (
          <button
            onClick={() => onRegenerate('visual_identity_agent', 'regenerate all brand variants with fresh creative directions')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 text-white/70 hover:text-white transition-all text-sm font-semibold"
          >
            Regenerate All
          </button>
        )}
      </div>

      {/* Info callout */}
      <div className="flex items-start gap-3 p-4 rounded-2xl bg-indigo-500/5 border border-indigo-500/15">
        <span className="text-indigo-400 text-lg flex-shrink-0">✦</span>
        <div className="text-xs text-white/45 leading-relaxed">
          Each variant includes a <span className="text-indigo-300 font-bold">Wordmark prompt</span> (text-based logo) and a{' '}
          <span className="text-emerald-300 font-bold">Logomark prompt</span> (symbol/icon) — ready for{' '}
          <strong className="text-white/60">Ideogram AI</strong>, <strong className="text-white/60">Midjourney</strong>, or a human designer.
          Click any variant to copy the prompts.
        </div>
      </div>

      {/* Gallery grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-3 gap-4">
        {localVariants.map((variant, realIndex) => (
          <GalleryCard
            key={realIndex}
            variant={variant}
            onClick={() => setSelected({ variant, index: realIndex })}
          />
        ))}
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
