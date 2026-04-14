"""
Agent 6 – Visual Identity Intelligence Agent
Uses GPT-4o mini to generate rich logo creation prompts (wordmark + logomark)
for each color palette variant. No SVG generation — prompts are ready for
Ideogram, Midjourney, DALL-E, or a human designer.
"""
import json
import os
import re
from urllib.parse import quote_plus, urlparse

from app.schemas.brand_schema import AgentResult
from app.utils.llm import call_openai
from app.utils.search import web_search


# ── Google Font helpers ────────────────────────────────────────────────────────
FREE_FONT_PAIRS = {
    "minimal":  {"heading": "Inter",            "body": "Manrope",        "reason": "Clean, modern, highly readable."},
    "modern":   {"heading": "Manrope",           "body": "Inter",          "reason": "Neutral and flexible for contemporary brands."},
    "premium":  {"heading": "Playfair Display",  "body": "Inter",          "reason": "Elegant editorial feel with modern readability."},
    "bold":     {"heading": "Montserrat",        "body": "DM Sans",        "reason": "Strong, geometric, attention-grabbing."},
    "creative": {"heading": "Poppins",           "body": "Nunito",         "reason": "Friendly, expressive, versatile."},
    "tech":     {"heading": "Space Grotesk",     "body": "Inter",          "reason": "Sharp, futuristic, product-focused."},
    "finance":  {"heading": "Libre Baskerville", "body": "Source Serif 4", "reason": "Trustworthy, authoritative, traditional finance credibility."},
}


def _pick_font_family(style_text: str) -> dict:
    s = style_text.lower()
    if any(t in s for t in ["luxury", "premium", "elegant", "editorial", "fashion"]):
        return FREE_FONT_PAIRS["premium"]
    if any(t in s for t in ["finance", "banking", "nbfc", "lending", "trust", "integrity"]):
        return FREE_FONT_PAIRS["finance"]
    if any(t in s for t in ["tech", "ai", "software", "saas", "product", "digital"]):
        return FREE_FONT_PAIRS["tech"]
    if any(t in s for t in ["bold", "dynamic", "vibrant", "sport", "startup"]):
        return FREE_FONT_PAIRS["bold"]
    if any(t in s for t in ["creative", "playful", "art", "organic", "handmade"]):
        return FREE_FONT_PAIRS["creative"]
    if any(t in s for t in ["minimal", "clean", "simple", "sleek"]):
        return FREE_FONT_PAIRS["minimal"]
    return FREE_FONT_PAIRS["modern"]


def _font_css_url(font_name: str) -> str:
    family = quote_plus(font_name).replace("%20", "+")
    return f"https://fonts.googleapis.com/css2?family={family}:wght@400;500;600;700;800&display=swap"



