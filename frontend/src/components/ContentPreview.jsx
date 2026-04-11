import { useState } from 'react';

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(text).catch(() => {}); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
      className="text-[10px] px-2 py-1 rounded-full border border-white/10 bg-white/5 hover:bg-white/10 text-white/40 hover:text-white/70 transition-all flex-shrink-0"
    >
      {copied ? '✓' : 'Copy'}
    </button>
  );
}

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
      <div className="text-[11px] text-white/30">Twitter / X · Bio preview</div>
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
        <div className="ml-auto">
          <svg className="w-5 h-5 text-white/60" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4z"/>
          </svg>
        </div>
      </div>
      <div className="flex items-start justify-between gap-3">
        <p className="text-white/80 text-sm leading-relaxed whitespace-pre-line">{bio}</p>
        <CopyButton text={bio} />
      </div>
      <div className="text-[11px] text-white/30">Instagram · Bio preview</div>
    </div>
  );
}

function LinkedInCard({ bio }) {
  return (
    <div className="rounded-2xl bg-[#0a66c2]/10 border border-[#0a66c2]/30 p-5 space-y-3">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-md bg-[#0a66c2] flex items-center justify-center font-black text-white text-sm">B</div>
        <div>
          <div className="font-bold text-white text-sm">Brand Name</div>
          <div className="text-white/40 text-xs">Company · LinkedIn</div>
        </div>
      </div>
      <div className="flex items-start justify-between gap-3">
        <p className="text-white/80 text-sm leading-relaxed">{bio}</p>
        <CopyButton text={bio} />
      </div>
      <div className="text-[11px] text-white/30">LinkedIn · Company bio preview</div>
    </div>
  );
}

export default function ContentPreview({ data, onRegenerate }) {
  const [tab, setTab] = useState('social');

  if (!data) return null;

  const bios    = data.social_media_bios || {};
  const pillars = Array.isArray(data.key_messaging_pillars) ? data.key_messaging_pillars : [];
  const ctas    = Array.isArray(data.call_to_action_phrases) ? data.call_to_action_phrases : [];
  const tags    = Array.isArray(data.brand_hashtags) ? data.brand_hashtags : [];

  const tabs = [
    { key: 'social',    label: 'Social Bios' },
    { key: 'pitch',     label: 'Elevator Pitch' },
    { key: 'pillars',   label: `Pillars (${pillars.length})` },
    { key: 'cta',       label: 'CTAs' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-2xl font-black text-white uppercase tracking-tight">Brand Content</h2>
          <p className="text-white/40 text-sm mt-1">Copy ready to publish across all channels</p>
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
            className={`px-4 py-2 rounded-full text-[11px] font-black uppercase tracking-[0.15em] border transition-all ${
              tab === t.key
                ? 'bg-blue-500/20 border-blue-400/40 text-blue-200'
                : 'bg-white/5 border-white/10 text-white/50 hover:text-white/70'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Social Bios */}
      {tab === 'social' && (
        <div className="space-y-4">
          {bios.twitter  && <TwitterCard   bio={bios.twitter}  />}
          {bios.instagram && <InstagramCard bio={bios.instagram} />}
          {bios.linkedin  && <LinkedInCard  bio={bios.linkedin}  />}
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-2 pt-2">
              {tags.map((tag, i) => (
                <span key={i} className="px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-300 text-sm font-semibold">
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Elevator Pitch */}
      {tab === 'pitch' && (
        <div className="space-y-4">
          {data.elevator_pitch && (
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
              <div className="flex items-start justify-between gap-3 mb-3">
                <div className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-300/70">Elevator Pitch</div>
                <CopyButton text={data.elevator_pitch} />
              </div>
              <p className="text-white/90 text-lg leading-relaxed font-medium">{data.elevator_pitch}</p>
            </div>
          )}
          {data.about_section && (
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
              <div className="flex items-start justify-between gap-3 mb-3">
                <div className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-300/70">About Section</div>
                <CopyButton text={data.about_section} />
              </div>
              <p className="text-white/80 leading-relaxed">{data.about_section}</p>
            </div>
          )}
          {data.email_signature_tagline && (
            <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4 flex items-center justify-between gap-4">
              <div>
                <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30 mb-1">Email Signature</div>
                <p className="text-white/70 italic text-sm">"{data.email_signature_tagline}"</p>
              </div>
              <CopyButton text={data.email_signature_tagline} />
            </div>
          )}
        </div>
      )}

      {/* Pillars */}
      {tab === 'pillars' && (
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
      )}

      {/* CTAs */}
      {tab === 'cta' && (
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
      )}
    </div>
  );
}
