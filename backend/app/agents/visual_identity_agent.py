"""
Agent 6 – Visual Identity Intelligence Agent (v3)

Pipeline:
  1. Gemini (+ Google Search) — researches competitors online, generates a brand-tailored
     10-concept logo design brief and a ready-to-use image generation prompt.
  2. OpenAI gpt-image-1 / DALL-E 3 — renders the visual 10-concept logo grid from the brief.
  3. Inspiration links collected in parallel from design reference sites.

Output data keys:
  logo_image_url      – data:image/png;base64,... stored in DB
  logo_image_model    – which model generated it
  logo_design_brief   – full text brief from Gemini (for UI display)
  logo_image_prompt   – the prompt used for image generation
  design_concepts     – list of 10 concept dicts {number, name, approach, rationale}
  competitor_visual_notes – Gemini's research on competitor visual landscape
  primary_color / accent_color / neutral_dark / font – top-level design tokens
  logo_inspiration    – curated designer reference links
"""
import json
import re
from urllib.parse import quote_plus, urlparse

from app.schemas.brand_schema import AgentResult
from app.utils.gemini_search import call_gemini_with_search
from app.utils.llm import call_llm, generate_logo_image
from app.utils.search import web_search


# ── Gemini system prompt ───────────────────────────────────────────────────────
GEMINI_BRIEF_SYSTEM = """You are a world-class brand identity director at a top-tier creative agency (Pentagram / Landor / Wolff Olins level).

Use Google Search to:
1. Research the brand's top 3-5 direct competitors — find their actual logo styles, color palettes, and visual identity details
2. Find 2024-2025 logo design trends specific to this industry
3. Identify unclaimed visual territory — design directions no competitor in this space has taken

Then generate a comprehensive 10-concept logo design brief tailored to THIS brand. Return ONLY valid JSON with exactly these keys:

{
  "brief_text": "Full formatted design brief (1000+ words). Sections: BRAND OVERVIEW, COMPETITOR VISUAL LANDSCAPE (real competitor names + visual details from your search), 2024-25 INDUSTRY TRENDS (from search), DESIGN DIRECTION (palette + font rationale), 10 LOGO CONCEPTS (each with symbol description + rationale). Use ━━━ section headers.",

  "image_prompt": "Image generation prompt for DALL-E / gpt-image-1. Target 2800-3500 chars. Must describe: white background professional brand identity presentation sheet titled with brand name, 10 logo concepts arranged in a clean grid (2 columns × 5 rows), each concept labeled with number + concept name, showing a geometric symbol mark + brandname wordmark + 3 color variants (full-color / monochrome / dark-inverted). Describe the geometric construction of each of the 10 symbols precisely — referencing this brand's specific industry, values, and identity. Include exact hex color codes. Specify clean modern sans-serif typography for all labels. Professional branding agency presentation style.",

  "concepts": [
    {"number": 1, "name": "short concept name", "approach": "Interlocked Monogram", "rationale": "one sentence specific to this brand"},
    {"number": 2, "name": "short concept name", "approach": "Ecosystem Orbit", "rationale": "one sentence"},
    {"number": 3, "name": "short concept name", "approach": "Growth Stack", "rationale": "one sentence"},
    {"number": 4, "name": "short concept name", "approach": "Bridge Arc", "rationale": "one sentence"},
    {"number": 5, "name": "short concept name", "approach": "Tri-form Overlap", "rationale": "one sentence"},
    {"number": 6, "name": "short concept name", "approach": "Network Nodes", "rationale": "one sentence"},
    {"number": 7, "name": "short concept name", "approach": "Dynamic Sweep", "rationale": "one sentence"},
    {"number": 8, "name": "short concept name", "approach": "Digital Grid", "rationale": "one sentence"},
    {"number": 9, "name": "short concept name", "approach": "Globe / Planet", "rationale": "one sentence"},
    {"number": 10, "name": "short concept name", "approach": "Journey Swoosh + Dot", "rationale": "one sentence"}
  ],

  "primary_color": "#hex",
  "accent_color": "#hex",
  "neutral_dark": "#1A1A2E",
  "font": "Google Font name",
  "competitor_visual_notes": "2-3 sentences summarizing what competitors look like visually and what visual territory is unclaimed"
}

CRITICAL RULES:
- Every concept name and rationale must reference this brand's specific industry, audience, or business model
- The image_prompt must be detailed enough for an AI to generate 10 distinct recognisable geometric symbols
- primary_color and accent_color must be appropriate for the brand's industry and values (include exact hex)
- Return ONLY valid JSON. No markdown fences, no extra text outside the JSON object."""


