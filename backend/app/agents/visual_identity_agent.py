"""
Agent 6 – Visual Identity Intelligence Agent (v4)

Pipeline:
  1. Gemini (+ Google Search) — researches competitors, generates brand-tailored
     10-concept logo design brief.
  2. Gemini (no search, 10 parallel calls) — generates one downloadable SVG per concept.
  3. Inspiration links collected in parallel.

Output data keys:
  design_concepts     – list of 10 dicts, each with "svg" field (self-contained SVG string)
  logo_design_brief   – full text brief from Gemini
  competitor_visual_notes
  primary_color / accent_color / neutral_dark / font
  logo_inspiration    – curated designer reference links
"""
import json
import re
from urllib.parse import quote_plus, urlparse

from app.schemas.brand_schema import AgentResult
from app.utils.gemini_search import call_gemini_with_search, call_gemini_for_svg
from app.utils.llm import call_llm
from app.utils.search import web_search


# ── Archetype → concrete SVG construction guide ───────────────────────────────
_ARCHETYPE_SVG_GUIDE: dict[str, str] = {
    "Interlocked Monogram": (
        "Draw overlapping geometric letter shapes for the brand initials. "
        "Use thin rectangles and diagonal strokes that interlock at precise angles to form a unified mark. "
        "Stroke-width 3-5, primary color. Stroke only on letter shapes — no fill."
    ),
    "Ecosystem Orbit": (
        "Central filled circle (r=38) in primary color at canvas center (200,155). "
        "Surrounding orbit ring: circle cx='200' cy='155' r='85' stroke=primary stroke-width='3' fill='none'. "
        "Three small filled circles (r=10) on the orbit ring at 0deg, 120deg, 240deg — one in accent color."
    ),
    "Growth Stack": (
        "Five ascending vertical bars, bottom-aligned at y=255. "
        "Heights: 70, 100, 130, 155, 185px. Width=28px, gap=12px, centered horizontally (leftmost bar starts at x=100). "
        "First four bars: primary color. Fifth (tallest) bar: accent color."
    ),
    "Bridge Arc": (
        "Wide arc: path d='M 80,215 Q 200,85 320,215' stroke=primary stroke-width='8' fill='none'. "
        "Two vertical lines from arc endpoints down: (80,215)→(80,258) and (320,215)→(320,258). "
        "Horizontal base line: (80,258)→(320,258). Small filled circles (r=8, accent) at both arc endpoints."
    ),
    "Tri-form Overlap": (
        "Three circles (r=65), overlapping by ~25%, arranged in a triangle. "
        "Centers: top (200,115), bottom-left (153,205), bottom-right (247,205). "
        "Each circle: stroke only, no fill, stroke-width=4. "
        "Colors: primary color, accent color, and a desaturated blend of both for the third."
    ),
    "Network Nodes": (
        "Six small filled circles (r=10) at: (130,125), (200,95), (268,135), (148,205), (238,195), (194,160). "
        "Connect them with thin lines (stroke-width=1.5, primary at 50% opacity). "
        "Central node at (194,160): r=22, accent color. Five outer nodes: primary color."
    ),
    "Dynamic Sweep": (
        "Bold upward-right sweep: path d='M 75,245 L 135,245 L 300,95 L 322,95 L 322,128 L 168,245 Z' fill=primary. "
        "Accent punctuation dot: circle cx='311' cy='108' r='18' fill=accent."
    ),
    "Digital Grid": (
        "Draw a 4x4 grid of squares (each 28x28px, gap=10px), top-left at (114,68). "
        "Fill pattern (P=primary, A=accent, E=empty/stroke-only): "
        "Row1: P A P E  Row2: A P E P  Row3: P E A P  Row4: E P P A. "
        "Empty squares: stroke=primary stroke-width=1.5 fill=none."
    ),
    "Globe / Planet": (
        "Globe circle: cx='200' cy='160' r='95' stroke=primary stroke-width='4' fill='none'. "
        "Two latitude ellipses inside: "
        "  ellipse cx='200' cy='140' rx='95' ry='22' stroke=primary stroke-width='2' fill='none'. "
        "  ellipse cx='200' cy='182' rx='95' ry='22' stroke=primary stroke-width='2' fill='none'. "
        "Orbital ring: ellipse cx='200' cy='160' rx='125' ry='28' stroke=accent stroke-width='3' fill='none' transform='rotate(-20 200 160)'."
    ),
    "Journey Swoosh + Dot": (
        "Flowing curve: path d='M 68,268 C 98,198 198,145 312,98' stroke=primary stroke-width='7' fill='none' stroke-linecap='round'. "
        "Destination dot: circle cx='312' cy='98' r='20' fill=accent. "
        "Origin dot: circle cx='68' cy='268' r='10' fill=primary opacity='0.4'."
    ),
}

