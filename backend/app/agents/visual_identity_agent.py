"""
Agent 6 – Visual Identity Intelligence Agent (v5)

Pipeline:
  1. Gemini (+ Google Search) — researches competitors, generates brand-tailored
     10-concept logo design brief using the industry-standard template.
  2. Python deterministic SVG renderer — builds pixel-perfect SVG for each archetype
     using brand colours from the brief. No LLM SVG generation — always correct output.
  3. Inspiration links collected in parallel.

Output data keys:
  design_concepts     – list of 10 dicts, each with "svg" field (self-contained SVG string)
  logo_design_brief   – full text brief from Gemini
  competitor_visual_notes
  primary_color / accent_color / neutral_dark / font / style_descriptors / symbol_concepts
  logo_inspiration    – curated designer reference links
"""
import json
import math
import re
from urllib.parse import quote_plus, urlparse

from app.schemas.brand_schema import AgentResult
from app.utils.gemini_search import call_gemini_with_search
from app.utils.llm import call_llm, call_openai
from app.utils.search import web_search


# ── Deterministic SVG symbol builders (one per archetype) ─────────────────────
# These always produce pixel-perfect, professional SVGs — no LLM involved.
# Canvas: 400×400. Symbol area: x 60-340, y 30-270. Wordmark below y=283.

