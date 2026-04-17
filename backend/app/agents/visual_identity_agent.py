"""
Agent 6 – Visual Identity Intelligence Agent (v6)

Pipeline:
  1. Gemini (+ Google Search) — researches competitors, generates brand-tailored
     10-concept logo design brief with rich visual_concept descriptions.
  2. Inspiration links collected from visual-keyword-based searches.

SVG/image generation is no longer done here — the frontend LogoGenerator
panel lets the user paste a reference image URL + prompt, and the
/api/logo/generate endpoint uses gpt-image-1 to produce a brand-specific
logo image from that reference.

Output data keys:
  design_concepts     – list of 10 dicts with visual_concept descriptions (no SVG)
  logo_design_brief   – full text brief from Gemini
  competitor_visual_notes
  primary_color / accent_color / neutral_dark / font / style_descriptors / symbol_concepts
  logo_inspiration    – curated designer reference links
"""
import json
import re
from urllib.parse import quote_plus, urlparse

from app.schemas.brand_schema import AgentResult
from app.utils.gemini_search import call_gemini_with_search
from app.utils.llm import call_llm
from app.utils.search import web_search

# ── Gemini brief system prompt ─────────────────────────────────────────────────
GEMINI_BRIEF_SYSTEM = """You are a world-class brand identity director at Pentagram / Landor / Wolff Olins level.

Use Google Search to:
1. Research the brand's top 3-5 direct competitors — logo styles, colours, fonts, visual identity
2. Find 2024-2025 logo design trends specific to this industry
3. Identify unclaimed visual territory no competitor has taken yet

Generate 10 COMPLETELY ORIGINAL logo concepts specific to this brand.
DO NOT use generic archetype names. Invent unique visual ideas rooted in this brand's story, values, and market.
Each concept must be visually distinct from the others.

Return ONLY valid JSON (no markdown, no text outside JSON):

{
  "brief_text": "Full design brief (1200+ words):
━━━ BRAND OVERVIEW ━━━
Company name (abbreviation), industry, core business, brand essence/tagline, values, audiences.
━━━ DESIGN REQUIREMENTS ━━━
Symbol + wordmark system. Style. 5-7 keywords symbols must express. Typography direction.
Colour palette (primary + accent + neutrals). 2024-25 trends. Works at: favicon, app icon, signage, digital, print, merch.
3 versions per concept: full-colour, monochrome, dark-inverted.
━━━ COMPETITOR VISUAL LANDSCAPE ━━━ (FROM LIVE SEARCH)
Real competitor names, logo styles, colours, fonts. Occupied visual territory. Unclaimed space.
━━━ 2024-25 INDUSTRY DESIGN TRENDS ━━━ (FROM LIVE SEARCH)
Specific current trends for this industry.
━━━ 10 LOGO CONCEPTS ━━━
Each with: concept name, precise visual description, rationale, typography, palette.",

  "concepts": [
    {
      "number": 1,
      "name": "Short memorable concept title",
      "visual_concept": "Precise visual description (4-6 sentences): what exact shapes to draw, their positions and proportions, how they relate to each other, what brand metaphor or story they express. Be specific — a designer must be able to execute this without any ambiguity. Example: Two thin curved lines rising from a shared base point, diverging outward like wings or a valley opening up, primary colour on the left curve, accent on the right. A small filled circle sits at the convergence point representing the origin. Together they suggest growth, duality, and upward momentum.",
      "rationale": "One sentence: why this specific visual idea represents this brand",
      "typography": "Specific Google Font name",
      "palette": ["#hex_primary", "#hex_accent", "#hex_neutral"]
    },
    ... 9 more, all visually distinct, all rooted in this brand's identity
  ],

  "primary_color": "#hex",
  "accent_color": "#hex",
  "neutral_dark": "#hex",
  "font": "primary Google Font for wordmark",
  "style_descriptors": "3-5 style keywords specific to this brand",
  "symbol_concepts": "5-7 keywords the symbols abstractly express",
  "competitor_visual_notes": "3-4 sentences: competitor names + visual styles (from search) + unclaimed visual territory"
}

Rules:
- visual_concept is the most important field — make it rich, specific, drawable
- 10 concepts must cover a genuine range: letterform/monogram, metaphor/icon, abstract geometry,
  motion/energy, structural, organic, systematic, orbital, networked, journey — but expressed
  as original ideas for THIS brand, not as generic templates
- Each concept gets its own palette (derived from the global palette with variations)
- Return ONLY valid JSON"""

