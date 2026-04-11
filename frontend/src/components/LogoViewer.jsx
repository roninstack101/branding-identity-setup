/**
 * LogoViewer – displays logo research inspiration, queries, and optional variations.
 */

const BOARD_TINTS = [
  'from-amber-100 to-orange-100',
  'from-emerald-100 to-lime-100',
  'from-cyan-100 to-blue-100',
  'from-rose-100 to-pink-100',
  'from-violet-100 to-indigo-100',
  'from-yellow-100 to-amber-100',
  'from-teal-100 to-emerald-100',
  'from-sky-100 to-cyan-100',
];

function shortTitle(text = '', max = 52) {
  const value = String(text || '').trim();
  if (!value) return 'Inspiration';
  if (value.length <= max) return value;
  return `${value.slice(0, max - 1)}...`;
}

function querySearchUrl(query = '') {
  return `https://www.pinterest.com/search/pins/?q=${encodeURIComponent(query)}`;
}

function isValidHref(link = '') {
  return /^https?:\/\//i.test(String(link || ''));
}

function domainLabel(link = '') {
  try {
    const host = new URL(link).hostname.replace(/^www\./, '');
    if (host.includes('pinterest')) return 'Pinterest';
    if (host.includes('behance')) return 'Behance';
    if (host.includes('dribbble')) return 'Dribbble';
    return host.split('.')[0] || 'Source';
  } catch {
    return 'Source';
  }
}

