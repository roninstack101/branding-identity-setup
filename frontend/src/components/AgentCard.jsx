import { useState } from 'react';
import ColorPalette from './ColorPalette';

const AGENT_META = {
  idea_discovery:      { icon: '💡', label: 'Idea Discovery' },
  market_research:     { icon: '📊', label: 'Market Research' },
  competitor_analysis: { icon: '🔍', label: 'Competitor Analysis' },
  brand_strategy:      { icon: '🎯', label: 'Brand Strategy' },
  naming:              { icon: '✏️', label: 'Brand Naming' },
  visual_identity_agent:{ icon: '🎨', label: 'Visual Identity Direction' },
  design_agent:        { icon: '🎨', label: 'Design Direction' },
  logo_generator:      { icon: '🖼️', label: 'Logo Output' },
  content_agent:       { icon: '📝', label: 'Brand Content' },
  guidelines_agent:    { icon: '📋', label: 'Brand Guidelines' },
  export_agent:        { icon: '📦', label: 'Export & Download' },
};

const HIDDEN_KEYS = ['logo_base64'];

function toLabel(value = '') {
  return String(value)
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function isPrimitive(value) {
  return ['string', 'number', 'boolean'].includes(typeof value);
}

function looksLikeUrl(value = '') {
  return /^https?:\/\//i.test(String(value));
}

function primitiveToText(value) {
  if (value === null || value === undefined || value === '') return 'N/A';
  return String(value);
}

function splitExplanation(explanation = '') {
  return explanation
    .split(/(?<=[.!?])\s+/)
    .map((part) => part.trim())
    .filter(Boolean)
    .slice(0, 6);
}

function buildHighlights(data = {}) {
  const entries = Object.entries(data || {}).filter(([key]) => !HIDDEN_KEYS.includes(key));
  const highlights = [];

  for (const [key, value] of entries) {
    if (highlights.length >= 6) break;

    if (isPrimitive(value)) {
      highlights.push({ title: toLabel(key), value: primitiveToText(value) });
      continue;
    }

    if (Array.isArray(value) && value.length > 0 && value.every((item) => isPrimitive(item))) {
      highlights.push({ title: toLabel(key), value: value.slice(0, 3).join(' • ') });
      continue;
    }

    if (value && typeof value === 'object' && !Array.isArray(value)) {
      const primitiveChild = Object.entries(value).find(([, child]) => isPrimitive(child));
      if (primitiveChild) {
        highlights.push({
          title: `${toLabel(key)} • ${toLabel(primitiveChild[0])}`,
          value: primitiveToText(primitiveChild[1]),
        });
      }
    }
  }

  return highlights;
}

function TypographySection({ typography }) {
  if (!typography) return null;

  const items = [
    { label: 'Heading Font', value: typography.heading_font, url: typography.google_fonts_specimen?.heading || typography.heading_font_url },
    { label: 'Body Font', value: typography.body_font, url: typography.google_fonts_specimen?.body || typography.body_font_url },
    { label: 'Accent Font', value: typography.accent_font, url: typography.google_fonts_specimen?.accent || typography.accent_font_url },
  ].filter((item) => item.value);

  return (
    <div className="space-y-3">
      <h4 className="text-[10px] font-black text-white/40 uppercase tracking-[0.2em]">Typography</h4>
      <div className="grid gap-3 md:grid-cols-3">
        {items.map((item) => (
          <a
            key={item.label}
            href={item.url || '#'}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-xl border border-white/10 bg-white/[0.03] p-4 hover:bg-white/[0.06] hover:border-cyan-400/30 transition-all"
          >
            <div className="text-[10px] font-black uppercase tracking-[0.18em] text-cyan-200/80 mb-2">{item.label}</div>
            <div className="text-lg font-semibold text-white leading-tight">{item.value}</div>
            {typography.font_provider && (
              <div className="mt-2 text-[11px] text-white/40">{typography.font_provider}</div>
            )}
          </a>
        ))}
      </div>
      {typography.font_reason && (
        <p className="text-sm text-white/50 leading-relaxed">{typography.font_reason}</p>
      )}
    </div>
  );
}

function PrimitiveValue({ value }) {
  const text = primitiveToText(value);
  if (looksLikeUrl(text)) {
    return (
      <a
        href={text}
        target="_blank"
        rel="noopener noreferrer"
        className="text-cyan-300 hover:text-cyan-200 underline decoration-cyan-500/30 break-all"
      >
        {text}
      </a>
    );
  }

  return <span className="text-white/80 break-words">{text}</span>;
}

function StructuredValue({ data, depth = 0 }) {
  if (data === null || data === undefined) {
    return <span className="text-white/30">N/A</span>;
  }

  if (isPrimitive(data)) {
    return <PrimitiveValue value={data} />;
  }

  if (Array.isArray(data)) {
    if (data.length === 0) {
      return <span className="text-white/30">No items</span>;
    }

    const allPrimitive = data.every((item) => isPrimitive(item));
    if (allPrimitive) {
      return (
        <div className="flex flex-wrap gap-2">
          {data.map((item, index) => (
            <span
              key={index}
              className="px-3 py-1.5 rounded-full text-xs font-semibold bg-blue-500/10 border border-blue-500/20 text-blue-200"
            >
              {primitiveToText(item)}
            </span>
          ))}
        </div>
      );
    }

    return (
      <div className="space-y-3">
        {data.map((item, index) => (
          <div key={index} className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
            <div className="text-[10px] font-black uppercase tracking-[0.18em] text-white/30 mb-3">Item {index + 1}</div>
            <StructuredValue data={item} depth={depth + 1} />
          </div>
        ))}
      </div>
    );
  }

  if (typeof data === 'object') {
    const entries = Object.entries(data).filter(([key]) => !HIDDEN_KEYS.includes(key));
    if (!entries.length) {
      return <span className="text-white/30">No fields</span>;
    }

    if (depth >= 3) {
      return (
        <pre className="text-xs text-white/70 bg-black/30 rounded-lg p-3 overflow-x-auto border border-white/10">
          {JSON.stringify(data, null, 2)}
        </pre>
      );
    }

    return (
      <div className="space-y-3">
        {entries.map(([key, value]) => (
          <div key={key} className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
            <div className="text-[10px] font-black uppercase tracking-[0.18em] text-cyan-200/80 mb-2">{toLabel(key)}</div>
            <StructuredValue data={value} depth={depth + 1} />
          </div>
        ))}
      </div>
    );
  }

  return <span className="text-white/70">{String(data)}</span>;
}

export default function AgentCard({ agentName, output, onRegenerate, isExpanded, onToggle }) {
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackText, setFeedbackText] = useState('');
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [activeTab, setActiveTab] = useState('structure');

  const meta = AGENT_META[agentName] || { icon: '🤖', label: agentName };
  const canRegenerate = ['visual_identity_agent', 'content_agent', 'design_agent', 'logo_generator'].includes(agentName);

  if (!output) return null;

  const { output_json, explanation, version, created_at } = output;
  const visibleOutput = Object.fromEntries(
    Object.entries(output_json || {}).filter(([key]) => !HIDDEN_KEYS.includes(key))
  );
  const explanationPoints = splitExplanation(explanation);
  const highlights = buildHighlights(visibleOutput);

  const handleRegenerateClick = async () => {
    if (feedbackText.trim().length < 3) return;
    setIsRegenerating(true);
    try {
      await onRegenerate(agentName, feedbackText.trim());
      setShowFeedback(false);
      setFeedbackText('');
    } finally {
      setIsRegenerating(false);
    }
  };

  return (
    <div className="glass-card overflow-hidden transition-all duration-300 hover:border-blue-500/50" id={`agent-${agentName}`}>
      {/* Header */}
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-6 text-left group hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center gap-4 flex-1 min-w-0">
          <span className="text-3xl flex-shrink-0">{meta.icon}</span>
          <div className="min-w-0 flex-1">
            <h3 className="text-lg font-semibold text-white group-hover:text-blue-300 transition-colors">
              {meta.label}
            </h3>
            <p className="text-white/40 text-sm mt-0.5">
              v{version} • {new Date(created_at).toLocaleString()}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0 ml-4">
          {canRegenerate && (
            <span className="px-2 py-1 text-[9px] font-black text-cyan-300 bg-cyan-500/10 border border-cyan-500/20 rounded-full font-mono uppercase tracking-widest">
              Swarm Iteration Available
            </span>
          )}
          <span className="px-3 py-1 text-[9px] font-black text-emerald-300 bg-emerald-500/10 border border-emerald-500/20 rounded-full font-mono uppercase tracking-widest">
            Verified Output
          </span>
          <svg
            className={`w-5 h-5 text-white/40 transition-transform duration-300 flex-shrink-0 ${isExpanded ? 'rotate-180' : ''}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {/* Expandable Content */}
      {isExpanded && (
        <div className="border-t border-white/5 animate-fade-in">
          <div className="px-6 pt-5 pb-2">
            <div className="flex flex-wrap gap-2">
              {[
                { key: 'highlights', label: 'Highlights' },
                { key: 'structure', label: 'Structured View' },
                { key: 'raw', label: 'Raw JSON' },
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`px-4 py-2 rounded-full text-[11px] font-black uppercase tracking-[0.16em] transition-all ${
                    activeTab === tab.key
                      ? 'bg-blue-500/20 border border-blue-400/40 text-blue-200'
                      : 'bg-white/5 border border-white/10 text-white/50 hover:text-white/70 hover:bg-white/10'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          <div className="px-6 py-4">
            <div className="bg-white/[0.02] rounded-2xl p-5 max-h-[540px] overflow-y-auto border border-white/5 shadow-inner space-y-5">
              {activeTab === 'highlights' && (
                <>
                  {explanationPoints.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="text-[10px] font-black text-blue-300 uppercase tracking-[0.2em] opacity-70">
                        Strategic Summary
                      </h4>
                      <div className="grid gap-3 md:grid-cols-2">
                        {explanationPoints.map((point, index) => (
                          <div key={index} className="rounded-xl border border-blue-500/20 bg-blue-500/5 p-4">
                            <div className="text-[10px] font-black uppercase tracking-[0.18em] text-blue-300/70 mb-2">Insight {index + 1}</div>
                            <p className="text-sm text-white/80 leading-relaxed">{point}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="space-y-3">
                    <h4 className="text-[10px] font-black text-white/40 uppercase tracking-[0.2em]">
                      Key Output Signals
                    </h4>
                    {highlights.length ? (
                      <div className="grid gap-3 md:grid-cols-2">
                        {highlights.map((item, index) => (
                          <div key={`${item.title}-${index}`} className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                            <div className="text-[10px] font-black uppercase tracking-[0.18em] text-cyan-200/80 mb-2">{item.title}</div>
                            <p className="text-sm text-white/80 leading-relaxed">{item.value}</p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-white/40">No highlight fields available for this output yet.</p>
                    )}
                  </div>
                </>
              )}

              {activeTab === 'structure' && (
                <>
                  {(agentName === 'visual_identity_agent' || agentName === 'design_agent') && visibleOutput.color_palette && (
                    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                      <ColorPalette palette={visibleOutput.color_palette} />
                    </div>
                  )}
                  {(agentName === 'visual_identity_agent' || agentName === 'design_agent') && visibleOutput.typography && (
                    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                      <TypographySection typography={visibleOutput.typography} />
                    </div>
                  )}
                  <StructuredValue data={visibleOutput} />
                </>
              )}

              {activeTab === 'raw' && (
                <pre className="text-xs leading-relaxed text-white/70 bg-black/35 rounded-xl p-4 overflow-x-auto border border-white/10">
                  {JSON.stringify(visibleOutput, null, 2)}
                </pre>
              )}
            </div>
          </div>

          {/* Regenerate Action Area */}
          {canRegenerate && onRegenerate && (
            <div className="px-6 py-6 border-t border-white/5 bg-white/[0.01]">
              {!showFeedback ? (
                <button
                  onClick={() => setShowFeedback(true)}
                  className="flex items-center gap-3 px-6 py-3 rounded-xl bg-blue-600/10 hover:bg-blue-600/20 border border-blue-600/30 hover:border-blue-600/50 text-blue-400 font-bold transition-all text-xs uppercase tracking-widest active:scale-95 group"
                >
                  <span className="text-lg group-hover:rotate-180 transition-transform duration-500">🔄</span>
                  <span>TRIGGER SWARM ITERATION</span>
                </button>
              ) : (
                <div className="space-y-4 animate-fade-in-up">
                  <div className="space-y-2">
                    <label className="text-[10px] font-black text-white/30 uppercase tracking-[0.2em]">Feedback Loop</label>
                    <textarea
                      value={feedbackText}
                      onChange={(e) => setFeedbackText(e.target.value)}
                      placeholder='e.g. "make the colors more vibrant" or "it feels too corporate"'
                      rows={3}
                      className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-xl text-white placeholder-white/20 focus:outline-none focus:border-blue-500/50 transition-all font-medium text-sm resize-none"
                    />
                  </div>
                  <div className="flex gap-3">
                    <button
                      onClick={handleRegenerateClick}
                      disabled={isRegenerating || feedbackText.trim().length < 3}
                      className="flex-1 flex items-center justify-center gap-3 px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed text-xs uppercase tracking-widest"
                    >
                      {isRegenerating ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          <span>PROCESSING...</span>
                        </>
                      ) : (
                        <span>SUBMIT FEEDBACK</span>
                      )}
                    </button>
                    <button
                      onClick={() => { setShowFeedback(false); setFeedbackText(''); }}
                      className="px-6 py-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-white/60 font-bold transition-all text-xs uppercase tracking-widest"
                    >
                      CANCEL
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
