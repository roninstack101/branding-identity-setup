import { useState } from 'react';
import { selectBrandName } from '../services/api';

const STYLE_BADGE = {
  'Modern Abstract': 'bg-cyan-500/15 text-cyan-300 border-cyan-500/25',
  'Portmanteau':     'bg-violet-500/15 text-violet-300 border-violet-500/25',
  'Real Word':       'bg-emerald-500/15 text-emerald-300 border-emerald-500/25',
  'Latin/Greek Root':'bg-amber-500/15 text-amber-300 border-amber-500/25',
};

function styleBadgeClass(style = '') {
  for (const [key, cls] of Object.entries(STYLE_BADGE)) {
    if (style.toLowerCase().includes(key.toLowerCase())) return cls;
  }
  return 'bg-white/10 text-white/60 border-white/15';
}

export default function NamingCards({ data, originalName, projectId }) {
  const [expanded, setExpanded]       = useState(null);
  const [selectedName, setSelectedName] = useState(null); // null = use AI recommended
  const [saving, setSaving]           = useState(false);
  const [saveError, setSaveError]     = useState('');
  const [saveSuccess, setSaveSuccess] = useState('');

  if (!data) return null;

  const recommended = data.brand_name;
  const candidates  = Array.isArray(data.name_candidates) ? data.name_candidates : [];
  // activeName: what's currently selected (null means AI recommended)
  const activeName  = selectedName ?? recommended;

  const handleSelect = async (name) => {
    if (name === activeName) return; // already selected
    setSaving(true);
    setSaveError('');
    setSaveSuccess('');
    try {
      await selectBrandName(projectId, name);
      setSelectedName(name);
      setSaveSuccess(`"${name}" will be used for all subsequent steps.`);
      setTimeout(() => setSaveSuccess(''), 3000);
    } catch (e) {
      setSaveError(e.response?.data?.detail || 'Failed to save selection');
    } finally {
      setSaving(false);
    }
  };

  const isActive = (name) => name === activeName;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-1">
        <h2 className="text-2xl font-black text-white uppercase tracking-tight">Brand Names</h2>
        <p className="text-white/40 text-sm">
          {candidates.length} candidates generated · Strategy: {data.naming_strategy || '—'}
        </p>
      </div>

      {/* Status feedback */}
      {saveSuccess && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-sm">
          <span>✓</span> {saveSuccess}
        </div>
      )}
      {saveError && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 text-sm">
          <span>⚠</span> {saveError}
        </div>
      )}

      {/* Active name hero */}
      <div className={`relative rounded-2xl border p-7 overflow-hidden transition-all ${
        activeName !== recommended
          ? 'border-emerald-500/30 bg-gradient-to-br from-emerald-500/10 to-teal-500/5'
          : 'border-blue-500/30 bg-gradient-to-br from-blue-500/10 to-cyan-500/5'
      }`}>
        <div className={`absolute top-4 right-4 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border ${
          activeName !== recommended
            ? 'bg-emerald-500/20 border-emerald-400/30 text-emerald-300'
            : 'bg-blue-500/20 border-blue-400/30 text-blue-300'
        }`}>
          {activeName !== recommended ? '✓ Your Selection' : '★ AI Recommended'}
        </div>
        <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30 mb-2">
          Active Brand Name
        </div>
        <div className="text-5xl font-black text-white tracking-tight">{activeName}</div>
        {activeName === recommended && data.tagline && (
          <div className="mt-3 text-lg text-white/60 font-medium italic">"{data.tagline}"</div>
        )}
        {activeName === recommended && data.brand_story_hook && (
          <p className="mt-4 text-sm text-white/50 leading-relaxed max-w-xl">{data.brand_story_hook}</p>
        )}
        <p className="mt-3 text-xs text-white/30">
          This name will be used in Visual Identity, Content, and Guidelines.
        </p>
      </div>

      {/* Original name option */}
      {originalName && (
        <div>
          <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30 mb-3">
            Your Original Name
          </div>
          <button
            onClick={() => handleSelect(originalName)}
            disabled={saving}
            className={`w-full text-left rounded-2xl border p-5 flex items-center justify-between gap-4 transition-all disabled:opacity-60 ${
              isActive(originalName)
                ? 'border-emerald-400/40 bg-emerald-500/10'
                : 'border-white/10 bg-white/[0.03] hover:bg-white/[0.06] hover:border-white/20'
            }`}
          >
            <div className="flex items-center gap-3">
              <span className="text-xl">✍️</span>
              <div>
                <div className="text-xl font-black text-white">{originalName}</div>
                <div className="text-xs text-white/40 mt-0.5">As you originally named it</div>
              </div>
            </div>
            <span className={`flex-shrink-0 text-xs font-black px-3 py-1.5 rounded-lg border transition-all ${
              isActive(originalName)
                ? 'bg-emerald-500/20 border-emerald-400/30 text-emerald-300'
                : 'bg-white/5 border-white/10 text-white/40'
            }`}>
              {saving && isActive(originalName) ? '…' : isActive(originalName) ? '✓ Selected' : 'Select'}
            </span>
          </button>
        </div>
      )}

      {/* AI candidate grid */}
      <div>
        <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30 mb-3">
          AI-Generated Candidates
        </div>
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
          {candidates.map((c, i) => {
            const isExpanded    = expanded === i;
            const isSelected    = isActive(c.name);
            const isRecommended = c.name === recommended;
            return (
              <div
                key={i}
                className={`rounded-2xl border transition-all ${
                  isSelected
                    ? 'border-emerald-400/30 bg-emerald-500/5'
                    : isRecommended
                    ? 'border-blue-400/20 bg-blue-500/5'
                    : 'border-white/10 bg-white/[0.03] hover:bg-white/[0.05]'
                }`}
              >
                <div className="p-5 space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="text-xl font-black text-white truncate">{c.name}</div>
                      {c.domain_suggestion && (
                        <div className="text-xs text-white/40 mt-1 font-mono truncate">{c.domain_suggestion}</div>
                      )}
                    </div>
                    <div className="flex flex-col items-end gap-2 flex-shrink-0">
                      {isRecommended && <span className="text-yellow-400">★</span>}
                      <button
                        onClick={() => handleSelect(c.name)}
                        disabled={saving || isSelected}
                        className={`text-[10px] font-black px-2.5 py-1 rounded-lg border transition-all disabled:cursor-default ${
                          isSelected
                            ? 'bg-emerald-500/20 border-emerald-400/30 text-emerald-300'
                            : 'bg-white/5 border-white/10 text-white/40 hover:text-white hover:bg-white/10'
                        }`}
                      >
                        {saving && isSelected ? '…' : isSelected ? '✓' : 'Select'}
                      </button>
                    </div>
                  </div>

                  {c.style && (
                    <span className={`inline-block px-3 py-1 rounded-full text-[10px] font-bold border ${styleBadgeClass(c.style)}`}>
                      {c.style}
                    </span>
                  )}

                  <button
                    className="text-[10px] text-white/30 hover:text-white/60 transition-colors"
                    onClick={() => setExpanded(isExpanded ? null : i)}
                  >
                    {isExpanded ? '▲ Hide rationale' : '▼ Show rationale'}
                  </button>
                </div>

                {isExpanded && c.rationale && (
                  <div className="px-5 pb-5 border-t border-white/5 pt-4">
                    <p className="text-sm text-white/70 leading-relaxed">{c.rationale}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