# ── Variant generation prompt ──────────────────────────────────────────────────
VARIANTS_SYSTEM_PROMPT = """You are the lead brand identity designer at a world-class agency. A client has come to you for logo design. You have been given a complete 5-pillar brand brief (Core Identity, Competitive Landscape, Visual Landmarks, Target Audience, Constraints) plus live web research on competitor logos and current industry design trends.

Your job: generate 4 logo identity variants. For each, produce Ideogram AI prompts that are specific enough to generate a professional, industry-worthy logo on the first attempt.

━━━ PILLAR REFERENCE ━━━
Pillar 1 – Core Identity: brand mission, personality adjectives, tone (authoritative/playful/bold etc.)
Pillar 2 – Competitive Landscape: named competitors, how we're different/better
Pillar 3 – Visual Landmarks: relevant symbols, typography preference (serif=traditional, sans=modern)
Pillar 4 – Target Audience: demographics, psychographics (speed/safety/status/community)
Pillar 5 – Constraints: color psychology, primary usage context (app icon / signage / digital)

━━━ IDEOGRAM PROMPT QUALITY STANDARD ━━━
Every ideogram_prompt must read like a professional design brief sentence, not a tag list. It must name:
• The exact brand name (wordmark) or icon geometry (logomark)
• Font weight and style classification (wordmark) OR shape construction method (logomark)
• Exact hex color from the palette
• A real named design style, movement, or trend reference (e.g. Swiss International Style, Bauhaus geometry, New Wave typography, Silicon Valley minimal, Japanese reductivism, 2024 fintech flat icon language)
• The emotional tone this communicates to the audience
• Technical rendering specs at the end

BAD PROMPT (do not write this): "Modern logo, blue color, clean design, professional"
GOOD PROMPT: "'Capitexa' wordmark in bold low-contrast geometric sans-serif with tight optical tracking, rendered in deep cobalt #1A3A6B on white, letterforms follow Swiss modernist grid discipline evoking Bloomberg-level financial authority, sharp terminals, high x-height for digital legibility, contrasting the heavy serif tradition of legacy NBFCs, flat vector, white background, text only, no icon, no gradients, high resolution"

━━━ JSON OUTPUT (exactly 4 variants) ━━━
{
  "variants": [
    {
      "variant_name": "2-3 word evocative direction name",

      "visual_strategy": "2 sentences: the emotion this triggers in the target audience, the market position it claims, which competitor(s) it visually outflanks and how.",

      "logo_motivation": "Name the specific industry design trend this captures from the research + the specific competitor visual weakness it exploits.",

      "brand_emotion": {
        "primary_emotion": "One word — the feeling this logo must produce in the viewer",
        "emotional_language": "The visual mechanism e.g. 'horizontal weight signals stability', 'ascending diagonal implies growth'",
        "voice_translation": "How the brand personality (adjectives) maps to visual decisions — stroke weight, spacing, form geometry",
        "audience_resonance": "Why this emotional direction specifically connects with this audience's psychology and pain points"
      },

      "competitive_positioning": {
        "differentiates_from": "Named competitor(s) from the research",
        "how_different": "Specific visual contrast — colors, form language, weight, style vs those competitors",
        "trend_captured": "Named design or market trend from the web research this variant owns",
        "white_space_claimed": "Visual territory no current competitor occupies",
        "industry_standard_used": "Convention followed for instant category recognition",
        "industry_standard_broken": "Specific cliché of this industry deliberately subverted"
      },

      "color_palette": ["#hex1", "#hex2", "#hex3", "#hex4", "#hex5"],
      "color_roles": {
        "primary":       "#hex1 — color name, psychological effect, contrast with competitor colors",
        "secondary":     "#hex2 — supporting role, tonal relationship to primary",
        "accent":        "#hex3 — energy, CTA, contrast moments",
        "light_neutral": "#hex4 — backgrounds, breathing room",
        "dark_neutral":  "#hex5 — text, depth, grounding"
      },

      "heading_font": "Exact Google Font name",
      "body_font": "Exact Google Font name",
      "font_pairing_rationale": "Personality of heading font + why it matches brand tone + how it differs from competitor typography in this industry.",

      "wordmark_prompt": {
        "concept": "Design director brief: typeface classification, weight, custom letterform touches (modified terminals, ligatures, crossbars), tracking philosophy, brand value each decision reinforces, competitor aesthetic deliberately avoided.",
        "ideogram_prompt": "Write ONE flowing paragraph of 55-80 words. Structure: open with brand name in single quotes + typeface description (weight + classification + key letterform detail) + exact primary hex color + a named design movement or style reference specific to this industry + the emotional tone this communicates to the target audience + close with technical specs: flat vector, white background, text only, no icon, no gradients, no drop shadows, high resolution.",
        "designer_brief": "Exact typeface or nearest equivalent, tracking in ems, hex + RGB color values, custom letterform modifications to commission, 3 visual clichés of this industry to explicitly avoid, the single first impression it must deliver."
      },

      "logomark_prompt": {
        "concept": "Design director brief: what the mark represents literally and symbolically, geometric construction logic, negative space strategy, brand value the form embodies, how it contrasts with competitor iconography from the research.",
        "ideogram_prompt": "Write ONE flowing paragraph of 55-80 words. Structure: open with precise icon geometry (shape + construction method + proportions) + exact primary hex color + a named design trend or style reference specific to this industry + the emotional quality of the form + close with technical specs: flat vector, transparent background, no text, scalable, no gradients, no drop shadows, professional.",
        "designer_brief": "Grid dimensions and anchor points, proportion ratios, scalability at 16px favicon and 512px, negative space rules, single-color version guidance, 3 icon symbols overused in this industry to avoid."
      }
    }
  ]
}

━━━ RULES ━━━
- Exactly 4 variants with distinct directions (e.g. authoritative-traditional, modern-minimal, bold-disruptive, warm-approachable).
- Every ideogram_prompt is a single flowing prose paragraph — never a comma-separated tag list.
- Every ideogram_prompt names a real design style, movement, or trend reference for this specific industry.
- Every ideogram_prompt contains the exact hex from color_palette.
- Wordmark prompts open with the brand name in single quotes.
- Every variant names specific competitors from the provided research.
- All fonts are real Google Fonts currently available.
- Return ONLY valid JSON. No markdown fences, no extra text."""