def _xe(s: str) -> str:
    """XML-escape text for safe embedding in SVG."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _sym_monogram(P: str, A: str, abbr: str) -> str:
    """Two interlocked L-bracket forms creating a unified square-frame mark."""
    L = _xe(abbr[0]) if abbr else "M"
    return (
        # Primary: top + left arms
        f'<rect x="118" y="58" width="20" height="192" rx="4" fill="{P}"/>'
        f'<rect x="118" y="58" width="118" height="20" rx="4" fill="{P}"/>'
        # Accent: bottom + right arms
        f'<rect x="262" y="58" width="20" height="192" rx="4" fill="{A}"/>'
        f'<rect x="164" y="230" width="118" height="20" rx="4" fill="{A}"/>'
        # Subtle centre crossbar (primary)
        f'<rect x="118" y="148" width="164" height="12" rx="3" fill="{P}" opacity="0.18"/>'
        # Ghost initial watermark
        f'<text x="200" y="200" text-anchor="middle" dominant-baseline="middle"'
        f' font-family="Arial,Helvetica,sans-serif" font-size="80" font-weight="900"'
        f' fill="{P}" opacity="0.05">{L}</text>'
    )


def _sym_orbit(P: str, A: str) -> str:
    """Central hub circle with orbit ring and three satellite nodes."""
    cx, cy, ro = 200, 152, 90
    # satellites at −90°(top), 210°(lower-left), 330°(lower-right)
    s = [(cx + ro * math.cos(math.radians(a)), cy + ro * math.sin(math.radians(a)))
         for a in (-90, 210, 330)]
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{ro}" stroke="{P}" stroke-width="3" fill="none"/>'
        f'<circle cx="{s[0][0]:.1f}" cy="{s[0][1]:.1f}" r="12" fill="{P}"/>'
        f'<circle cx="{s[1][0]:.1f}" cy="{s[1][1]:.1f}" r="12" fill="{P}"/>'
        f'<circle cx="{s[2][0]:.1f}" cy="{s[2][1]:.1f}" r="14" fill="{A}"/>'
        f'<circle cx="{cx}" cy="{cy}" r="40" fill="{P}"/>'
    )


def _sym_growth(P: str, A: str) -> str:
    """Five ascending bars — tallest in accent, rounded tops."""
    base = 262
    specs = [(108, 78, P), (148, 108, P), (188, 140, P), (228, 168, P), (268, 200, A)]
    return "".join(
        f'<rect x="{x}" y="{base - h}" width="28" height="{h}" rx="5" fill="{c}"/>'
        for x, h, c in specs
    )


def _sym_bridge(P: str, A: str) -> str:
    """Arch with two pylons, horizontal base, accent spring-point dots."""
    return (
        f'<path d="M 80,222 Q 200,60 320,222" stroke="{P}" stroke-width="9"'
        f' fill="none" stroke-linecap="round"/>'
        f'<rect x="71" y="222" width="18" height="40" rx="4" fill="{P}"/>'
        f'<rect x="311" y="222" width="18" height="40" rx="4" fill="{P}"/>'
        f'<rect x="62" y="258" width="276" height="12" rx="4" fill="{P}"/>'
        f'<circle cx="80" cy="222" r="11" fill="{A}"/>'
        f'<circle cx="320" cy="222" r="11" fill="{A}"/>'
    )


def _sym_triform(P: str, A: str) -> str:
    """Three overlapping circles in equilateral triangle — stroke + subtle fill."""
    return (
        f'<circle cx="200" cy="88"  r="74" stroke="{P}" stroke-width="5"'
        f' fill="{P}" fill-opacity="0.07"/>'
        f'<circle cx="148" cy="190" r="74" stroke="{A}" stroke-width="5"'
        f' fill="{A}" fill-opacity="0.07"/>'
        f'<circle cx="252" cy="190" r="74" stroke="{P}" stroke-width="3"'
        f' fill="{P}" fill-opacity="0.04" opacity="0.55"/>'
    )


def _sym_network(P: str, A: str) -> str:
    """Hub-and-spoke network: central accent node + six outer primary nodes."""
    cx, cy, ro = 200, 152, 88
    outer = [(cx + ro * math.cos(math.radians(a)), cy + ro * math.sin(math.radians(a)))
             for a in range(0, 360, 60)]
    spokes = "".join(
        f'<line x1="{cx}" y1="{cy}" x2="{ox:.1f}" y2="{oy:.1f}"'
        f' stroke="{P}" stroke-width="2" opacity="0.35"/>'
        for ox, oy in outer
    )
    # Adjacent cross-links (every other pair)
    links = "".join(
        f'<line x1="{outer[i][0]:.1f}" y1="{outer[i][1]:.1f}"'
        f' x2="{outer[(i+2)%6][0]:.1f}" y2="{outer[(i+2)%6][1]:.1f}"'
        f' stroke="{P}" stroke-width="1" opacity="0.18"/>'
        for i in range(0, 6, 2)
    )
    nodes = "".join(
        f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="10" fill="{P}"/>'
        for ox, oy in outer
    )
    hub = f'<circle cx="{cx}" cy="{cy}" r="24" fill="{A}"/>'
    return spokes + links + nodes + hub


def _sym_sweep(P: str, A: str) -> str:
    """Bold diagonal slash parallelogram with accent punctuation circle."""
    return (
        f'<path d="M 72,252 L 150,252 L 328,70 L 328,103 L 178,252 Z" fill="{P}"/>'
        f'<circle cx="317" cy="86" r="21" fill="{A}"/>'
    )


def _sym_grid(P: str, A: str) -> str:
    """4×4 pixel grid with a distinctive primary/accent colour pattern."""
    sq, gap, sx, sy = 28, 10, 129, 82
    pattern = [
        [P,    None, P,    A   ],
        [None, P,    A,    None],
        [A,    None, P,    P   ],
        [P,    A,    None, P   ],
    ]
    out = ""
    for ri, row in enumerate(pattern):
        for ci, col in enumerate(row):
            x = sx + ci * (sq + gap)
            y = sy + ri * (sq + gap)
            if col:
                out += f'<rect x="{x}" y="{y}" width="{sq}" height="{sq}" rx="5" fill="{col}"/>'
            else:
                out += (
                    f'<rect x="{x}" y="{y}" width="{sq}" height="{sq}" rx="5"'
                    f' stroke="{P}" stroke-width="1.5" fill="none" opacity="0.22"/>'
                )
    return out


def _sym_globe(P: str, A: str) -> str:
    """Globe outline with latitude lines (clipPath) and accent orbital ring."""
    return (
        '<defs><clipPath id="gc"><circle cx="200" cy="148" r="98"/></clipPath></defs>'
        f'<circle cx="200" cy="148" r="100" stroke="{P}" stroke-width="3.5" fill="none"/>'
        f'<g clip-path="url(#gc)">'
        f'<line x1="60" y1="115" x2="340" y2="115" stroke="{P}" stroke-width="1.5" opacity="0.45"/>'
        f'<line x1="60" y1="148" x2="340" y2="148" stroke="{P}" stroke-width="1.5" opacity="0.45"/>'
        f'<line x1="60" y1="181" x2="340" y2="181" stroke="{P}" stroke-width="1.5" opacity="0.45"/>'
        f'<line x1="200" y1="48"  x2="200" y2="248" stroke="{P}" stroke-width="1.5" opacity="0.45"/>'
        '</g>'
        f'<ellipse cx="200" cy="148" rx="132" ry="32" stroke="{A}" stroke-width="3.5"'
        f' fill="none" transform="rotate(-22 200 148)"/>'
        f'<circle cx="272" cy="116" r="9" fill="{A}"/>'
    )


def _sym_swoosh(P: str, A: str) -> str:
    """Smooth bezier swoosh from origin to destination, with accent dot."""
    return (
        f'<path d="M 68,268 C 92,202 188,148 318,95"'
        f' stroke="{P}" stroke-width="8" fill="none" stroke-linecap="round"/>'
        f'<circle cx="318" cy="95"  r="23" fill="{A}"/>'
        f'<circle cx="68"  cy="268" r="11" fill="{P}" opacity="0.4"/>'
    )


# ── Archetype dispatcher ───────────────────────────────────────────────────────
def _build_deterministic_svg(
    approach: str,
    brand_name: str,
    abbreviation: str,
    concept_num: int,
    concept_name: str,
    primary: str,
    accent: str,
) -> str:
    al = approach.lower()
    if   "monogram" in al:                         sym = _sym_monogram(primary, accent, abbreviation)
    elif "orbit"    in al or "ecosystem"  in al:   sym = _sym_orbit(primary, accent)
    elif "stack"    in al or "growth"     in al:   sym = _sym_growth(primary, accent)
    elif "arc"      in al or "bridge"     in al:   sym = _sym_bridge(primary, accent)
    elif "overlap"  in al or "tri"        in al:   sym = _sym_triform(primary, accent)
    elif "node"     in al or "network"    in al:   sym = _sym_network(primary, accent)
    elif "sweep"    in al or "dynamic"    in al:   sym = _sym_sweep(primary, accent)
    elif "grid"     in al or "digital"    in al:   sym = _sym_grid(primary, accent)
    elif "globe"    in al or "planet"     in al:   sym = _sym_globe(primary, accent)
    elif "journey"  in al or "swoosh"     in al:   sym = _sym_swoosh(primary, accent)
    else:                                           sym = _sym_orbit(primary, accent)

    bn = _xe(brand_name)
    ab = _xe(abbreviation)
    cn = _xe(concept_name).upper()

    return (
        f'<svg viewBox="0 0 400 400" width="400" height="400" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="400" height="400" fill="white"/>'
        f'{sym}'
        f'<line x1="60" y1="283" x2="340" y2="283" stroke="#e5e7eb" stroke-width="1"/>'
        f'<text x="200" y="316" text-anchor="middle" font-family="Arial,Helvetica,sans-serif"'
        f' font-size="26" font-weight="700" fill="{primary}">{bn}</text>'
        f'<text x="200" y="346" text-anchor="middle" font-family="Arial,Helvetica,sans-serif"'
        f' font-size="11" font-weight="600" letter-spacing="5" fill="{accent}">{ab}</text>'
        f'<text x="200" y="383" text-anchor="middle" font-family="Arial,Helvetica,sans-serif"'
        f' font-size="9" fill="#9ca3af">{concept_num}. {cn}</text>'
        f'</svg>'
    )

# ── Gemini brief system prompt ─────────────────────────────────────────────────
GEMINI_BRIEF_SYSTEM = """You are a world-class brand identity director at a top-tier creative agency (Pentagram / Landor / Wolff Olins level).