_FALLBACK_GUIDE = "Create an abstract minimal geometric mark using circles, rectangles, and lines in the primary and accent colors, centered in the canvas."

# ── SVG system prompt ──────────────────────────────────────────────────────────
_SVG_SYSTEM_PROMPT = """You are a professional SVG graphic designer creating minimal geometric logos.
Return ONLY raw SVG markup — no explanation, no markdown fences, no other text.

STRICT RULES:
- Start with <svg and end with </svg>
- Use ONLY: rect, circle, ellipse, path, polygon, line, polyline, text, g, defs, linearGradient, stop
- NO JavaScript, NO external images, NO foreignObject, NO HTML, NO CSS @import
- All attribute values must be quoted strings with explicit numeric values
- Font: font-family="Arial, Helvetica, sans-serif" only"""

# ── Gemini brief system prompt ─────────────────────────────────────────────────
GEMINI_BRIEF_SYSTEM = """You are a world-class brand identity director at a top-tier creative agency (Pentagram / Landor / Wolff Olins level).

Use Google Search to:
1. Research the brand's top 3-5 direct competitors — find their actual logo styles, colors, visual identity details
2. Find 2024-2025 logo design trends specific to this industry
3. Identify unclaimed visual territory — directions no competitor has taken

Generate a comprehensive 10-concept logo design brief. Return ONLY valid JSON:

{
  "brief_text": "Full formatted design brief (1000+ words). Sections: BRAND OVERVIEW, COMPETITOR VISUAL LANDSCAPE (real names + visual details from search), 2024-25 INDUSTRY TRENDS (from search), DESIGN DIRECTION, 10 LOGO CONCEPTS. Use section headers.",
  "concepts": [
    {"number": 1, "name": "short name", "approach": "Interlocked Monogram", "rationale": "one sentence specific to this brand"},
    {"number": 2, "name": "short name", "approach": "Ecosystem Orbit", "rationale": "one sentence"},
    {"number": 3, "name": "short name", "approach": "Growth Stack", "rationale": "one sentence"},
    {"number": 4, "name": "short name", "approach": "Bridge Arc", "rationale": "one sentence"},
    {"number": 5, "name": "short name", "approach": "Tri-form Overlap", "rationale": "one sentence"},
    {"number": 6, "name": "short name", "approach": "Network Nodes", "rationale": "one sentence"},
    {"number": 7, "name": "short name", "approach": "Dynamic Sweep", "rationale": "one sentence"},
    {"number": 8, "name": "short name", "approach": "Digital Grid", "rationale": "one sentence"},
    {"number": 9, "name": "short name", "approach": "Globe / Planet", "rationale": "one sentence"},
    {"number": 10, "name": "short name", "approach": "Journey Swoosh + Dot", "rationale": "one sentence"}
  ],
  "primary_color": "#hex",
  "accent_color": "#hex",
  "neutral_dark": "#1A1A2E",
  "font": "Google Font name",
  "competitor_visual_notes": "2-3 sentences on competitor visual landscape and unclaimed territory"
}

Return ONLY valid JSON. No markdown fences, no text outside the JSON."""