async def _search_visual_references(
    brand_name: str,
    industry: str,
    competitors: list[str],
    archetype: str,
    target_audience: str,
) -> dict:
    """
    Search the web for:
    1. Competitor logo / brand identity descriptions
    2. Current industry logo design trends
    3. Visual inspiration for this brand archetype
    Returns a dict with keys: competitor_visuals, industry_trends, inspiration_notes
    """
    import asyncio

    queries = []

    # Competitor logo research
    for comp in competitors[:3]:
        if comp:
            queries.append(("competitor", comp, f"{comp} brand identity logo design style visual"))

    # Industry design trends
    queries.append(("trend", "industry", f"{industry} logo design trends 2024 2025 brand identity"))
    queries.append(("trend", "inspiration", f"{archetype} brand logo design inspiration {industry}"))
    queries.append(("trend", "audience", f"{industry} brand design {target_audience} visual identity"))

    async def _fetch(label, key, query):
        results = await web_search(query, num_results=4)
        snippets = [
            f"[{r.get('title','')}] {r.get('snippet','')}"
            for r in results if r.get("snippet")
        ]
        return label, key, snippets

    tasks = [_fetch(label, key, q) for label, key, q in queries]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    competitor_visuals: list[str] = []
    trend_notes: list[str] = []

    for item in raw_results:
        if isinstance(item, Exception):
            continue
        label, key, snippets = item
        if label == "competitor":
            competitor_visuals.append(f"--- {key} ---\n" + "\n".join(snippets[:3]))
        else:
            trend_notes.extend(snippets[:2])

    print(f"[visual_identity_agent] Web research: {len(competitor_visuals)} competitor profiles, {len(trend_notes)} trend snippets")

    return {
        "competitor_visuals": competitor_visuals,
        "trend_notes": trend_notes[:8],
    }


def _platform_from_url(url: str) -> str:
    host = (urlparse(url).netloc or "").lower().replace("www.", "")
    if "pinterest"         in host: return "Pinterest"
    if "dribbble"          in host: return "Dribbble"
    if "behance"           in host: return "Behance"
    if "underconsideration" in host: return "Brand New"
    if "logopond"          in host: return "Logopond"
    if "logolounge"        in host: return "Logolounge"
    if "fontsinuse"        in host: return "Fonts In Use"
    if "thelogocreative"   in host: return "Logo Creative"
    if "brandingidentitydesign" in host: return "Branding Journal"
    return host.split(".")[0].title() if host else "Source"


def _category_from_platform(platform: str) -> str:
    if platform in ("Brand New", "Behance", "Branding Journal"):  return "Case Studies"
    if platform in ("Logopond", "Logolounge", "Logo Creative"):    return "Logo Gallery"
    if platform in ("Fonts In Use",):                              return "Typography"
    if platform in ("Dribbble",):                                  return "Design Shots"
    if platform in ("Pinterest",):                                 return "Moodboard"
    return "Reference"