Use Google Search to:
1. Research the brand's top 3-5 direct competitors — find their actual logo styles, colours, fonts, visual identity
2. Find 2024-2025 logo/brand design trends specific to this industry
3. Identify unclaimed visual territory — directions no competitor has taken yet

Generate a comprehensive 10-concept logo design brief using the industry-standard template below.
Return ONLY valid JSON (no markdown fences, no text outside the JSON):

{
  "brief_text": "Full formatted design brief (1200+ words) structured as follows:

━━━ BRAND OVERVIEW ━━━
Full company name (abbreviation). Industry / sector. Core business description — what it does, key divisions/products/services, geographic focus. Brand essence / tagline. Values (list). Primary audience, secondary audience, tertiary audience.

━━━ DESIGN REQUIREMENTS ━━━
Symbol + wordmark logo system. Style descriptors. Symbol must abstractly express (5-7 keywords from brand essence, values, business model). Typography direction. Colour palette with primary (name + hex range), accent options, neutrals. 2024-25 design trends applied. Must work at: favicon, app icon, signage, digital UI, print, merchandise. Deliver 3 versions per concept: 1. Full-colour  2. Monochrome (black/white)  3. Inverted on dark background.

━━━ COMPETITOR VISUAL LANDSCAPE ━━━
(FROM LIVE SEARCH) Real competitor names, their logo styles, dominant colours, typography choices. Visual territory already occupied. Unclaimed visual space this brand can own.

━━━ 2024-25 INDUSTRY DESIGN TRENDS ━━━
(FROM LIVE SEARCH) Specific current trends relevant to this industry. Flat/minimal geometry, subtle gradients, responsive icon systems, monogram-friendly variants, plus industry-specific trend.

━━━ 10 LOGO CONCEPT DIRECTIONS ━━━
For each: concept number, visual approach name, brand-specific description of the direction, one-line rationale, typography, palette.",

  "concepts": [
    {
      "number": 1,
      "name": "short memorable name",
      "approach": "Interlocked Monogram",
      "direction": "Brand-specific: describe which letters interlock and what the combined form symbolises for this brand",
      "rationale": "One-line creative rationale — why this direction fits this brand specifically",
      "typography": "Google Font name",
      "palette": ["#primary", "#accent", "#neutral"]
    },
    {
      "number": 2,
      "name": "short memorable name",
      "approach": "Ecosystem Orbit",
      "direction": "Brand-specific: what central concept is the hub, what orbits it, what does it express about the business",
      "rationale": "one sentence",
      "typography": "Google Font name",
      "palette": ["#primary", "#accent", "#neutral"]
    },
    {
      "number": 3,
      "name": "short memorable name",
      "approach": "Growth Stack",
      "direction": "Brand-specific: what does the ascending stack represent — divisions, milestones, market growth",
      "rationale": "one sentence",
      "typography": "Google Font name",
      "palette": ["#primary", "#accent", "#neutral"]
    },
    {
      "number": 4,
      "name": "short memorable name",
      "approach": "Bridge Arc",
      "direction": "Brand-specific: what two entities / stakeholders / concepts does the arc connect",
      "rationale": "one sentence",
      "typography": "Google Font name",
      "palette": ["#primary", "#accent", "#neutral"]
    },
    {
      "number": 5,
      "name": "short memorable name",
      "approach": "Tri-form Overlap",
      "direction": "Brand-specific: what three pillars / divisions / audiences do the three forms represent",
      "rationale": "one sentence",
      "typography": "Google Font name",
      "palette": ["#primary", "#accent", "#neutral"]
    },
    {
      "number": 6,
      "name": "short memorable name",
      "approach": "Network Nodes",
      "direction": "Brand-specific: what does the network represent — partners, markets, service touchpoints",
      "rationale": "one sentence",
      "typography": "Google Font name",
      "palette": ["#primary", "#accent", "#neutral"]
    },
    {
      "number": 7,
      "name": "short memorable name",
      "approach": "Dynamic Sweep",
      "direction": "Brand-specific: what does the bold motion express — speed, momentum, transformation",
      "rationale": "one sentence",
      "typography": "Google Font name",
      "palette": ["#primary", "#accent", "#neutral"]
    },
    {
      "number": 8,
      "name": "short memorable name",
      "approach": "Digital Grid",
      "direction": "Brand-specific: how does the structured grid reflect the brand's precision, technology, or system",
      "rationale": "one sentence",
      "typography": "Google Font name",
      "palette": ["#primary", "#accent", "#neutral"]
    },
    {
      "number": 9,
      "name": "short memorable name",
      "approach": "Globe / Planet",
      "direction": "Brand-specific: what global or expansive concept does this express — reach, scale, ambition",
      "rationale": "one sentence",
      "typography": "Google Font name",
      "palette": ["#primary", "#accent", "#neutral"]
    },
    {
      "number": 10,
      "name": "short memorable name",
      "approach": "Journey Swoosh + Dot",
      "direction": "Brand-specific: what journey or transformation does the curve represent — origin to destination",
      "rationale": "one sentence",
      "typography": "Google Font name",
      "palette": ["#primary", "#accent", "#neutral"]
    }
  ],

  "primary_color": "#hex",
  "accent_color": "#hex",
  "neutral_dark": "#1A1A2E",
  "font": "primary Google Font for the brand wordmark",
  "style_descriptors": "modern, geometric, minimal, premium — add 2-3 brand-specific style words",
  "symbol_concepts": "5-7 keywords the symbol abstractly expresses (derived from brand essence + values)",
  "competitor_visual_notes": "3-4 sentences from live search: competitor names + visual styles + unclaimed territory"
}

