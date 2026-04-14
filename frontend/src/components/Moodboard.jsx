import { useState } from 'react';

// ── Category config ───────────────────────────────────────────────────────────
const CATEGORIES = [
  {
    key: 'Case Studies',
    icon: '📐',
    color: 'text-blue-300',
    border: 'border-blue-500/25',
    bg: 'bg-blue-500/8',
    badge: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    desc: 'Full brand identity projects with process & rationale',
  },
  {
    key: 'Logo Gallery',
    icon: '🏛',
    color: 'text-violet-300',
    border: 'border-violet-500/25',
    bg: 'bg-violet-500/8',
    badge: 'bg-violet-500/20 text-violet-300 border-violet-500/30',
    desc: 'Curated logo libraries & annual trend reports',
  },
  {
    key: 'Design Shots',
    icon: '🎯',
    color: 'text-pink-300',
    border: 'border-pink-500/25',
    bg: 'bg-pink-500/8',
    badge: 'bg-pink-500/20 text-pink-300 border-pink-500/30',
    desc: 'Logo explorations & design process snapshots',
  },
  {
    key: 'Typography',
    icon: 'Aa',
    color: 'text-cyan-300',
    border: 'border-cyan-500/25',
    bg: 'bg-cyan-500/8',
    badge: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
    desc: 'Real-world typeface usage in brand identities',
  },
  {
    key: 'Moodboard',
    icon: '🖼',
    color: 'text-amber-300',
    border: 'border-amber-500/25',
    bg: 'bg-amber-500/8',
    badge: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
    desc: 'Pinterest boards & visual direction references',
  },
  {
    key: 'Reference',
    icon: '🔗',
    color: 'text-white/50',
    border: 'border-white/15',
    bg: 'bg-white/5',
    badge: 'bg-white/10 text-white/50 border-white/15',
    desc: 'Additional design references',
  },
];

const CAT_MAP = Object.fromEntries(CATEGORIES.map((c) => [c.key, c]));

function getCat(item) {
  return CAT_MAP[item.category] || CAT_MAP['Reference'];
}

function shortText(text = '', max = 90) {
  const s = String(text || '').trim();
  return s.length > max ? s.slice(0, max - 1) + '…' : s;
}