async def _collect_inspiration_links(
    variants: list[dict],
    brand_name: str,  # noqa: ARG001 – kept for call-site compatibility
    archetype: str,
    industry: str,
) -> list[dict]:
    """Collect curated designer inspiration links from multiple sources, organised by category."""
    import asyncio

    search_plan: list[dict] = []
    seen_queries: set[str] = set()

    def _plan(label: str, query: str, reason: str, category: str):
        if query not in seen_queries:
            seen_queries.add(query)
            search_plan.append({"label": label, "query": query, "reason": reason, "category": category})

    # ── Moodboard (Pinterest) ──────────────────────────────────────────────
    _plan("Pinterest – Archetype Board",
          f"site:pinterest.com {archetype} brand identity logo color palette",
          "Archetype-aligned visual boards", "Moodboard")
    _plan(f"Pinterest – {industry} logos",
          f"site:pinterest.com {industry} logo design brand identity inspiration",
          f"Logo mood boards for {industry}", "Moodboard")
    for v in variants[:2]:
        style = " ".join(v.get("variant_name", "").split()[:2])
        if style:
            _plan(f"Pinterest – {style}",
                  f"site:pinterest.com {style} logo brand design {industry}",
                  f"Mood board for '{style}' direction", "Moodboard")

    # ── Design Shots (Dribbble) ────────────────────────────────────────────
    _plan("Dribbble – Logo Exploration",
          f"site:dribbble.com {industry} logo brand identity",
          "Professional logo shots & explorations", "Design Shots")
    _plan("Dribbble – Wordmark Design",
          f"site:dribbble.com wordmark logo {industry} typography",
          "Wordmark design explorations", "Design Shots")

    # ── Case Studies (Behance + Brand New) ────────────────────────────────
    _plan("Behance – Brand Identity",
          f"site:behance.net {industry} brand identity logo case study",
          "Full brand identity project case studies", "Case Studies")
    _plan("Brand New – Identity Reviews",
          f"site:underconsideration.com/brandnew {industry} brand identity logo",
          "Professional brand identity critique & analysis", "Case Studies")

    # ── Logo Gallery (Logopond + Logolounge) ──────────────────────────────
    _plan("Logopond – Logo Gallery",
          f"site:logopond.com {industry} logo",
          "Curated logo gallery filtered by industry", "Logo Gallery")
    _plan("Logolounge – Trends",
          f"site:logolounge.com {industry} logo trend brand mark",
          "Annual logo trend reports for this industry", "Logo Gallery")
    _plan("Logo Creative – Inspiration",
          f"site:thelogocreative.co.uk {industry} logo design inspiration",
          "Curated logo inspiration by industry", "Logo Gallery")

    # ── Typography (Fonts In Use) ──────────────────────────────────────────
    for v in variants[:2]:
        hfont = v.get("heading_font", "")
        if hfont:
            _plan(f"Fonts In Use – {hfont}",
                  f"site:fontsinuse.com {hfont} brand logo identity",
                  f"Real-world brand usage of {hfont}", "Typography")
    _plan("Fonts In Use – Industry Type",
          f"site:fontsinuse.com {industry} wordmark brand logo",
          f"Typography used in {industry} brand identities", "Typography")

    # ── Per-variant designer inspiration ──────────────────────────────────
    for v in variants[:4]:
        vname = v.get("variant_name", "")
        style = " ".join(vname.split()[:2])
        emotion = v.get("brand_emotion", {}).get("primary_emotion", "")
        if style:
            _plan(f"Dribbble – {vname}",
                  f"site:dribbble.com {style} {emotion} {industry} brand logo",
                  f"Design shots for '{vname}' direction", "Design Shots")
            _plan(f"Pinterest – {vname}",
                  f"site:pinterest.com {style} {industry} brand identity logo inspiration",
                  f"Moodboard for '{vname}'", "Moodboard")

    # ── Run all searches in parallel ──────────────────────────────────────
    async def _fetch(plan_item: dict) -> list[dict]:
        results = await web_search(plan_item["query"], num_results=4)
        links = []
        for r in results:
            link  = r.get("link", "")
            title = r.get("title", "")
            if link and title:
                platform = _platform_from_url(link)
                links.append({
                    "title":        title,
                    "brand_name":   title,
                    "link":         link,
                    "snippet":      r.get("snippet", ""),
                    "query":        plan_item["query"],
                    "query_label":  plan_item["label"],
                    "platform":     platform,
                    "category":     plan_item.get("category") or _category_from_platform(platform),
                    "reason":       plan_item["reason"],
                })
        return links

    tasks = [_fetch(p) for p in search_plan[:18]]
    batches = await asyncio.gather(*tasks, return_exceptions=True)

    # Deduplicate
    seen_links: set[str] = set()
    all_links: list[dict] = []
    for batch in batches:
        if isinstance(batch, Exception):
            continue
        for item in batch:
            if item["link"] not in seen_links:
                seen_links.add(item["link"])
                all_links.append(item)

    # Sort: Case Studies > Logo Gallery > Design Shots > Typography > Moodboard
    order = {"Case Studies": 0, "Logo Gallery": 1, "Design Shots": 2, "Typography": 3, "Moodboard": 4, "Reference": 5}
    all_links.sort(key=lambda x: order.get(x.get("category", "Reference"), 5))

    # Pad with direct search fallback links if sparse
    fallback_searches = [
        ("Logopond",  f"https://logopond.com/?filter={quote_plus(industry)}",
         "Logo Gallery", f"Browse {industry} logos on Logopond"),
        ("Logolounge", f"https://www.logolounge.com/articles",
         "Logo Gallery", "Annual logo trend reports"),
        ("Brand New",  "https://www.underconsideration.com/brandnew/",
         "Case Studies", "Professional brand identity reviews"),
        ("Fonts In Use", f"https://fontsinuse.com/search#q={quote_plus(industry)}",
         "Typography", f"Typography used in {industry} brands"),
        ("Dribbble",   f"https://dribbble.com/search/{quote_plus(industry + ' logo')}",
         "Design Shots", f"{industry} logo shots on Dribbble"),
    ]
    for plat, url, cat, reason in fallback_searches:
        if not any(e["link"] == url for e in all_links):
            all_links.append({
                "title": f"{plat}: {industry} design", "brand_name": plat,
                "link": url, "snippet": reason,
                "query": "", "query_label": plat, "platform": plat,
                "category": cat, "reason": reason,
            })

    print(f"[visual_identity_agent] Inspiration links: {len(all_links)} across {len(set(x['category'] for x in all_links))} categories")
    return all_links[:30]