_FALLBACK_BRIEF_SYSTEM = (
    "You are a brand identity director. Generate a 10-concept logo design brief. "
    "Return ONLY valid JSON with keys: brief_text, concepts (array of 10 with number/name/approach/rationale), "
    "primary_color, accent_color, neutral_dark, font, competitor_visual_notes."
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


# ── SVG generation (10 parallel Gemini calls) ──────────────────────────────────
async def _generate_concept_svgs(
    brand_name: str,
    abbreviation: str,
    tagline: str,
    concepts: list[dict],
    primary_color: str,
    accent_color: str,
) -> list[dict]:
    import asyncio

    def _placeholder(number: int, name: str) -> str:
        return (
            f'<svg viewBox="0 0 400 400" width="400" height="400" xmlns="http://www.w3.org/2000/svg">'
            f'<rect width="400" height="400" fill="white"/>'
            f'<rect x="170" y="150" width="60" height="60" rx="6" fill="{primary_color}" opacity="0.12"/>'
            f'<text x="200" y="188" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" fill="{primary_color}" opacity="0.35">SVG pending</text>'
            f'<line x1="60" y1="285" x2="340" y2="285" stroke="#e5e7eb" stroke-width="1"/>'
            f'<text x="200" y="318" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="26" font-weight="700" fill="{primary_color}">{brand_name}</text>'
            f'<text x="200" y="348" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="11" letter-spacing="5" fill="{accent_color}">{abbreviation}</text>'
            f'<text x="200" y="385" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="9" fill="#9ca3af">{number}. {name.upper()}</text>'
            f'</svg>'
        )

    async def _generate_one(concept: dict) -> dict:
        approach = concept.get("approach", "")

        # Find matching archetype guide
        guide_raw = _FALLBACK_GUIDE
        for key, val in _ARCHETYPE_SVG_GUIDE.items():
            key_root = key.lower().split("/")[0].strip()
            if key_root in approach.lower():
                guide_raw = val
                break

        guide = (
            guide_raw
            .replace("{primary}", primary_color)
            .replace("{accent}", accent_color)
            .replace("primary color", primary_color)
            .replace("accent color", accent_color)
        )

        prompt = (
            f"{_SVG_SYSTEM_PROMPT}\n\n"
            f"Brand: {brand_name} | Abbreviation: {abbreviation} | Tagline: {tagline}\n"
            f"Concept {concept['number']}: {concept['name']} — {approach}\n"
            f"Rationale: {concept.get('rationale', '')}\n"
            f"Primary color: {primary_color} | Accent color: {accent_color}\n\n"
            f"SYMBOL CONSTRUCTION (follow precisely):\n{guide}\n\n"
            f"SVG SPEC: viewBox=\"0 0 400 400\" width=\"400\" height=\"400\" xmlns=\"http://www.w3.org/2000/svg\"\n\n"
            f"REQUIRED STRUCTURE:\n"
            f'1. <rect width="400" height="400" fill="white"/>\n'
            f"2. Draw the symbol mark centered in the area x:60-340, y:30-270 using the construction guide above\n"
            f'3. <line x1="60" y1="283" x2="340" y2="283" stroke="#e5e7eb" stroke-width="1"/>\n'
            f'4. <text x="200" y="316" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" '
            f'font-size="26" font-weight="700" fill="{primary_color}">{brand_name}</text>\n'
            f'5. <text x="200" y="346" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" '
            f'font-size="11" font-weight="600" letter-spacing="5" fill="{accent_color}">{abbreviation}</text>\n'
            f'6. <text x="200" y="383" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" '
            f'font-size="9" fill="#9ca3af">{concept["number"]}. {concept["name"].upper()}</text>\n\n'
            f"Return ONLY the complete SVG. No text before or after."
        )

        svg = await call_gemini_for_svg(prompt)
        if not svg:
            print(f"[visual_identity_agent] SVG empty for concept {concept['number']} — using placeholder")
            svg = _placeholder(concept["number"], concept["name"])

        return {**concept, "svg": svg}

    tasks = [_generate_one(c) for c in concepts]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    final: list[dict] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"[visual_identity_agent] Concept {i + 1} exception: {result}")
            final.append({**concepts[i], "svg": _placeholder(concepts[i]["number"], concepts[i]["name"])})
        else:
            final.append(result)

    svg_ok = sum(1 for r in final if r.get("svg") and "SVG pending" not in r["svg"])
    print(f"[visual_identity_agent] SVGs: {svg_ok}/{len(final)} generated successfully")
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
    user_prompt = (
        f"Brand Name: {brand_name}\nAbbreviation: {abbreviation}\nTagline: {tagline}\n"
        f"Industry: {industry}\nBusiness: {problem}\nValue Proposition: {value_prop}\n"
        f"Brand Personality: {archetype} — {tone_voice}\nTone Hints: {tone_hints}\n"
        f"Brand Values: {', '.join(str(v) for v in brand_values)}\n"
        f"Target Audience: {json.dumps(target_segs[:2])}\n"
        f"Known Competitors: {', '.join(competitor_names) or 'None identified yet'}\n"
        f"Positioning: {positioning}\n"
        f"Market Trends: {', '.join(str(t) for t in market_trends[:4])}\n"
        + (f"\nFeedback to apply: {feedback}\n" if feedback else "")
        + "\nResearch competitors online and generate the 10-concept logo design brief."
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

    brief_text       = brief_data.get("brief_text", "")
    concepts         = brief_data.get("concepts", [])
    primary_color    = brief_data.get("primary_color", "#005B80")
    accent_color     = brief_data.get("accent_color", "#FFB300")
    neutral_dark     = brief_data.get("neutral_dark", "#1A1A2E")
    font             = brief_data.get("font", "Inter")
    competitor_notes = brief_data.get("competitor_visual_notes", "")

    if not isinstance(concepts, list):
        concepts = []

    print(f"[visual_identity_agent] Brief done — {len(concepts)} concepts, colors: {primary_color} / {accent_color}")

    # ── Step 2: Generate SVG per concept (parallel) ───────────────────────────
    concepts_with_svg: list[dict] = []
    if concepts:
        print(f"[visual_identity_agent] Step 2 — generating {len(concepts)} SVGs in parallel")
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