// ── Inspiration Card ──────────────────────────────────────────────────────────
function InspirationCard({ item }) {
  const cat = getCat(item);
  return (
    <a
      href={item.link}
      target="_blank"
      rel="noopener noreferrer"
      className="group flex flex-col rounded-2xl border overflow-hidden hover:scale-[1.02] transition-all duration-200"
      style={{ borderColor: 'rgba(255,255,255,0.08)', background: 'rgba(255,255,255,0.025)' }}
    >
      {/* Top accent bar */}
      <div className={`h-1 w-full ${cat.bg.replace('/8', '/40')}`} />

      <div className="p-4 flex flex-col gap-2 flex-1">
        {/* Platform + arrow */}
        <div className="flex items-center justify-between gap-2">
          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${cat.badge}`}>
            {item.platform || item.category}
          </span>
          <span className="text-white/20 group-hover:text-white/60 transition-colors text-xs">↗</span>
        </div>

        {/* Title */}
        <div className="text-xs font-bold text-white/80 leading-snug line-clamp-2">
          {shortText(item.brand_name || item.title, 55)}
        </div>

        {/* Snippet */}
        {item.snippet && (
          <p className="text-[11px] text-white/40 leading-relaxed line-clamp-3 flex-1">
            {shortText(item.snippet, 110)}
          </p>
        )}

        {/* Query label */}
        {item.query_label && (
          <div className={`text-[9px] font-black uppercase tracking-[0.15em] mt-auto ${cat.color} opacity-60`}>
            {item.query_label}
          </div>
        )}
      </div>
    </a>
  );
}

// ── Category Section ──────────────────────────────────────────────────────────
function CategorySection({ catKey, items }) {
  const [expanded, setExpanded] = useState(true);
  const cat = CAT_MAP[catKey] || CAT_MAP['Reference'];

  return (
    <div className={`rounded-2xl border overflow-hidden ${cat.border}`}>
      {/* Header */}
      <button
        onClick={() => setExpanded((e) => !e)}
        className="w-full flex items-center gap-3 px-5 py-4 hover:bg-white/[0.03] transition-colors text-left"
        style={{ background: 'rgba(255,255,255,0.02)' }}
      >
        <span className="text-lg w-7 text-center flex-shrink-0">{cat.icon}</span>
        <div className="flex-1 min-w-0">
          <div className={`text-sm font-black ${cat.color}`}>{catKey}</div>
          <div className="text-[11px] text-white/30 mt-0.5">{cat.desc}</div>
        </div>
        <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full border ${cat.badge}`}>
          {items.length}
        </span>
        <span className="text-white/30 text-xs ml-1">{expanded ? '▲' : '▼'}</span>
      </button>

      {/* Cards */}
      {expanded && (
        <div className="px-4 pb-4 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 mt-1">
          {items.map((item, i) => (
            <InspirationCard key={`${item.link}-${i}`} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main Export ───────────────────────────────────────────────────────────────
export default function Moodboard({ data }) {
  const [activeFilter, setActiveFilter] = useState('All');

  if (!data) return null;

  const inspiration = Array.isArray(data.logo_inspiration) ? data.logo_inspiration : [];
  if (inspiration.length === 0) return null;

  // Group by category
  const grouped = {};
  for (const item of inspiration) {
    const cat = item.category || 'Reference';
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push(item);
  }

  // Build filter tabs — only show categories that have items
  const presentCats = CATEGORIES.filter((c) => grouped[c.key]?.length > 0);
  const filters = ['All', ...presentCats.map((c) => c.key)];

  // What to show
  const visibleGroups = activeFilter === 'All'
    ? presentCats.map((c) => c.key)
    : [activeFilter];

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-2xl font-black text-white uppercase tracking-tight">
            Designer Inspiration Pack
          </h2>
          <p className="text-white/40 text-sm mt-1">
            {inspiration.length} references across {presentCats.length} source types — curated for your brand
          </p>
        </div>
      </div>

      {/* Source guide */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
        {presentCats.map((cat) => (
          <div
            key={cat.key}
            className={`rounded-xl px-3 py-2 border ${cat.border} flex items-center gap-2`}
            style={{ background: 'rgba(255,255,255,0.02)' }}
          >
            <span className="text-base">{cat.icon}</span>
            <div className="min-w-0">
              <div className={`text-[11px] font-black ${cat.color}`}>{cat.key}</div>
              <div className="text-[10px] text-white/30 truncate">{grouped[cat.key]?.length} links</div>
            </div>
          </div>
        ))}
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 flex-wrap">
        {filters.map((f) => {
          const cat = CAT_MAP[f];
          const isActive = activeFilter === f;
          return (
            <button
              key={f}
              onClick={() => setActiveFilter(f)}
              className={`px-3 py-1.5 rounded-full text-[11px] font-bold border transition-all ${
                isActive
                  ? (cat?.badge || 'bg-white/20 text-white border-white/30')
                  : 'bg-white/5 border-white/10 text-white/50 hover:text-white/70'
              }`}
            >
              {cat?.icon ? `${cat.icon} ` : ''}{f}
              {f !== 'All' && grouped[f] && (
                <span className="ml-1.5 opacity-60">{grouped[f].length}</span>
              )}
            </button>
          );
        })}
      </div>

      {/* Sections */}
      <div className="space-y-4">
        {visibleGroups.map((catKey) =>
          grouped[catKey]?.length > 0 ? (
            <CategorySection key={catKey} catKey={catKey} items={grouped[catKey]} />
          ) : null
        )}
      </div>

      {/* How to use callout */}
      <div className="rounded-2xl border border-white/8 bg-white/[0.02] p-5 space-y-3">
        <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30">How to use this pack</div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-white/45 leading-relaxed">
          <div className="flex gap-2">
            <span className="text-blue-300 flex-shrink-0">📐</span>
            <span><strong className="text-blue-300">Case Studies</strong> — Study the full identity system: logo + color + type + usage rules. Great for understanding how brands handle your category.</span>
          </div>
          <div className="flex gap-2">
            <span className="text-violet-300 flex-shrink-0">🏛</span>
            <span><strong className="text-violet-300">Logo Gallery</strong> — Browse logos by industry. Use Logolounge trend reports to see what visual styles are rising or fading this year.</span>
          </div>
          <div className="flex gap-2">
            <span className="text-pink-300 flex-shrink-0">🎯</span>
            <span><strong className="text-pink-300">Design Shots</strong> — See exploratory logo sketches and WIP designs. Great for understanding the design process behind polished logos.</span>
          </div>
          <div className="flex gap-2">
            <span className="text-cyan-300 flex-shrink-0">Aa</span>
            <span><strong className="text-cyan-300">Typography</strong> — See exactly how the suggested fonts are used in real brand identities. Validates your type choices with live examples.</span>
          </div>
        </div>
      </div>
    </div>
  );
}
