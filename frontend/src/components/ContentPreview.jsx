import { useState } from 'react';

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(text).catch(() => {}); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
      className="text-[10px] px-2 py-1 rounded-full border border-white/10 bg-white/5 hover:bg-white/10 text-white/40 hover:text-white/70 transition-all flex-shrink-0"
    >
      {copied ? '✓ Copied' : 'Copy'}
    </button>
  );
}

// ── Block component: label + body + copy ─────────────────────────────────────
function Block({ label, children, text, accent = 'cyan' }) {
  const colours = {
    cyan:    'text-cyan-300/70',
    indigo:  'text-indigo-300/70',
    emerald: 'text-emerald-300/70',
    amber:   'text-amber-300/70',
    rose:    'text-rose-300/70',
    violet:  'text-violet-300/70',
  };
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 space-y-2">
      <div className="flex items-start justify-between gap-3">
        <div className={`text-[10px] font-black uppercase tracking-[0.2em] ${colours[accent] || colours.cyan}`}>{label}</div>
        {text && <CopyButton text={text} />}
      </div>
      {children}
    </div>
  );
}

// ── Social platform cards ─────────────────────────────────────────────────────
function TwitterCard({ bio }) {
  return (
    <div className="rounded-2xl bg-black border border-white/10 p-5 space-y-3">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center font-black text-white text-sm">B</div>
        <div>
          <div className="font-bold text-white text-sm">Brand Name</div>
          <div className="text-white/40 text-xs">@brand</div>
        </div>
        <div className="ml-auto">
          <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="currentColor">
            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.743l7.73-8.835L1.254 2.25H8.08l4.264 5.638 5.9-5.638Zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
          </svg>
        </div>
      </div>
      <div className="flex items-start justify-between gap-3">
        <p className="text-white/80 text-sm leading-relaxed">{bio}</p>
        <CopyButton text={bio} />
      </div>
    </div>
  );
}

function InstagramCard({ bio }) {
  return (
    <div className="rounded-2xl bg-gradient-to-br from-purple-900/80 to-pink-900/80 border border-white/10 p-5 space-y-3">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-pink-500 to-orange-400 flex items-center justify-center font-black text-white text-sm">B</div>
        <div>
          <div className="font-bold text-white text-sm">brand</div>
          <div className="text-white/40 text-xs">Instagram</div>
        </div>
      </div>
      <div className="flex items-start justify-between gap-3">
        <p className="text-white/80 text-sm leading-relaxed whitespace-pre-line">{bio}</p>
        <CopyButton text={bio} />
      </div>
    </div>
  );
}