Keep exact approach names. Return ONLY valid JSON."""

_FALLBACK_BRIEF_SYSTEM = (
    "You are a brand identity director. Generate a 10-concept logo design brief following the industry-standard template. "
    "Return ONLY valid JSON with keys: brief_text (structured with sections: BRAND OVERVIEW, DESIGN REQUIREMENTS, "
    "COMPETITOR VISUAL LANDSCAPE, 2024-25 TRENDS, 10 LOGO CONCEPT DIRECTIONS), "
    "concepts (array of 10 each with: number, name, approach, direction, rationale, typography, palette), "
    "primary_color, accent_color, neutral_dark, font, style_descriptors, symbol_concepts, competitor_visual_notes."
)


# ── Platform / category helpers ────────────────────────────────────────────────
def _platform_from_url(url: str) -> str:
    host = (urlparse(url).netloc or "").lower().replace("www.", "")
    if "pinterest"          in host: return "Pinterest"
    if "dribbble"           in host: return "Dribbble"
    if "behance"            in host: return "Behance"
    if "underconsideration" in host: return "Brand New"
    if "logopond"           in host: return "Logopond"
    if "logolounge"         in host: return "Logolounge"
    if "fontsinuse"         in host: return "Fonts In Use"
    return host.split(".")[0].title() if host else "Source"


def _category_from_platform(platform: str) -> str:
    if platform in ("Brand New", "Behance"):                   return "Case Studies"
    if platform in ("Logopond", "Logolounge"):                 return "Logo Gallery"
    if platform in ("Fonts In Use",):                          return "Typography"
    if platform in ("Dribbble",):                              return "Design Shots"
    if platform in ("Pinterest",):                             return "Moodboard"
    return "Reference"


async def _collect_inspiration_links(industry: str, concepts: list[dict]) -> list[dict]:
    import asyncio

    search_plan: list[dict] = []
    seen: set[str] = set()

    def _plan(label: str, query: str, reason: str, category: str):
        if query not in seen:
            seen.add(query)
            search_plan.append({"label": label, "query": query, "reason": reason, "category": category})

    _plan("Behance",          f"site:behance.net {industry} brand identity logo case study", "Brand identity case studies", "Case Studies")
    _plan("Brand New",        f"site:underconsideration.com/brandnew {industry} brand identity", "Professional brand critique", "Case Studies")
    _plan("Logopond",         f"site:logopond.com {industry} logo", "Curated logo gallery", "Logo Gallery")
    _plan("Logolounge",       f"site:logolounge.com {industry} logo trend", "Annual logo trends", "Logo Gallery")
    _plan("Dribbble – Logos", f"site:dribbble.com {industry} logo brand identity", "Logo explorations", "Design Shots")
    _plan("Fonts In Use",     f"site:fontsinuse.com {industry} brand logo", "Real brand typeface usage", "Typography")
    _plan("Pinterest",        f"site:pinterest.com {industry} logo brand identity inspiration", "Visual mood boards", "Moodboard")

    for c in concepts[:3]:
        approach = c.get("approach", "").split("/")[0].strip()
        if approach:
            _plan(f"Dribbble – {approach}", f"site:dribbble.com {approach} logo {industry}", f"Shots for {approach}", "Design Shots")

    async def _fetch(p: dict) -> list[dict]:
        results = await web_search(p["query"], num_results=4)
        out = []
        for r in results:
            link, title = r.get("link", ""), r.get("title", "")
            if link and title:
                plat = _platform_from_url(link)
                out.append({"title": title, "brand_name": title, "link": link,
                             "snippet": r.get("snippet", ""), "query_label": p["label"],
                             "platform": plat, "category": p.get("category") or _category_from_platform(plat),
                             "reason": p["reason"]})
        return out

    batches = await asyncio.gather(*[_fetch(p) for p in search_plan[:14]], return_exceptions=True)

    seen_links: set[str] = set()
    all_links: list[dict] = []
    for batch in batches:
        if isinstance(batch, Exception):
            continue
        for item in batch:
            if item["link"] not in seen_links:
                seen_links.add(item["link"])
                all_links.append(item)

    order = {"Case Studies": 0, "Logo Gallery": 1, "Design Shots": 2, "Typography": 3, "Moodboard": 4, "Reference": 5}
    all_links.sort(key=lambda x: order.get(x.get("category", "Reference"), 5))

    for plat, url, cat, reason in [
        ("Brand New", "https://www.underconsideration.com/brandnew/", "Case Studies", "Brand identity reviews"),
        ("Logopond", f"https://logopond.com/?filter={quote_plus(industry)}", "Logo Gallery", f"{industry} logos"),
        ("Dribbble", f"https://dribbble.com/search/{quote_plus(industry + ' logo')}", "Design Shots", f"{industry} logo shots"),
    ]:
        if not any(e["link"] == url for e in all_links):
            all_links.append({"title": f"{plat}: {industry}", "brand_name": plat, "link": url,
                               "snippet": reason, "query_label": plat, "platform": plat,
                               "category": cat, "reason": reason})

    print(f"[visual_identity_agent] Inspiration: {len(all_links)} links")
    return all_links[:30]


# ── GPT-4o symbol prompt ──────────────────────────────────────────────────────
_SYMBOL_SYSTEM = """\
You are a world-class SVG logo designer. Generate ONLY the inner SVG shape elements for a logo symbol mark.