# ── regenerate_variant_svg kept for API compatibility (now just re-prompts) ───
async def regenerate_variant_svg(
    variant: dict,
    variant_index: int,   # noqa: ARG001 – kept for call-site compatibility
    brand_name: str,      # noqa: ARG001 – kept for call-site compatibility
    new_color_palette: list[str],
    heading_font: str | None = None,
    body_font: str | None = None,
) -> dict:
    """Update variant colors/fonts and patch all prompts. No SVG generated."""
    updated = dict(variant)
    old_palette = list(variant.get("color_palette", []))
    updated["color_palette"] = new_color_palette

    if heading_font:
        updated["heading_font"] = heading_font
    if body_font:
        updated["body_font"] = body_font

    # Patch hex codes in all prompt fields
    prompt_fields = [
        "wordmark_prompt.ideogram_prompt",
        "wordmark_prompt.designer_brief", "wordmark_prompt.concept",
        "logomark_prompt.ideogram_prompt",
        "logomark_prompt.designer_brief", "logomark_prompt.concept",
        "ideogram_prompt",  # legacy field
    ]
    for field_path in prompt_fields:
        parts = field_path.split(".")
        if len(parts) == 1:
            text = updated.get(parts[0], "")
            for old_hex, new_hex in zip(old_palette, new_color_palette):
                text = text.replace(old_hex, new_hex)
            if heading_font and variant.get("heading_font"):
                text = text.replace(variant["heading_font"], heading_font)
            if body_font and variant.get("body_font"):
                text = text.replace(variant["body_font"], body_font)
            updated[parts[0]] = text
        elif len(parts) == 2:
            parent = updated.get(parts[0])
            if isinstance(parent, dict):
                text = parent.get(parts[1], "")
                for old_hex, new_hex in zip(old_palette, new_color_palette):
                    text = text.replace(old_hex, new_hex)
                if heading_font and variant.get("heading_font"):
                    text = text.replace(variant.get("heading_font", ""), heading_font)
                if body_font and variant.get("body_font"):
                    text = text.replace(variant.get("body_font", ""), body_font)
                parent[parts[1]] = text

    # Patch color_roles
    roles = dict(variant.get("color_roles", {}))
    for key, desc in roles.items():
        for old_hex, new_hex in zip(old_palette, new_color_palette):
            desc = desc.replace(old_hex, new_hex)
        roles[key] = desc
    updated["color_roles"] = roles

    # No SVG to regenerate — clear stale SVG fields
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
    """Generate 4 brand identity variants with rich logo prompts (wordmark + logomark)."""
    idea_discovery_data  = idea_discovery_data  if isinstance(idea_discovery_data,  dict) else {}
    market_research_data = market_research_data if isinstance(market_research_data, dict) else {}
    competitor_data      = competitor_data      if isinstance(competitor_data,      dict) else {}
    strategy_data        = strategy_data        if isinstance(strategy_data,        dict) else {}
    naming_data          = naming_data          if isinstance(naming_data,          dict) else {}

    brand_name = naming_data.get("brand_name", "Brand")
    tagline    = naming_data.get("tagline", "")
    brand_personality = strategy_data.get("brand_personality", {}) if isinstance(strategy_data.get("brand_personality"), dict) else {}
    archetype  = brand_personality.get("archetype", "modern")
    industry   = idea_discovery_data.get("industry_category", "")

    # ── Build rich brand brief for GPT ────────────────────────────────────
    brand_brief = {
        "brand_name":              brand_name,
        "tagline":                 tagline,
        "industry":                industry,
        "business_model":          idea_discovery_data.get("business_model", ""),
        "problem_solved":          idea_discovery_data.get("problem_solved", ""),
        "value_proposition":       idea_discovery_data.get("value_proposition", ""),
        "brand_tone_hints":        idea_discovery_data.get("brand_tone_hints", ""),
        "brand_archetype":         archetype,
        "tone_of_voice":           brand_personality.get("tone_of_voice", ""),
        "brand_values":            strategy_data.get("brand_values", []),
        "positioning_statement":   strategy_data.get("positioning_statement", ""),
        "unique_selling_proposition": strategy_data.get("unique_selling_proposition", ""),
        "emotional_benefits":      strategy_data.get("emotional_benefits", []),
        "target_segments":         strategy_data.get("target_segments", []),
        "market_gaps":             market_research_data.get("market_gaps", []),
        "market_trends":           market_research_data.get("market_trends", []),
    }

    competitor_design_profiles = [
        {"name": c.get("name", ""), "design_trends": c.get("design_trends", {})}
        for c in competitor_data.get("direct_competitors", [])[:4]
        if isinstance(c, dict) and c.get("design_trends")
    ]
    industry_design_trends = competitor_data.get("industry_design_trends", {})
    competitor_names = [
        c.get("name", "") for c in competitor_data.get("direct_competitors", [])[:3]
        if isinstance(c, dict) and c.get("name")
    ]
    target_audience_str = str(brand_brief.get("target_segments", ["general audience"])[:1])

    # ── Live web research: competitor logos + industry trends ─────────────
    web_refs = await _search_visual_references(
        brand_name=brand_name,
        industry=industry,
        competitors=competitor_names,
        archetype=archetype,
        target_audience=target_audience_str,
    )

    # Flatten industry design trends
    trend_lines = []
    if industry_design_trends:
        if industry_design_trends.get("dominant_styles"):
            trend_lines.append("Dominant visual styles: " + ", ".join(industry_design_trends["dominant_styles"]))
        if industry_design_trends.get("color_trends"):
            trend_lines.append("Color trends: " + industry_design_trends["color_trends"])
        if industry_design_trends.get("typography_trends"):
            trend_lines.append("Typography trends: " + industry_design_trends["typography_trends"])
        if industry_design_trends.get("design_white_space"):
            trend_lines.append("Unclaimed visual space: " + industry_design_trends["design_white_space"])
    market_trend_lines = market_research_data.get("market_trends", [])

    user_prompt = (
        f"━━━ PILLAR 1 — CORE IDENTITY ━━━\n"
        f"Brand: {brand_name} | Industry: {industry} | Archetype: {archetype}\n"
        f"Mission: {brand_brief.get('problem_solved', '')}\n"
        f"Value Proposition: {brand_brief.get('value_proposition', '')}\n"
        f"Tone: {brand_brief.get('tone_of_voice', '')} | Personality hints: {brand_brief.get('brand_tone_hints', '')}\n"
        f"Brand Values: {', '.join(str(v) for v in brand_brief.get('brand_values', []))}\n\n"

        f"━━━ PILLAR 2 — COMPETITIVE LANDSCAPE ━━━\n"
        f"Direct competitors: {', '.join(competitor_names) or 'None identified'}\n"
        f"Positioning: {brand_brief.get('positioning_statement', '')}\n"
        f"USP vs competitors: {brand_brief.get('unique_selling_proposition', '')}\n"
        + (
            "Competitor visual profiles (from brand research):\n"
            + json.dumps(competitor_design_profiles, indent=2) + "\n"
            if competitor_design_profiles else ""
        )
        + (
            "\nCompetitor logo research (live web search results):\n"
            + "\n\n".join(web_refs["competitor_visuals"])
            + "\n"
            if web_refs["competitor_visuals"] else ""
        )
        + "\n"

        f"━━━ PILLAR 3 — VISUAL LANDMARKS ━━━\n"
        + (
            "Industry design trends (from competitor analysis):\n"
            + "\n".join(f"• {t}" for t in trend_lines)
            + "\n"
            if trend_lines else ""
        )
        + (
            "Market trends to embed in prompts:\n"
            + "\n".join(f"• {t}" for t in market_trend_lines[:5])
            + "\n"
            if market_trend_lines else ""
        )
        + (
            "Live web research — industry design trends & inspiration:\n"
            + "\n".join(f"• {s}" for s in web_refs["trend_notes"])
            + "\n"
            if web_refs["trend_notes"] else ""
        )
        + "\n"

        f"━━━ PILLAR 4 — TARGET AUDIENCE ━━━\n"
        f"Segments: {json.dumps(brand_brief.get('target_segments', []))}\n"
        f"Emotional benefits they seek: {json.dumps(brand_brief.get('emotional_benefits', []))}\n\n"

        f"━━━ PILLAR 5 — CONSTRAINTS ━━━\n"
        f"Brand name to use in all wordmark prompts: '{brand_name}'\n"
        f"Tagline: {brand_brief.get('tagline', '')}\n"
        + (f"User feedback to apply: {feedback}\n" if feedback else "")
        + "\n\nUsing all 5 pillars and the web research above, generate exactly 4 brand identity variants. "
        "Every Ideogram prompt must be a rich flowing paragraph that references the actual design trends and competitor visual styles found in the research."
    )

    # ── Call GPT-4o mini ───────────────────────────────────────────────────
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not openai_key:
        print("[visual_identity_agent] ERROR: OPENAI_API_KEY not set in .env — cannot generate variants")

    raw = await call_openai(
        system_prompt=VARIANTS_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.8,
        max_tokens=8000,
    )

    try:
        clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw.strip(), flags=re.MULTILINE)
        parsed = json.loads(clean)
        variants = parsed.get("variants", [])
        if not variants:
            print(f"[visual_identity_agent] WARNING: parsed OK but variants list is empty. raw[:300]: {raw[:300]}")
    except Exception as exc:
        print(f"[visual_identity_agent] JSON parse failed: {exc} | raw[:300]: {raw[:300]}")
        variants = []

    if not isinstance(variants, list):
        variants = []

    print(f"[visual_identity_agent] Generated {len(variants)} variants for '{brand_name}'")

    # ── Collect inspiration links ──────────────────────────────────────────
    inspiration_links = await _collect_inspiration_links(variants, brand_name, archetype, industry)

    # ── Build output ───────────────────────────────────────────────────────
    first_variant = variants[0] if variants else {}
    first_colors  = first_variant.get("color_palette", ["#000000", "#ffffff", "#cccccc", "#333333", "#f5f5f5"])
    style_text    = f"{archetype} {industry} {first_variant.get('variant_name', '')}"
    font_bundle   = _pick_font_family(style_text)

    data: dict = {
        "design_style":    first_variant.get("variant_name", "modern"),
        "mood_keywords":   [archetype, "professional", "distinctive"],
        "design_trends":   market_research_data.get("market_trends", [])[:4],
        "imagery_style":   f"Visual identity built around {archetype} archetype.",
        "logo_direction": {
            "summary":         first_variant.get("wordmark_prompt", {}).get("concept", f"A {archetype} logo for {brand_name}."),
            "best_logo_types": list({v.get("variant_name", "") for v in variants[:5]}),
            "style_words":     [archetype, "distinctive", "professional"],
            "avoid_words":     ["generic", "clip-art", "overused gradients"],
            "why_it_fits":     first_variant.get("visual_strategy", ""),
        },
        "color_palette": {
            "primary":       {"hex": first_colors[0] if len(first_colors) > 0 else "#000000", "name": "Primary",      "usage": "Main brand color"},
            "secondary":     {"hex": first_colors[1] if len(first_colors) > 1 else "#ffffff", "name": "Secondary",    "usage": "Supporting elements"},
            "accent":        {"hex": first_colors[2] if len(first_colors) > 2 else "#cccccc", "name": "Accent",       "usage": "CTAs and highlights"},
            "neutral_dark":  {"hex": first_colors[3] if len(first_colors) > 3 else "#333333", "name": "Dark Neutral", "usage": "Primary text"},
            "neutral_light": {"hex": first_colors[4] if len(first_colors) > 4 else "#f5f5f5", "name": "Light Neutral","usage": "Backgrounds"},
        },
        "typography": {
            "heading_font":     first_variant.get("heading_font") or font_bundle["heading"],
            "body_font":        first_variant.get("body_font")    or font_bundle["body"],
            "font_provider":    "Google Fonts (free)",
            "font_reason":      first_variant.get("font_pairing_rationale") or font_bundle["reason"],
            "heading_font_url": _font_css_url(first_variant.get("heading_font") or font_bundle["heading"]),
            "body_font_url":    _font_css_url(first_variant.get("body_font")    or font_bundle["body"]),
        },
        "variants":         variants,
        "logo_inspiration": inspiration_links,
        "combined_summary": (
            f"{len(variants)} brand identity variants generated for {brand_name}. "
            f"Each has a wordmark prompt, logomark prompt, color palette, and typography. "
            f"{len(inspiration_links)} inspiration links collected."
        ),
    }

    explanation = (
        f"Visual identity generated for '{brand_name}': {len(variants)} variants, "
        f"each with a strategic wordmark prompt and logomark prompt ready for Ideogram, Midjourney, or a designer. "
        f"Prompts are grounded in brand strategy, market trends, and competitor design analysis. "
        f"{len(inspiration_links)} inspiration links collected."
    )

    return AgentResult(data=data, explanation=explanation)
