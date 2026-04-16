import { useState } from 'react';

// ── Archetype config ──────────────────────────────────────────────────────────
const ARCHETYPE_COLORS = {
  'Interlocked Monogram': { color: '#818cf8', bg: 'rgba(129,140,248,0.1)',  border: 'rgba(129,140,248,0.25)' },
  'Ecosystem Orbit':      { color: '#34d399', bg: 'rgba(52,211,153,0.1)',   border: 'rgba(52,211,153,0.25)'  },
  'Growth Stack':         { color: '#60a5fa', bg: 'rgba(96,165,250,0.1)',   border: 'rgba(96,165,250,0.25)'  },
  'Bridge Arc':           { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)',   border: 'rgba(245,158,11,0.25)'  },
  'Tri-form Overlap':     { color: '#c084fc', bg: 'rgba(192,132,252,0.1)',  border: 'rgba(192,132,252,0.25)' },
  'Network Nodes':        { color: '#38bdf8', bg: 'rgba(56,189,248,0.1)',   border: 'rgba(56,189,248,0.25)'  },
  'Dynamic Sweep':        { color: '#fb923c', bg: 'rgba(251,146,60,0.1)',   border: 'rgba(251,146,60,0.25)'  },
  'Digital Grid':         { color: '#a3e635', bg: 'rgba(163,230,53,0.1)',   border: 'rgba(163,230,53,0.25)'  },
  'Globe / Planet':       { color: '#2dd4bf', bg: 'rgba(45,212,191,0.1)',   border: 'rgba(45,212,191,0.25)'  },
  'Journey Swoosh + Dot': { color: '#f472b6', bg: 'rgba(244,114,182,0.1)',  border: 'rgba(244,114,182,0.25)' },
};

function getArchetypeStyle(approach = '') {
  for (const [key, val] of Object.entries(ARCHETYPE_COLORS)) {
    if (approach.includes(key.split('/')[0].trim())) return val;
  }
  return { color: '#94a3b8', bg: 'rgba(148,163,184,0.1)', border: 'rgba(148,163,184,0.2)' };
}

// ── Copy hook ─────────────────────────────────────────────────────────────────
function useCopy(timeout = 2000) {
  const [copied, setCopied] = useState(false);
  const copy = (text) => {
    navigator.clipboard.writeText(text).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), timeout);
  };
  return [copied, copy];
}