_FALLBACK_BRIEF_SYSTEM = (
    "You are a brand identity director. Generate 10 completely original logo concepts for this brand. "
    "Do NOT use generic archetype names — invent unique visual ideas rooted in the brand's story. "
    "Return ONLY valid JSON with keys: brief_text, "
    "concepts (array of 10, each with: number, name, visual_concept, rationale, typography, palette), "
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


_VISUAL_STOP = {
    "a", "an", "the", "and", "or", "of", "to", "in", "for", "with", "as", "at",
    "by", "from", "on", "are", "is", "be", "been", "that", "this", "they", "it",
    "its", "has", "have", "which", "each", "their", "into", "between", "through",
    "around", "above", "below", "left", "right", "both", "where", "while", "when",
    "also", "very", "more", "two", "three", "four", "five", "six", "one", "upon",
    "creating", "suggesting", "expressing", "representing", "forming", "using",
    "gives", "give", "make", "creates", "create", "together", "overall",
}


def _visual_keywords(visual_concept: str, name: str) -> list[str]:
    """
    Extract 3-4 searchable visual shape/metaphor keywords from a concept.
    Pulls from the concept name + first two sentences of visual_concept.
    """
    first_two = ". ".join(visual_concept.split(".")[:2]) if visual_concept else ""
    text = f"{name} {first_two}"
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text)
    seen_kw: set[str] = set()
    result: list[str] = []
    for w in words:
        lw = w.lower()
        if lw not in _VISUAL_STOP and lw not in seen_kw:
            seen_kw.add(lw)
            result.append(lw)
        if len(result) >= 4:
            break
    return result


async def _collect_inspiration_links(industry: str, concepts: list[dict]) -> list[dict]:
    import asyncio

    search_plan: list[dict] = []
    seen: set[str] = set()

    def _plan(label: str, query: str, reason: str, category: str):
        if query not in seen:
            seen.add(query)
            search_plan.append({"label": label, "query": query, "reason": reason, "category": category})

    # ── Base industry searches (platform variety) ─────────────────────────────
    _plan("Behance – Industry",  f"site:behance.net {industry} brand identity logo case study", "Brand identity case studies", "Case Studies")
    _plan("Brand New",           f"site:underconsideration.com/brandnew {industry} brand identity", "Professional brand critique", "Case Studies")
    _plan("Logolounge",          f"site:logolounge.com {industry} logo trend", "Annual logo trends", "Logo Gallery")
    _plan("Fonts In Use",        f"site:fontsinuse.com {industry} brand logo", "Real brand typeface usage", "Typography")
    _plan("Pinterest – Brand",   f"site:pinterest.com {industry} logo brand identity inspiration", "Visual mood boards", "Moodboard")

    # ── Per-concept: search by visual keywords extracted from visual_concept ──
    # These make the inspiration resonate with what's actually being drawn.
    for c in concepts[:5]:
        name    = c.get("name", "").strip()
        vc      = c.get("visual_concept", "")
        kws     = _visual_keywords(vc, name)
        if not kws:
            continue
        kw2 = " ".join(kws[:2])   # e.g. "converging curves"
        kw3 = " ".join(kws[:3])   # e.g. "converging curves rising"

        _plan(
            f"Dribbble – {name}",
            f"site:dribbble.com {kw2} logo brand identity",
            f"Visual inspiration matching '{kw2}' shapes in concept '{name}'",
            "Design Shots",
        )
        _plan(
            f"Behance – {name}",
            f"site:behance.net {kw3} logo branding",
            f"Case study with '{kw3}' visual language for concept '{name}'",
            "Case Studies",
        )
        _plan(
            f"Logopond – {name}",
            f"site:logopond.com {kw2} logo",
            f"Logo gallery matching '{kw2}' for concept '{name}'",
            "Logo Gallery",
        )

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

    # Cap to 20 queries: 5 base + up to 15 per-concept (5 concepts × 3 queries)
    batches = await asyncio.gather(*[_fetch(p) for p in search_plan[:20]], return_exceptions=True)

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

    # Attach concept context to each link so the frontend can group/label them
    for c in concepts[:5]:
        name = c.get("name", "")
        kws  = _visual_keywords(c.get("visual_concept", ""), name)
        for link in all_links:
            ql = link.get("query_label", "")
            if name and name in ql:
                link["concept_name"]  = name
                link["visual_keywords"] = " · ".join(kws)

    # Static fallback links if search returned nothing useful
    for plat, url, cat, reason in [
        ("Brand New", "https://www.underconsideration.com/brandnew/", "Case Studies", "Brand identity reviews"),
        ("Logopond", f"https://logopond.com/?filter={quote_plus(industry)}", "Logo Gallery", f"{industry} logos"),
        ("Dribbble",  f"https://dribbble.com/search/{quote_plus(industry + ' logo')}", "Design Shots", f"{industry} logo shots"),
    ]:
        if not any(e["link"] == url for e in all_links):
            all_links.append({"title": f"{plat}: {industry}", "brand_name": plat, "link": url,
                               "snippet": reason, "query_label": plat, "platform": plat,
                               "category": cat, "reason": reason})

    print(f"[visual_identity_agent] Inspiration: {len(all_links)} links")
    return all_links[:35]




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

    # ── Step 2: Inspiration links ─────────────────────────────────────────────
    inspiration_links = await _collect_inspiration_links(industry, concepts)

    data: dict = {
        "design_concepts":         concepts,
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
            f"10-concept logo brief for {brand_name} ({abbreviation}). "
            f"{len(concepts)} concepts ready. "
            f"{len(inspiration_links)} inspiration links."
        ),
    }

    explanation = (
        f"Visual identity for '{brand_name}': Gemini researched competitors and generated "
        f"10 distinct logo concepts with visual descriptions. "
        f"Use the Logo Generator panel to produce images from reference links. "
        f"{len(inspiration_links)} inspiration links collected."
    )

    return AgentResult(data=data, explanation=explanation)