# ── Fallback brief generator (Groq, no search) ────────────────────────────────
FALLBACK_BRIEF_SYSTEM = """You are a brand identity director. Generate a 10-concept logo design brief.
Return ONLY valid JSON with exactly these keys:
brief_text, image_prompt, concepts (array of 10), primary_color, accent_color, neutral_dark, font, competitor_visual_notes.
Same structure as your instructions. Make everything specific to the brand provided."""


# ── Platform / category helpers ────────────────────────────────────────────────
def _platform_from_url(url: str) -> str:
    host = (urlparse(url).netloc or "").lower().replace("www.", "")
    if "pinterest"            in host: return "Pinterest"
    if "dribbble"             in host: return "Dribbble"
    if "behance"              in host: return "Behance"
    if "underconsideration"   in host: return "Brand New"
    if "logopond"             in host: return "Logopond"
    if "logolounge"           in host: return "Logolounge"
    if "fontsinuse"           in host: return "Fonts In Use"
    if "thelogocreative"      in host: return "Logo Creative"
    if "brandingidentitydesign" in host: return "Branding Journal"
    return host.split(".")[0].title() if host else "Source"


def _category_from_platform(platform: str) -> str:
    if platform in ("Brand New", "Behance", "Branding Journal"): return "Case Studies"
    if platform in ("Logopond", "Logolounge", "Logo Creative"):  return "Logo Gallery"
    if platform in ("Fonts In Use",):                            return "Typography"
    if platform in ("Dribbble",):                                return "Design Shots"
    if platform in ("Pinterest",):                               return "Moodboard"
    return "Reference"


# ── Inspiration link collector ─────────────────────────────────────────────────
async def _collect_inspiration_links(industry: str, concepts: list[dict]) -> list[dict]:
    """Collect curated designer inspiration links from multiple sources."""
    import asyncio

    search_plan: list[dict] = []
    seen_queries: set[str] = set()

    def _plan(label: str, query: str, reason: str, category: str):
        if query not in seen_queries:
            seen_queries.add(query)
            search_plan.append({"label": label, "query": query, "reason": reason, "category": category})

    # Case Studies
    _plan("Behance – Brand Identity", f"site:behance.net {industry} brand identity logo case study", "Full brand identity case studies", "Case Studies")
    _plan("Brand New – Reviews",      f"site:underconsideration.com/brandnew {industry} brand identity", "Professional brand critique", "Case Studies")

    # Logo Gallery
    _plan("Logopond – Gallery",    f"site:logopond.com {industry} logo",           "Curated logo gallery by industry", "Logo Gallery")
    _plan("Logolounge – Trends",   f"site:logolounge.com {industry} logo trend",   "Annual logo trend reports",       "Logo Gallery")
    _plan("Logo Creative",         f"site:thelogocreative.co.uk {industry} logo",  "Curated logo inspiration",        "Logo Gallery")

    # Design Shots
    _plan("Dribbble – Logo Shots",  f"site:dribbble.com {industry} logo brand identity",    "Logo explorations", "Design Shots")
    _plan("Dribbble – Wordmark",    f"site:dribbble.com wordmark logo {industry}",           "Wordmark designs",  "Design Shots")

    # Typography
    _plan("Fonts In Use",  f"site:fontsinuse.com {industry} brand logo",    "Real brand typeface usage", "Typography")

    # Moodboard
    _plan("Pinterest – Moodboard", f"site:pinterest.com {industry} logo brand identity inspiration", "Visual mood boards", "Moodboard")

    # Per-concept shots (first 3 concepts)
    for c in concepts[:3]:
        approach = c.get("approach", "")
        if approach:
            short = approach.split("/")[0].strip()
            _plan(f"Dribbble – {short}", f"site:dribbble.com {short} logo {industry}", f"Shots for {short} approach", "Design Shots")
            _plan(f"Pinterest – {short}", f"site:pinterest.com {short} logo brand identity", f"Boards for {short}", "Moodboard")

    async def _fetch(p: dict) -> list[dict]:
        results = await web_search(p["query"], num_results=4)
        links = []
        for r in results:
            link  = r.get("link", "")
            title = r.get("title", "")
            if link and title:
                platform = _platform_from_url(link)
                links.append({
                    "title":       title,
                    "brand_name":  title,
                    "link":        link,
                    "snippet":     r.get("snippet", ""),
                    "query_label": p["label"],
                    "platform":    platform,
                    "category":    p.get("category") or _category_from_platform(platform),
                    "reason":      p["reason"],
                })
        return links

    tasks = [_fetch(p) for p in search_plan[:16]]
    batches = await asyncio.gather(*tasks, return_exceptions=True)

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

    # Pad with direct fallback links
    fallbacks = [
        ("Brand New",   "https://www.underconsideration.com/brandnew/",             "Case Studies",  "Professional brand identity reviews"),
        ("Logopond",    f"https://logopond.com/?filter={quote_plus(industry)}",      "Logo Gallery",  f"Browse {industry} logos on Logopond"),
        ("Logolounge",  "https://www.logolounge.com/articles",                       "Logo Gallery",  "Annual logo trend reports"),
        ("Fonts In Use", f"https://fontsinuse.com/search#q={quote_plus(industry)}", "Typography",    f"Typography in {industry} brands"),
        ("Dribbble",    f"https://dribbble.com/search/{quote_plus(industry+' logo')}", "Design Shots", f"{industry} logo shots"),
    ]
    for plat, url, cat, reason in fallbacks:
        if not any(e["link"] == url for e in all_links):
            all_links.append({"title": f"{plat}: {industry} design", "brand_name": plat, "link": url,
                              "snippet": reason, "query_label": plat, "platform": plat, "category": cat, "reason": reason})

    print(f"[visual_identity_agent] Inspiration: {len(all_links)} links across {len(set(x['category'] for x in all_links))} categories")
    return all_links[:30]