function LinkedInCard({ bio }) {
  return (
    <div className="rounded-2xl bg-[#0a66c2]/10 border border-[#0a66c2]/30 p-5 space-y-3">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-md bg-[#0a66c2] flex items-center justify-center font-black text-white text-sm">in</div>
        <div>
          <div className="font-bold text-white text-sm">Brand Name</div>
          <div className="text-white/40 text-xs">Company · LinkedIn</div>
        </div>
      </div>
      <div className="flex items-start justify-between gap-3">
        <p className="text-white/80 text-sm leading-relaxed">{bio}</p>
        <CopyButton text={bio} />
      </div>
    </div>
  );
}

// ── Tab content sections ──────────────────────────────────────────────────────

function FoundationsTab({ data }) {
  return (
    <div className="space-y-4">
      {data.mission_statement && (
        <Block label="Mission Statement" text={data.mission_statement} accent="emerald">
          <p className="text-white/90 text-base leading-relaxed font-medium">{data.mission_statement}</p>
        </Block>
      )}
      {data.vision_statement && (
        <Block label="Vision Statement" text={data.vision_statement} accent="indigo">
          <p className="text-white/90 text-base leading-relaxed font-medium">{data.vision_statement}</p>
        </Block>
      )}
      {data.brand_stands_for && (
        <Block label="What We Stand For" text={data.brand_stands_for} accent="violet">
          <p className="text-white/80 leading-relaxed">{data.brand_stands_for}</p>
        </Block>
      )}
      {data.mission_statement_extended && (
        <Block label="Extended Mission" text={data.mission_statement_extended} accent="cyan">
          <p className="text-white/70 text-sm leading-relaxed">{data.mission_statement_extended}</p>
        </Block>
      )}
    </div>
  );
}

function VoiceTab({ data }) {
  const tov = data.tone_of_voice || {};
  const chars    = Array.isArray(tov.character)   ? tov.character   : [];
  const writeLike = Array.isArray(tov.write_like) ? tov.write_like  : [];
  const avoid    = Array.isArray(tov.avoid)        ? tov.avoid      : [];

  return (
    <div className="space-y-4">
      {/* Character chips */}
      {chars.length > 0 && (
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 space-y-3">
          <div className="text-[10px] font-black uppercase tracking-[0.2em] text-amber-300/70">Voice Character</div>
          <div className="flex flex-wrap gap-2">
            {chars.map((c, i) => (
              <span key={i} className="px-3 py-1.5 rounded-full border border-amber-400/30 bg-amber-400/8 text-amber-200 text-xs font-bold">
                {c}
              </span>
            ))}
          </div>
          {tov.description && <p className="text-white/70 text-sm leading-relaxed">{tov.description}</p>}
        </div>
      )}

      {/* Hero copy example */}
      {tov.example_hero_copy && (
        <Block label="Sample Brand Voice (Homepage Hero)" text={tov.example_hero_copy} accent="cyan">
          <p className="text-white/85 leading-relaxed italic border-l-2 border-cyan-400/30 pl-4">
            "{tov.example_hero_copy}"
          </p>
        </Block>
      )}

      {/* Write like / Avoid */}
      <div className="grid md:grid-cols-2 gap-4">
        {writeLike.length > 0 && (
          <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-5 space-y-3">
            <div className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-300/70">Write Like This ✓</div>
            <ul className="space-y-2">
              {writeLike.map((ex, i) => (
                <li key={i} className="flex gap-2 text-sm text-white/75 leading-relaxed">
                  <span className="text-emerald-400 flex-shrink-0 mt-0.5">→</span>
                  <span>"{ex}"</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        {avoid.length > 0 && (
          <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-5 space-y-3">
            <div className="text-[10px] font-black uppercase tracking-[0.2em] text-red-300/70">Avoid ✕</div>
            <ul className="space-y-2">
              {avoid.map((ex, i) => (
                <li key={i} className="flex gap-2 text-sm text-white/65 leading-relaxed">
                  <span className="text-red-400 flex-shrink-0 mt-0.5">✕</span>
                  <span>{ex}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

function EmailTab({ data }) {
  const tagline = data.email_tagline || data.email_signature_tagline || '';

  return (
    <div className="space-y-4">
      {tagline ? (
        <Block label="Email Sign-off Tagline" text={tagline} accent="violet">
          <p className="text-white/90 text-xl font-medium italic leading-relaxed">"{tagline}"</p>
          <p className="text-[11px] text-white/35 mt-2">
            Use this as the closing line in all staff email signatures — consistent across the team.
          </p>
        </Block>
      ) : (
        <p className="text-white/30 text-sm">No email tagline generated yet.</p>
      )}
    </div>
  );
}

function PitchTab({ data }) {
  return (
    <div className="space-y-4">
      {data.elevator_pitch && (
        <Block label="Elevator Pitch" text={data.elevator_pitch} accent="cyan">
          <p className="text-white/90 text-lg leading-relaxed font-medium">{data.elevator_pitch}</p>
        </Block>
      )}
      {data.about_section && (
        <Block label="About Section" text={data.about_section} accent="indigo">
          <p className="text-white/80 leading-relaxed">{data.about_section}</p>
        </Block>
      )}
    </div>
  );
}

function SocialTab({ data }) {
  const bios = data.social_media_bios || {};
  const tags = Array.isArray(data.brand_hashtags) ? data.brand_hashtags : [];

  return (
    <div className="space-y-4">
      {bios.twitter   && <TwitterCard   bio={bios.twitter}   />}
      {bios.instagram && <InstagramCard bio={bios.instagram} />}
      {bios.linkedin  && <LinkedInCard  bio={bios.linkedin}  />}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-1">
          {tags.map((tag, i) => (
            <span key={i} className="px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-300 text-sm font-semibold">
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function PillarsTab({ data }) {
  const pillars = Array.isArray(data.key_messaging_pillars) ? data.key_messaging_pillars : [];
  return (
    <div className="grid md:grid-cols-2 gap-4">
      {pillars.map((p, i) => (
        <div key={i} className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 space-y-2">
          <div className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-300/70">Pillar {i + 1}</div>
          <div className="font-black text-white text-lg">{p.pillar}</div>
          <div className="text-blue-300 font-semibold text-sm">{p.headline}</div>
          <p className="text-white/60 text-sm leading-relaxed">{p.description}</p>
        </div>
      ))}
    </div>
  );
}

function CTAsTab({ data }) {
  const ctas = Array.isArray(data.call_to_action_phrases) ? data.call_to_action_phrases : [];
  return (
    <div className="grid md:grid-cols-2 gap-3">
      {ctas.map((cta, i) => (
        <div key={i} className="rounded-xl border border-white/10 bg-white/[0.03] p-4 flex items-center justify-between gap-4">
          <div>
            <div className="text-[10px] text-white/30 uppercase tracking-widest mb-1">CTA {i + 1}</div>
            <div className="text-white/90 font-semibold">{cta}</div>
          </div>
          <CopyButton text={cta} />
        </div>
      ))}
    </div>
  );
}

// ── Main Export ───────────────────────────────────────────────────────────────
export default function ContentPreview({ data, onRegenerate }) {
  const [tab, setTab] = useState('foundations');

  if (!data) return null;

  const pillars = Array.isArray(data.key_messaging_pillars) ? data.key_messaging_pillars : [];
  const ctas    = Array.isArray(data.call_to_action_phrases) ? data.call_to_action_phrases : [];

  const tabs = [
    { key: 'foundations', label: 'Mission & Vision' },
    { key: 'voice',       label: 'Tone of Voice' },
    { key: 'email',       label: 'Email Signature' },
    { key: 'pitch',       label: 'About & Pitch' },
    { key: 'social',      label: 'Social Bios' },
    { key: 'pillars',     label: `Pillars (${pillars.length})` },
    { key: 'cta',         label: `CTAs (${ctas.length})` },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-2xl font-black text-white uppercase tracking-tight">Brand Content</h2>
          <p className="text-white/40 text-sm mt-1">Mission, voice, copy — ready for every channel</p>
        </div>
        {onRegenerate && (
          <button
            onClick={() => onRegenerate('content_agent', 'refresh all content with a more compelling voice')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 text-white/70 hover:text-white transition-all text-sm font-semibold"
          >
            🔄 Regenerate
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 flex-wrap">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 rounded-full text-[11px] font-black uppercase tracking-[0.12em] border transition-all ${
              tab === t.key
                ? 'bg-blue-500/20 border-blue-400/40 text-blue-200'
                : 'bg-white/5 border-white/10 text-white/50 hover:text-white/70'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'foundations' && <FoundationsTab data={data} />}
      {tab === 'voice'       && <VoiceTab       data={data} />}
      {tab === 'email'       && <EmailTab        data={data} />}
      {tab === 'pitch'       && <PitchTab        data={data} />}
      {tab === 'social'      && <SocialTab       data={data} />}
      {tab === 'pillars'     && <PillarsTab      data={data} />}
      {tab === 'cta'         && <CTAsTab         data={data} />}
    </div>
  );
}