export default function LogoViewer({ logoData, onRegenerate }) {
  if (!logoData) return null;

  const {
    logos,
    total_variations,
    logo_inspiration,
    search_queries,
    logo_direction,
    competitor_logo_brands,
    trend_keywords,
    logo_inspiration_notes,
  } = logoData;

  const hasResearchContent =
    (Array.isArray(search_queries) && search_queries.length > 0) ||
    (Array.isArray(logo_inspiration) && logo_inspiration.length > 0) ||
    (Array.isArray(competitor_logo_brands) && competitor_logo_brands.length > 0) ||
    (Array.isArray(trend_keywords) && trend_keywords.length > 0) ||
    (Array.isArray(logo_inspiration_notes) && logo_inspiration_notes.length > 0);

  const inspiration = Array.isArray(logo_inspiration) ? logo_inspiration : [];
  const queries = Array.isArray(search_queries) ? search_queries : [];
  const references = Array.isArray(competitor_logo_brands) ? competitor_logo_brands : [];
  const previewIdeas = inspiration.slice(0, 20);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="glass-card p-8 space-y-6">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h3 className="text-xl font-black text-white uppercase tracking-tight">Logo Direction</h3>
            <p className="text-sm text-white/40 mt-1">
              Research-driven logo ideas, competitor references, and trend queries.
            </p>
          </div>
          {Array.isArray(trend_keywords) && trend_keywords.length > 0 && (
            <div className="flex flex-wrap gap-2 justify-end">
              {trend_keywords.slice(0, 4).map((keyword, index) => (
                <span
                  key={index}
                  className="px-3 py-1 rounded-full text-[11px] font-semibold bg-cyan-500/10 border border-cyan-500/20 text-cyan-200"
                >
                  {keyword}
                </span>
              ))}
            </div>
          )}
        </div>

        {logo_direction?.summary && (
          <div className="rounded-2xl border border-blue-500/20 bg-blue-500/5 p-5 space-y-3">
            <h4 className="text-sm font-black uppercase tracking-[0.18em] text-blue-300">Recommended Direction</h4>
            <p className="text-white/80 leading-relaxed">{logo_direction.summary}</p>
            {Array.isArray(logo_direction.best_logo_types) && logo_direction.best_logo_types.length > 0 && (
              <div className="flex flex-wrap gap-2 pt-2">
                {logo_direction.best_logo_types.map((type, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 rounded-full text-[11px] font-semibold bg-white/5 border border-white/10 text-white/70"
                  >
                    {type}
                  </span>
                ))}
              </div>
            )}
            {logo_direction.why_it_fits && (
              <p className="text-sm text-white/50">{logo_direction.why_it_fits}</p>
            )}
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-cyan-400/20 bg-cyan-500/10 p-4">
            <div className="text-[10px] uppercase font-black tracking-[0.2em] text-cyan-200/70 mb-2">Inspiration Links</div>
            <div className="text-3xl font-black text-white">{previewIdeas.length}</div>
          </div>
          <div className="rounded-2xl border border-blue-400/20 bg-blue-500/10 p-4">
            <div className="text-[10px] uppercase font-black tracking-[0.2em] text-blue-200/70 mb-2">LLM Search Queries</div>
            <div className="text-3xl font-black text-white">{queries.length}</div>
          </div>
          <div className="rounded-2xl border border-emerald-400/20 bg-emerald-500/10 p-4">
            <div className="text-[10px] uppercase font-black tracking-[0.2em] text-emerald-200/70 mb-2">Reference Brands</div>
            <div className="text-3xl font-black text-white">{references.length}</div>
          </div>
        </div>

        {queries.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-[10px] font-black text-white/40 uppercase tracking-[0.2em]">Search Queries Used</h4>
            <div className="grid gap-3 md:grid-cols-2">
              {queries.map((item, index) => (
                <div key={index} className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-xs font-black uppercase tracking-[0.18em] text-cyan-200/80">
                      {item.label || `Query ${index + 1}`}
                    </span>
                    {item.query && (
                      <a
                        href={querySearchUrl(item.query)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[10px] px-2 py-1 rounded-full border border-cyan-400/30 bg-cyan-500/10 text-cyan-200 uppercase tracking-widest font-black"
                      >
                        Open
                      </a>
                    )}
                  </div>
                  <p className="mt-2 text-sm text-white/80 break-words">{item.query}</p>
                  {item.reason && <p className="mt-2 text-xs text-white/40">{item.reason}</p>}
                </div>
              ))}
            </div>
          </div>
        )}

        {Array.isArray(logo_inspiration_notes) && logo_inspiration_notes.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-[10px] font-black text-white/40 uppercase tracking-[0.2em]">Logo Inspiration Notes</h4>
            <div className="grid gap-3 md:grid-cols-2">
              {logo_inspiration_notes.map((note, index) => (
                <div
                  key={index}
                  className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-sm text-white/75 leading-relaxed"
                >
                  {note}
                </div>
              ))}
            </div>
          </div>
        )}

        {references.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-[10px] font-black text-white/40 uppercase tracking-[0.2em]">Competitor / Reference Brands</h4>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {references.map((brand, index) => {
                const href = brand.website || '#';
                const isClickable = href && href !== '#';

                const content = (
                  <>
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-200/70 mb-2">
                          Reference {index + 1}
                        </div>
                        <h4 className="font-bold text-white leading-snug">{brand.name || 'Reference Brand'}</h4>
                      </div>
                      <span className="text-white/30 group-hover:text-cyan-300 transition-colors">↗</span>
                    </div>
                    {brand.reason && <p className="text-sm text-white/50 mt-3 leading-relaxed">{brand.reason}</p>}
                    {brand.website && <div className="mt-4 text-[11px] text-cyan-300/80 break-all">{brand.website}</div>}
                  </>
                );

                return isClickable ? (
                  <a
                    key={`${brand.website || brand.name || index}`}
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group rounded-2xl border border-white/10 bg-white/[0.03] p-4 hover:bg-white/[0.06] hover:border-cyan-400/30 transition-all"
                  >
                    {content}
                  </a>
                ) : (
                  <div
                    key={`${brand.website || brand.name || index}`}
                    className="group rounded-2xl border border-white/10 bg-white/[0.03] p-4"
                  >
                    {content}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {previewIdeas.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div>
                <h3 className="text-xl font-black text-white uppercase tracking-tight">Inspiration Moodboard Links</h3>
                <p className="text-sm text-white/40 mt-1">Visual-first links styled like logo inspiration boards and mini brand sheets.</p>
              </div>
              <span className="text-xs font-bold text-cyan-300 bg-cyan-500/10 border border-cyan-500/20 rounded-full px-3 py-1 uppercase tracking-widest">
                {previewIdeas.length} ideas
              </span>
            </div>

            <div className="grid gap-4 grid-cols-2 md:grid-cols-3 xl:grid-cols-4">
              {previewIdeas.map((idea, index) => (
                <a
                  key={`${idea.link}-${index}`}
                  href={idea.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`group rounded-2xl border border-white/10 bg-gradient-to-br ${BOARD_TINTS[index % BOARD_TINTS.length]} p-4 hover:scale-[1.02] transition-all min-h-[185px] flex flex-col justify-between`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-700/80 mb-2">
                        {idea.query_label || `Idea ${index + 1}`}
                      </div>
                      <h4 className="font-black text-slate-900 text-lg leading-snug break-words uppercase tracking-tight">
                        {shortTitle(idea.brand_name || idea.title, 32)}
                      </h4>
                    </div>
                    <span className="text-slate-700/60 group-hover:text-slate-900 transition-colors text-lg">↗</span>
                  </div>
                  <div className="mt-4">
                    {idea.snippet && (
                      <p className="text-xs text-slate-700/80 leading-relaxed line-clamp-3">{shortTitle(idea.snippet, 110)}</p>
                    )}
                    <div className="mt-3 flex items-center justify-between gap-2 text-[11px]">
                      <span className="px-2 py-1 rounded-full bg-white/60 border border-slate-300/60 text-slate-700 font-bold uppercase tracking-widest">
                        {idea.platform || domainLabel(idea.link)}
                      </span>
                      <span className="text-slate-700/70 font-semibold">#{index + 1}</span>
                    </div>
                  </div>
                </a>
              ))}
            </div>
          </div>
        )}

        {logos && logos.length > 0 && (
          <div className="glass-card p-8 space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-black text-white uppercase tracking-tight">Optional Generated Variations</h3>
              <span className="text-sm font-bold text-white/50">
                {total_variations ? `1 of ${total_variations}` : 'Preview'}
              </span>
            </div>
            <div className="text-sm text-white/50 bg-white/5 rounded-2xl p-4 border border-white/10">
              Generated variations are kept only as optional fallback. The primary output now focuses on research-driven logo ideas and competitor references.
            </div>
            {onRegenerate && (
              <div className="flex gap-3 pt-2 border-t border-white/10">
                <button
                  onClick={() => onRegenerate('visual_identity_agent', 'refine the visual direction, logo direction, and return fresher inspiration links mostly from Pinterest brand boards')}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 text-blue-300 hover:text-blue-200 font-semibold transition-all text-sm"
                >
                  <span>🔄</span>
                  <span>Refine Inspiration</span>
                </button>
                <button
                  onClick={() => onRegenerate('visual_identity_agent', 'generate new search queries and provide 15 to 20 logo/design reference links in the same visual style')}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 border border-cyan-500/30 text-cyan-300 hover:text-cyan-200 font-semibold transition-all text-sm"
                >
                  <span>✨</span>
                  <span>Refresh All Ideas</span>
                </button>
              </div>
            )}
          </div>
        )}

        {!hasResearchContent && !(logos && logos.length > 0) && (
          <div className="glass-card p-8 text-center text-white/50">
            No logo inspiration available yet.
          </div>
        )}
      </div>
    </div>
  );
}