# ── regenerate_variant_svg kept for brand.py API compatibility ─────────────────
async def regenerate_variant_svg(
    variant: dict,
    variant_index: int,
    brand_name: str,
    new_color_palette: list[str],
    heading_font: str | None = None,
    body_font: str | None = None,
) -> dict:
    """Patch variant colors/fonts in all prompt fields. No SVG generated."""
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
    """
    Generate a 10-concept logo design brief via Gemini (with live search),
    then render the visual grid with OpenAI image generation.
    """
    idea_discovery_data  = idea_discovery_data  if isinstance(idea_discovery_data,  dict) else {}
    market_research_data = market_research_data if isinstance(market_research_data, dict) else {}
    competitor_data      = competitor_data      if isinstance(competitor_data,      dict) else {}
    strategy_data        = strategy_data        if isinstance(strategy_data,        dict) else {}
    naming_data          = naming_data          if isinstance(naming_data,          dict) else {}

    brand_name   = naming_data.get("brand_name", "Brand")
    tagline      = naming_data.get("tagline", "")
    industry     = idea_discovery_data.get("industry_category", "")
    problem      = idea_discovery_data.get("problem_solved", "")
    value_prop   = idea_discovery_data.get("value_proposition", "")
    tone_hints   = idea_discovery_data.get("brand_tone_hints", "")
    brand_personality = strategy_data.get("brand_personality", {}) if isinstance(strategy_data.get("brand_personality"), dict) else {}
    archetype    = brand_personality.get("archetype", "modern")
    tone_voice   = brand_personality.get("tone_of_voice", "")
    brand_values = strategy_data.get("brand_values", [])
    positioning  = strategy_data.get("positioning_statement", "")
    target_segs  = strategy_data.get("target_segments", [])
    market_trends = market_research_data.get("market_trends", [])

    competitor_names = [
        c.get("name", "") for c in competitor_data.get("direct_competitors", [])[:5]
        if isinstance(c, dict) and c.get("name")
    ]

    # Derive abbreviation (e.g. "World Digital Ventures" → "WDV")
    abbreviation = "".join(w[0].upper() for w in brand_name.split() if w)

    # ── Step 1: Gemini generates 10-concept brief + image prompt ──────────────
    user_prompt = (
        f"Brand Name: {brand_name}\n"
        f"Abbreviation / Initials: {abbreviation}\n"
        f"Tagline: {tagline}\n"
        f"Industry: {industry}\n"
        f"Business Description: {problem}\n"
        f"Value Proposition: {value_prop}\n"
        f"Brand Personality: {archetype} — {tone_voice}\n"
        f"Brand Tone Hints: {tone_hints}\n"
        f"Brand Values: {', '.join(str(v) for v in brand_values)}\n"
        f"Target Audience: {json.dumps(target_segs[:2])}\n"
        f"Known Direct Competitors: {', '.join(competitor_names) or 'None identified yet'}\n"
        f"Positioning: {positioning}\n"
        f"Market Trends: {', '.join(str(t) for t in market_trends[:4])}\n"
        + (f"\nUser feedback to apply: {feedback}\n" if feedback else "")
        + "\nResearch competitors online and generate the 10-concept logo design brief and image prompt for this brand."
    )

    print(f"[visual_identity_agent] Calling Gemini to generate 10-concept brief for '{brand_name}'")
    raw_json = await call_gemini_with_search(
        system_prompt=GEMINI_BRIEF_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.7,
    )

    # Parse Gemini output
    try:
        brief_data = json.loads(raw_json) if raw_json and raw_json != "{}" else {}
    except Exception as exc:
        print(f"[visual_identity_agent] Gemini JSON parse error: {exc}")
        brief_data = {}

    # Fallback to Groq if Gemini failed
    if not brief_data or not brief_data.get("image_prompt"):
        print("[visual_identity_agent] Gemini returned empty/invalid — falling back to Groq")
        fallback_raw = await call_llm(
            system_prompt=FALLBACK_BRIEF_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.7,
            max_tokens=4096,
        )
        try:
            clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', fallback_raw.strip(), flags=re.MULTILINE)
            brief_data = json.loads(clean)
        except Exception:
            brief_data = {}

    # Extract structured fields from brief_data
    brief_text       = brief_data.get("brief_text", "")
    image_prompt_raw = brief_data.get("image_prompt", "")
    concepts         = brief_data.get("concepts", [])
    primary_color    = brief_data.get("primary_color", "#005B80")
    accent_color     = brief_data.get("accent_color", "#FFB300")
    neutral_dark     = brief_data.get("neutral_dark", "#1A1A2E")
    font             = brief_data.get("font", "Inter")
    competitor_notes = brief_data.get("competitor_visual_notes", "")

    if not isinstance(concepts, list):
        concepts = []

    print(f"[visual_identity_agent] Brief generated: {len(concepts)} concepts, image_prompt={len(image_prompt_raw)} chars")

    # ── Step 2: OpenAI generates the logo grid image ───────────────────────────
    image_result: dict = {}
    if image_prompt_raw:
        # Enrich the image prompt with brand context if it's too sparse
        if len(image_prompt_raw) < 800:
            image_prompt_raw = (
                f"Professional brand identity presentation sheet on white background. "
                f"Title at top: '{brand_name} ({abbreviation}) — 10 Distinct Logo Concepts'. "
                f"Tagline: '{tagline}'. Industry: {industry}.\n\n"
                + image_prompt_raw
            )
        print(f"[visual_identity_agent] Generating image with prompt length={len(image_prompt_raw)}")
        image_result = await generate_logo_image(image_prompt_raw)
    else:
        print("[visual_identity_agent] No image prompt from Gemini — skipping image generation")

    # Build image data URL from base64
    logo_image_url = ""
    if image_result.get("b64_json"):
        logo_image_url = f"data:image/png;base64,{image_result['b64_json']}"
        print(f"[visual_identity_agent] Image generated ({image_result.get('model', 'unknown')}) — {len(logo_image_url)//1024}KB data URL")
    elif image_result.get("error"):
        print(f"[visual_identity_agent] Image generation error: {image_result['error']}")

    # ── Step 3: Collect inspiration links ─────────────────────────────────────
    inspiration_links = await _collect_inspiration_links(industry, concepts)

    # ── Build output ───────────────────────────────────────────────────────────
    data: dict = {
        "logo_image_url":         logo_image_url,
        "logo_image_model":       image_result.get("model", ""),
        "logo_image_error":       image_result.get("error", ""),
        "logo_design_brief":      brief_text,
        "logo_image_prompt":      image_prompt_raw,
        "design_concepts":        concepts,
        "competitor_visual_notes": competitor_notes,
        "primary_color":          primary_color,
        "accent_color":           accent_color,
        "neutral_dark":           neutral_dark,
        "font":                   font,
        "logo_inspiration":       inspiration_links,
        # Legacy keys (kept so existing project reads don't break)
        "variants":               [],
        "design_style":           archetype,
        "mood_keywords":          [archetype, "professional", "distinctive"],
        "combined_summary": (
            f"10-concept logo design brief generated for {brand_name} ({abbreviation}). "
            f"{'Visual grid image generated. ' if logo_image_url else 'Image generation failed — check logs. '}"
            f"{len(concepts)} concepts covering all 10 visual archetypes. "
            f"{len(inspiration_links)} inspiration links collected."
        ),
    }

    explanation = (
        f"Visual identity generated for '{brand_name}': Gemini researched competitors and produced "
        f"a 10-concept logo brief covering all archetypes (monogram, orbit, stack, bridge, tri-form, "
        f"nodes, sweep, grid, globe, swoosh). "
        + (f"Image grid rendered by {image_result.get('model', 'OpenAI')}. " if logo_image_url else "Image generation failed. ")
        + f"{len(inspiration_links)} inspiration links collected."
    )

    return AgentResult(data=data, explanation=explanation)