// ── Generated Image Panel ─────────────────────────────────────────────────────
function GeneratedImagePanel({ imageUrl, imageModel, imageError, imagePrompt, onRegenerate }) {
  const [showPrompt, setShowPrompt] = useState(false);
  const [copied, copy] = useCopy();

  const hasImage = Boolean(imageUrl);

  // Download handler
  const handleDownload = () => {
    const a = document.createElement('a');
    a.href = imageUrl;
    a.download = 'logo-concepts.png';
    a.click();
  };

  if (!hasImage && imageError) {
    return (
      <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-8 text-center space-y-3">
        <div className="text-3xl opacity-40">⚠️</div>
        <div className="text-white/60 font-bold">Image generation failed</div>
        <div className="text-white/35 text-sm leading-relaxed max-w-md mx-auto">
          {imageError.includes('OPENAI_API_KEY') ? (
            <>OPENAI_API_KEY is missing in the backend <code className="bg-white/10 px-1 rounded">.env</code> file.</>
          ) : (
            imageError
          )}
          {imageError.includes('tier') && (
            <> gpt-image-1 requires OpenAI Tier 4+. DALL-E 3 requires an active paid plan.</>
          )}
        </div>
        {onRegenerate && (
          <button
            onClick={() => onRegenerate('visual_identity_agent', 'regenerate logo concepts image')}
            className="mt-2 px-5 py-2 rounded-xl bg-white/5 border border-white/15 text-white/60 hover:text-white hover:bg-white/10 text-sm font-bold transition-all"
          >
            Retry
          </button>
        )}
      </div>
    );
  }

  if (!hasImage) return null;

  return (
    <div className="space-y-3">
      {/* Image */}
      <div className="relative group rounded-2xl overflow-hidden border border-white/10">
        <img
          src={imageUrl}
          alt="10-concept logo design grid"
          className="w-full block"
          style={{ imageRendering: 'crisp-edges' }}
        />

        {/* Overlay actions */}
        <div className="absolute top-3 right-3 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          {imageModel && (
            <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-black/60 text-white/70 border border-white/15 backdrop-blur-sm">
              {imageModel}
            </span>
          )}
          <button
            onClick={handleDownload}
            className="px-3 py-1 rounded-full text-[10px] font-bold bg-black/60 text-white/90 border border-white/20 backdrop-blur-sm hover:bg-white/10 transition-all"
          >
            ↓ Download
          </button>
        </div>
      </div>

      {/* Image prompt toggle */}
      {imagePrompt && (
        <div className="rounded-xl border border-white/8 overflow-hidden">
          <button
            onClick={() => setShowPrompt((p) => !p)}
            className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-white/[0.02] transition-colors"
          >
            <span className="text-[11px] font-black uppercase tracking-[0.15em] text-white/30">
              Image Generation Prompt
            </span>
            <span className="text-white/20 text-xs">{showPrompt ? '▲' : '▼'}</span>
          </button>
          {showPrompt && (
            <div className="px-4 pb-4 space-y-2">
              <div className="flex justify-end">
                <button
                  onClick={() => copy(imagePrompt)}
                  className="text-[10px] px-2.5 py-1 rounded-lg font-bold transition-all"
                  style={{
                    background: copied ? 'rgba(16,185,129,0.15)' : 'rgba(255,255,255,0.05)',
                    border: `1px solid ${copied ? 'rgba(16,185,129,0.4)' : 'rgba(255,255,255,0.1)'}`,
                    color: copied ? '#10b981' : 'rgba(255,255,255,0.4)',
                  }}
                >
                  {copied ? '✓ Copied' : 'Copy'}
                </button>
              </div>
              <p className="text-[11px] text-white/35 leading-relaxed bg-white/[0.02] rounded-xl p-3 border border-white/5 italic">
                {imagePrompt}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Design Brief Panel ────────────────────────────────────────────────────────
function DesignBriefPanel({ briefText, competitorNotes, primaryColor, accentColor, font }) {
  const [expanded, setExpanded] = useState(false);

  if (!briefText) return null;

  // Render brief text with ━━━ headers styled
  const renderBrief = (text) => {
    return text.split('\n').map((line, i) => {
      if (line.startsWith('━━━')) {
        const title = line.replace(/━+/g, '').trim();
        return title ? (
          <div key={i} className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40 mt-5 mb-2 pt-3 border-t border-white/5">
            {title}
          </div>
        ) : null;
      }
      if (line.startsWith('•') || line.startsWith('-')) {
        return <div key={i} className="text-[11px] text-white/45 leading-relaxed pl-3">{line}</div>;
      }
      if (line.trim() === '') return <div key={i} className="h-1" />;
      return <div key={i} className="text-[11px] text-white/50 leading-relaxed">{line}</div>;
    });
  };

  return (
    <div className="rounded-2xl border border-white/8 overflow-hidden">
      <button
        onClick={() => setExpanded((e) => !e)}
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
          {/* Design tokens */}
          <div className="hidden sm:flex items-center gap-2">
            {primaryColor && (
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full border border-white/20" style={{ backgroundColor: primaryColor }} />
                <span className="text-[9px] text-white/30 font-mono">{primaryColor}</span>
              </div>
            )}
            {accentColor && (
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full border border-white/20" style={{ backgroundColor: accentColor }} />
                <span className="text-[9px] text-white/30 font-mono">{accentColor}</span>
              </div>
            )}
            {font && <span className="text-[9px] text-white/30">{font}</span>}
          </div>
          <span className="text-white/25 text-xs">{expanded ? '▲' : '▼'}</span>
        </div>
      </button>

      {expanded && (
        <div className="px-5 pb-5 space-y-1">
          {competitorNotes && (
            <div className="mb-4 p-3 rounded-xl bg-amber-500/5 border border-amber-500/15">
              <div className="text-[9px] font-black uppercase tracking-[0.2em] text-amber-400/60 mb-1">
                Competitor Visual Research
              </div>
              <p className="text-[11px] text-amber-100/50 leading-relaxed">{competitorNotes}</p>
            </div>
          )}
          <div className="space-y-0.5">{renderBrief(briefText)}</div>
        </div>
      )}
    </div>
  );
}

// ── Concept Card ──────────────────────────────────────────────────────────────
function ConceptCard({ concept }) {
  const style = getArchetypeStyle(concept.approach || '');

  return (
    <div
      className="rounded-2xl p-4 space-y-2 border"
      style={{ background: style.bg, borderColor: style.border }}
    >
      <div className="flex items-start gap-2">
        <span
          className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-black flex-shrink-0 mt-0.5"
          style={{ background: style.border, color: style.color }}
        >
          {concept.number}
        </span>
        <div className="min-w-0">
          <div className="text-sm font-black text-white/85 leading-tight">{concept.name}</div>
          <div className="text-[10px] font-bold mt-0.5" style={{ color: style.color }}>
            {concept.approach}
          </div>
        </div>
      </div>
      {concept.rationale && (
        <p className="text-[11px] text-white/45 leading-relaxed pl-8">{concept.rationale}</p>
      )}
    </div>
  );
}

// ── Main Export ───────────────────────────────────────────────────────────────
export default function VariantGallery({ data, projectId, onRegenerate }) {
  if (!data) return null;

  const imageUrl       = data.logo_image_url   || '';
  const imageModel     = data.logo_image_model  || '';
  const imageError     = data.logo_image_error  || '';
  const briefText      = data.logo_design_brief || '';
  const imagePrompt    = data.logo_image_prompt  || '';
  const concepts       = Array.isArray(data.design_concepts) ? data.design_concepts : [];
  const primaryColor   = data.primary_color     || '';
  const accentColor    = data.accent_color      || '';
  const font           = data.font              || '';
  const compNotes      = data.competitor_visual_notes || '';

  const hasAnything = imageUrl || briefText || concepts.length > 0;

  if (!hasAnything) {
    return (
      <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-8 text-center space-y-3">
        <div className="text-3xl opacity-40">⚠️</div>
        <div className="text-white/60 font-bold">Visual Identity data is empty</div>
        <div className="text-white/35 text-sm leading-relaxed max-w-md mx-auto">
          The visual identity agent returned no data. Check that{' '}
          <span className="text-amber-300/80">OPENAI_API_KEY</span> and{' '}
          <span className="text-amber-300/80">GEMINI_API_KEY</span> are set in the backend{' '}
          <code className="bg-white/10 px-1 rounded">.env</code> file.
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
            10 distinct visual directions — researched & designed by Gemini + rendered by{' '}
            {imageModel || 'OpenAI'}
          </p>
        </div>
        {onRegenerate && (
          <button
            onClick={() => onRegenerate('visual_identity_agent', 'regenerate logo concepts with fresh visual directions')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 text-white/70 hover:text-white transition-all text-sm font-semibold"
          >
            Regenerate
          </button>
        )}
      </div>

      {/* How it works callout */}
      <div className="flex items-start gap-3 p-4 rounded-2xl bg-indigo-500/5 border border-indigo-500/15">
        <span className="text-indigo-400 text-lg flex-shrink-0">✦</span>
        <div className="text-xs text-white/45 leading-relaxed">
          <span className="text-indigo-300 font-bold">Gemini</span> researched your competitors online and generated a
          brand-tailored 10-concept design brief. <span className="text-amber-300 font-bold">OpenAI</span> rendered the
          visual grid. Use it as a reference for your designer or paste individual concept descriptions into Midjourney / Ideogram.
        </div>
      </div>

      {/* Generated image */}
      <GeneratedImagePanel
        imageUrl={imageUrl}
        imageModel={imageModel}
        imageError={imageError}
        imagePrompt={imagePrompt}
        onRegenerate={onRegenerate}
      />

      {/* Design tokens row */}
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

      {/* 10 Concept cards */}
      {concepts.length > 0 && (
        <div className="space-y-3">
          <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30">
            10 Visual Concepts
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {concepts.map((c) => (
              <ConceptCard key={c.number} concept={c} />
            ))}
          </div>
        </div>
      )}

      {/* Design brief */}
      <DesignBriefPanel
        briefText={briefText}
        competitorNotes={compNotes}
        primaryColor={primaryColor}
        accentColor={accentColor}
        font={font}
      />
    </div>
  );
}
