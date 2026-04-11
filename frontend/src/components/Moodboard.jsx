import { useState } from 'react';

const TINTS = [
  'from-amber-50 to-orange-100',
  'from-emerald-50 to-teal-100',
  'from-cyan-50 to-blue-100',
  'from-rose-50 to-pink-100',
  'from-violet-50 to-indigo-100',
  'from-yellow-50 to-amber-100',
  'from-sky-50 to-cyan-100',
  'from-lime-50 to-emerald-100',
];

const PLATFORM_COLORS = {
  Pinterest: 'bg-red-500/20 text-red-300 border-red-500/30',
  Dribbble:  'bg-pink-500/20 text-pink-300 border-pink-500/30',
  Behance:   'bg-blue-500/20 text-blue-300 border-blue-500/30',
};

function getPlatformClass(platform = '') {
  return PLATFORM_COLORS[platform] || 'bg-white/10 text-white/60 border-white/15';
}

function shortText(text = '', max = 55) {
  const s = String(text || '').trim();
  return s.length > max ? s.slice(0, max - 1) + '…' : s;
}

function domainLabel(link = '') {
  try {
    const host = new URL(link).hostname.replace(/^www\./, '');
    if (host.includes('pinterest')) return 'Pinterest';
    if (host.includes('dribbble'))  return 'Dribbble';
    if (host.includes('behance'))   return 'Behance';
    return host.split('.')[0] || 'Source';
  } catch {
    return 'Source';
  }
}

export default function Moodboard({ data }) {
  const [platform, setPlatform] = useState('All');

  if (!data) return null;

  const inspiration = Array.isArray(data.logo_inspiration) ? data.logo_inspiration : [];
  const queries     = Array.isArray(data.search_queries)   ? data.search_queries   : [];

  if (inspiration.length === 0 && queries.length === 0) return null;

  const platforms = ['All', ...new Set(inspiration.map((i) => i.platform || domainLabel(i.link)).filter(Boolean))];
  const filtered  = platform === 'All'
    ? inspiration
    : inspiration.filter((i) => (i.platform || domainLabel(i.link)) === platform);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-2xl font-black text-white uppercase tracking-tight">Inspiration Moodboard</h2>
          <p className="text-white/40 text-sm mt-1">{inspiration.length} curated links · Pinterest-prioritised</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          {platforms.map((p) => (
            <button
              key={p}
              onClick={() => setPlatform(p)}
              className={`px-3 py-1.5 rounded-full text-[11px] font-bold border transition-all ${
                platform === p
                  ? (PLATFORM_COLORS[p] || 'bg-white/20 text-white border-white/30')
                  : 'bg-white/5 border-white/10 text-white/50 hover:text-white/70'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Masonry-style grid */}
      <div className="columns-2 md:columns-3 xl:columns-4 gap-4 space-y-4">
        {filtered.map((item, i) => {
          const plat = item.platform || domainLabel(item.link);
          return (
            <a
              key={`${item.link}-${i}`}
              href={item.link}
              target="_blank"
              rel="noopener noreferrer"
              className={`group block rounded-2xl border border-white/10 bg-gradient-to-br ${TINTS[i % TINTS.length]} p-4 mb-4 break-inside-avoid hover:scale-[1.02] transition-all`}
            >
              <div className="flex items-start justify-between gap-2 mb-3">
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${getPlatformClass(plat)}`}>
                  {plat}
                </span>
                <span className="text-slate-600/50 group-hover:text-slate-800 transition-colors text-sm">↗</span>
              </div>
              <div className="font-black text-slate-900 text-sm leading-snug uppercase tracking-tight">
                {shortText(item.brand_name || item.title, 45)}
              </div>
              {item.snippet && (
                <p className="mt-2 text-xs text-slate-700/70 leading-relaxed line-clamp-3">
                  {shortText(item.snippet, 110)}
                </p>
              )}
              {item.query_label && (
                <div className="mt-3 text-[10px] font-semibold text-slate-600/60 uppercase tracking-wider">
                  {item.query_label}
                </div>
              )}
            </a>
          );
        })}
      </div>

      {/* Search queries used */}
      {queries.length > 0 && (
        <details className="rounded-2xl border border-white/10 bg-white/[0.02]">
          <summary className="px-5 py-4 cursor-pointer text-[11px] font-black uppercase tracking-[0.2em] text-white/40 hover:text-white/60 transition-colors">
            {queries.length} Search Queries Used
          </summary>
          <div className="px-5 pb-5 grid md:grid-cols-2 gap-3">
            {queries.map((q, i) => (
              <a
                key={i}
                href={`https://www.pinterest.com/search/pins/?q=${encodeURIComponent(q.query || '')}`}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-xl border border-white/10 bg-white/[0.03] p-4 hover:bg-white/[0.06] transition-all group"
              >
                <div className="flex items-center justify-between gap-3 mb-1">
                  <span className="text-[10px] font-black uppercase tracking-widest text-cyan-300/70">
                    {q.label || `Query ${i + 1}`}
                  </span>
                  <span className="text-white/20 group-hover:text-cyan-300 transition-colors text-xs">↗</span>
                </div>
                <p className="text-xs text-white/60 break-words">{q.query}</p>
              </a>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