STRICT OUTPUT RULES:
- Return ONLY SVG elements — NO full <svg> wrapper, NO <defs>, NO <style>, NO <text>
- Allowed tags: rect, circle, ellipse, path, polygon, polyline, line, g
- All coordinates must stay within x:60–340, y:30–265 (center: x=200, y=148)
- No JavaScript, no external refs, no event handlers, no clip-path ids
- Attribute values must be valid SVG strings
- Create 4–10 shapes that clearly express the visual approach
- The mark should be minimal, geometric, and professional

Return nothing except the raw SVG element(s). No explanation, no markdown."""

_SYMBOL_USER_TMPL = """\
Brand: {brand} ({abbr})
Tagline: "{tagline}"
Visual approach: {approach}
Concept name: {name}
Design direction: {direction}
Creative rationale: {rationale}
Primary colour: {primary}
Accent colour: {accent}

Draw a {approach} logo symbol for {brand} using the design direction above.
Express the brand's identity through minimal geometric shapes.
Primary colour {primary} for the main shapes. Accent colour {accent} for highlights."""


def _extract_svg_elements(raw: str) -> str:
    """Strip any accidental <svg> wrapper or markdown fences, return inner elements only."""
    if not raw:
        return ""
    # Strip markdown fences
    raw = re.sub(r"```[a-z]*\n?", "", raw).strip()
    # If there's a full <svg>…</svg>, extract inner content
    inner = re.search(r"<svg[^>]*>([\s\S]*?)</svg>", raw, re.IGNORECASE)
    if inner:
        raw = inner.group(1).strip()
    # Remove any <defs>, <style>, <text> blocks
    raw = re.sub(r"<defs[\s\S]*?</defs>", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"<style[\s\S]*?</style>", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"<text[\s\S]*?</text>", "", raw, flags=re.IGNORECASE)
    # Remove script tags and event handlers
    raw = re.sub(r"<script[\s\S]*?</script>", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r'\s+on\w+="[^"]*"', "", raw)
    # Keep only lines that look like SVG elements
    lines = [l for l in raw.splitlines() if l.strip() and not l.strip().startswith("<!--")]
    return "\n".join(lines).strip()


def _wordmark(brand_name: str, abbreviation: str, concept_num: int, concept_name: str,
              primary: str, accent: str) -> str:
    bn = _xe(brand_name)
    ab = _xe(abbreviation)
    cn = _xe(concept_name).upper()
    return (
        f'<line x1="60" y1="283" x2="340" y2="283" stroke="#e5e7eb" stroke-width="1"/>'
        f'<text x="200" y="316" text-anchor="middle" font-family="Arial,Helvetica,sans-serif"'
        f' font-size="26" font-weight="700" fill="{primary}">{bn}</text>'
        f'<text x="200" y="346" text-anchor="middle" font-family="Arial,Helvetica,sans-serif"'
        f' font-size="11" font-weight="600" letter-spacing="5" fill="{accent}">{ab}</text>'
        f'<text x="200" y="383" text-anchor="middle" font-family="Arial,Helvetica,sans-serif"'
        f' font-size="9" fill="#9ca3af">{concept_num}. {cn}</text>'
    )


def _wrap_svg(symbol: str, wm: str) -> str:
    return (
        '<svg viewBox="0 0 400 400" width="400" height="400" xmlns="http://www.w3.org/2000/svg">'
        '<rect width="400" height="400" fill="white"/>'
        f'{symbol}'
        f'{wm}'
        '</svg>'
    )


# ── SVG generation — GPT-4o symbol + deterministic wordmark ───────────────────
async def _generate_concept_svgs(
    brand_name: str,
    abbreviation: str,
    tagline: str,
    concepts: list[dict],
    primary_color: str,
    accent_color: str,
) -> list[dict]:
    """
    For each concept:
      1. Ask GPT-4o to generate brand-specific symbol SVG elements.
      2. Combine with deterministic wordmark section.
      3. Fall back to pre-built geometric template if GPT-4o fails.
    Runs sequentially — quality over speed.
    """
    final: list[dict] = []

    for i, concept in enumerate(concepts):
        palette   = concept.get("palette", [])
        c_primary = palette[0] if palette else primary_color
        c_accent  = palette[1] if len(palette) > 1 else accent_color

        num  = concept.get("number", i + 1)
        name = concept.get("name", "")
        approach   = concept.get("approach", "")
        direction  = concept.get("direction", approach)
        rationale  = concept.get("rationale", "")

        print(f"[visual_identity_agent] SVG {i+1}/{len(concepts)}: {name} ({approach})")

        wm  = _wordmark(brand_name, abbreviation, num, name, c_primary, c_accent)
        sym = ""

        # ── Attempt: GPT-4o brand-specific symbol ────────────────────────────
        try:
            user_prompt = _SYMBOL_USER_TMPL.format(
                brand=brand_name, abbr=abbreviation, tagline=tagline,
                approach=approach, name=name,
                direction=direction, rationale=rationale,
                primary=c_primary, accent=c_accent,
            )
            raw = await call_openai(
                system_prompt=_SYMBOL_SYSTEM,
                user_prompt=user_prompt,
                model="gpt-4o",
                temperature=0.6,
                max_tokens=1200,
                json_mode=False,
            )
            sym = _extract_svg_elements(raw)
        except Exception as exc:
            print(f"[visual_identity_agent] GPT-4o failed for concept {num}: {exc}")

        # ── Fallback: deterministic geometric template ────────────────────────
        if not sym or len(sym) < 40:
            print(f"[visual_identity_agent] Using deterministic fallback for concept {num}")
            fallback_svg = _build_deterministic_svg(
                approach=approach, brand_name=brand_name, abbreviation=abbreviation,
                concept_num=num, concept_name=name, primary=c_primary, accent=c_accent,
            )
            final.append({**concept, "svg": fallback_svg})
            continue

        final.append({**concept, "svg": _wrap_svg(sym, wm)})

    ai_ok = sum(1 for c in final if c.get("svg") and "SVG pending" not in c["svg"])
    print(f"[visual_identity_agent] SVGs complete: {ai_ok}/{len(final)}")
    return final


# ── regenerate_variant_svg kept for brand.py API ───────────────────────────────
async def regenerate_variant_svg(
    variant: dict,
    variant_index: int,   # noqa: ARG001 – kept for call-site compatibility
    brand_name: str,      # noqa: ARG001 – kept for call-site compatibility
    new_color_palette: list[str],
    heading_font: str | None = None,
    body_font: str | None = None,
) -> dict:
    updated = dict(variant)
    updated["color_palette"] = new_color_palette
    if heading_font:
        updated["heading_font"] = heading_font
    if body_font:
        updated["body_font"] = body_font
    updated["logo_svg"] = None
    updated["logo_url"] = None
    return updated


# ── Main agent entry point ─────────────────────────────────────────────────────
async def run(
    idea_discovery_data: dict,
    market_research_data: dict,
    competitor_data: dict,
    strategy_data: dict,
    naming_data: dict,
    feedback: str | None = None,
) -> AgentResult:
    idea_discovery_data  = idea_discovery_data  if isinstance(idea_discovery_data,  dict) else {}
    market_research_data = market_research_data if isinstance(market_research_data, dict) else {}
    competitor_data      = competitor_data      if isinstance(competitor_data,      dict) else {}
    strategy_data        = strategy_data        if isinstance(strategy_data,        dict) else {}
    naming_data          = naming_data          if isinstance(naming_data,          dict) else {}

    brand_name    = naming_data.get("brand_name", "Brand")
    tagline       = naming_data.get("tagline", "")
    industry      = idea_discovery_data.get("industry_category", "")
    problem       = idea_discovery_data.get("problem_solved", "")
    value_prop    = idea_discovery_data.get("value_proposition", "")
    tone_hints    = idea_discovery_data.get("brand_tone_hints", "")
    bp            = strategy_data.get("brand_personality", {})
    brand_personality = bp if isinstance(bp, dict) else {}
    archetype     = brand_personality.get("archetype", "modern")
    tone_voice    = brand_personality.get("tone_of_voice", "")
    brand_values  = strategy_data.get("brand_values", [])
    positioning   = strategy_data.get("positioning_statement", "")
    target_segs   = strategy_data.get("target_segments", [])
    market_trends = market_research_data.get("market_trends", [])
    competitor_names = [
        c.get("name", "") for c in competitor_data.get("direct_competitors", [])[:5]
        if isinstance(c, dict) and c.get("name")
    ]
    abbreviation = "".join(w[0].upper() for w in brand_name.split() if w)

    # ── Step 1: Gemini generates design brief ─────────────────────────────────
    values_str    = ", ".join(str(v) for v in brand_values) if brand_values else "Not specified"
    audience_list = [str(s) for s in target_segs[:3]]
    audience_str  = ", ".join(audience_list) if audience_list else "General market"
    competitors_str = ", ".join(competitor_names) if competitor_names else "research online"
    trends_str    = ", ".join(str(t) for t in market_trends[:4]) if market_trends else "research current trends"

    user_prompt = (
        f"Create 10 distinct, high-quality logo concepts for:\n\n"
        f"Company: {brand_name} ({abbreviation})\n"
        f"Industry / Sector: {industry}\n"
        f"Core Business: {problem}. {value_prop}\n"
        f'Brand Essence / Tagline: "{tagline}"\n'
        f"Brand Personality: {archetype} — {tone_voice}\n"
        f"Tone Hints: {tone_hints}\n"
        f"Values: {values_str}\n"
        f"Target Audiences: {audience_str}\n"
        f"Known Competitors: {competitors_str}\n"
        f"Positioning: {positioning}\n"
        f"Market Trends Identified: {trends_str}\n\n"
        f"Design Requirements:\n"
        f"- Symbol + wordmark logo system\n"
        f"- Style: modern, geometric, minimal, premium yet accessible — refine based on brand personality\n"
        f"- Symbol must abstractly express the brand's core values and business model (5-7 keywords)\n"
        f"- Typography: modern sans-serif, clean, strong, highly legible\n"
        f"- Colour palette: research 2024-25 trends for {industry}, avoid colours dominated by competitors\n"
        f"- Must work at: favicon, app icon, signage, digital UI, print, merchandise\n"
        f"- Deliver 3 versions per concept: 1. Full-colour  2. Monochrome (black/white)  3. Inverted on dark background\n"
        f"- Latest 2024-25 trends: flat/minimal geometry, subtle gradients, responsive icon system, monogram-friendly\n\n"
        + (f"Additional feedback to apply: {feedback}\n\n" if feedback else "")
        + f"Research {competitors_str} and other competitors online. Generate the full 10-concept brief following the template."
    )

    print(f"[visual_identity_agent] Step 1 — Gemini brief for '{brand_name}'")
    raw_json = await call_gemini_with_search(
        system_prompt=GEMINI_BRIEF_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.7,
    )

    try:
        brief_data = json.loads(raw_json) if raw_json and raw_json != "{}" else {}
    except Exception as exc:
        print(f"[visual_identity_agent] Gemini JSON parse error: {exc}")
        brief_data = {}

    if not brief_data or not brief_data.get("concepts"):
        print("[visual_identity_agent] Gemini empty — falling back to Groq")
        fallback_raw = await call_llm(
            system_prompt=_FALLBACK_BRIEF_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.7,
            max_tokens=4096,
        )
        try:
            clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', fallback_raw.strip(), flags=re.MULTILINE)
            brief_data = json.loads(clean)
        except Exception:
            brief_data = {}

    brief_text        = brief_data.get("brief_text", "")
    concepts          = brief_data.get("concepts", [])
    primary_color     = brief_data.get("primary_color", "#005B80")
    accent_color      = brief_data.get("accent_color", "#FFB300")
    neutral_dark      = brief_data.get("neutral_dark", "#1A1A2E")
    font              = brief_data.get("font", "Inter")
    style_descriptors = brief_data.get("style_descriptors", "")
    symbol_concepts   = brief_data.get("symbol_concepts", "")
    competitor_notes  = brief_data.get("competitor_visual_notes", "")

    if not isinstance(concepts, list):
        concepts = []

    print(f"[visual_identity_agent] Brief done — {len(concepts)} concepts, colors: {primary_color} / {accent_color}")

    # ── Step 2: Generate brand-specific SVGs (GPT-4o + deterministic fallback) ─
    concepts_with_svg: list[dict] = []
    if concepts:
        print(f"[visual_identity_agent] Step 2 — generating {len(concepts)} brand-specific SVGs")
        concepts_with_svg = await _generate_concept_svgs(
            brand_name, abbreviation, tagline, concepts, primary_color, accent_color
        )
    else:
        print("[visual_identity_agent] No concepts — skipping SVG generation")

    # ── Step 3: Inspiration links ─────────────────────────────────────────────
    inspiration_links = await _collect_inspiration_links(industry, concepts)

    svg_count = sum(1 for c in concepts_with_svg if c.get("svg") and "SVG pending" not in c["svg"])

    data: dict = {
        "design_concepts":         concepts_with_svg,
        "logo_design_brief":       brief_text,
        "competitor_visual_notes": competitor_notes,
        "primary_color":           primary_color,
        "accent_color":            accent_color,
        "neutral_dark":            neutral_dark,
        "font":                    font,
        "style_descriptors":       style_descriptors,
        "symbol_concepts":         symbol_concepts,
        "logo_inspiration":        inspiration_links,
        # Legacy keys
        "variants":                [],
        "logo_image_url":          "",
        "design_style":            archetype,
        "combined_summary": (
            f"10-concept SVG logo brief for {brand_name} ({abbreviation}). "
            f"{svg_count}/{len(concepts_with_svg)} SVGs generated. "
            f"{len(inspiration_links)} inspiration links."
        ),
    }

    explanation = (
        f"Visual identity for '{brand_name}': Gemini researched competitors and generated "
        f"10 logo concepts covering all visual archetypes. "
        f"{svg_count} downloadable SVGs generated. "
        f"{len(inspiration_links)} inspiration links collected."
    )

    return AgentResult(data=data, explanation=explanation)
