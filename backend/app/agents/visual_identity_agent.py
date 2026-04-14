"""
Agent 6 – Visual Identity Intelligence Agent
Uses GPT-4o mini to generate rich logo creation prompts (wordmark + logomark)
for each color palette variant. No SVG generation — prompts are ready for
Ideogram, Midjourney, DALL-E, or a human designer.
"""
import json
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


def _domain_label(url: str) -> str:
    host = (urlparse(url).netloc or "").lower().replace("www.", "")
    if "pinterest" in host: return "Pinterest"
    if "behance"   in host: return "Behance"
    if "dribbble"  in host: return "Dribbble"
    return host.split(".")[0].title() if host else "Source"


# ── Variant generation prompt ──────────────────────────────────────────────────
VARIANTS_SYSTEM_PROMPT = """You are a world-class brand identity designer and creative director.

Given a complete brand brief (strategy, market research, competitor analysis, market trends),
generate 6 distinct brand identity variants. For each variant you will:
1. Design a color palette (5 hex colors) grounded in brand strategy and market positioning
2. Write a professional WORDMARK logo prompt (text-based logo)
3. Write a professional LOGOMARK logo prompt (symbol/icon-based logo)
4. Select appropriate typography
5. Explain the strategic motivation for this visual direction

Each variant must be visually distinct — vary color mood, typography style, and logo concept significantly.

Return this exact JSON structure:
{
  "variants": [
    {
      "variant_name": "Short creative direction name (e.g. 'Authoritative Trust', 'Modern Agility')",
      "visual_strategy": "2-3 sentences explaining WHY this visual direction — what market positioning it claims, what competitor gap it fills, what emotion it triggers in the target audience",
      "logo_motivation": "What specific market trend, competitor weakness, or brand value inspired this logo direction",
      "color_palette": ["#hex1", "#hex2", "#hex3", "#hex4", "#hex5"],
      "color_roles": {
        "primary":       "#hex1 — role and strategic reasoning",
        "secondary":     "#hex2 — role and strategic reasoning",
        "accent":        "#hex3 — role and strategic reasoning",
        "light_neutral": "#hex4 — role and strategic reasoning",
        "dark_neutral":  "#hex5 — role and strategic reasoning"
      },
      "heading_font": "Google Font name",
      "body_font": "Google Font name",
      "font_pairing_rationale": "Why these fonts work for this brand and variant direction",
      "wordmark_prompt": {
        "concept": "Describe the wordmark concept — lettering style, custom touches, spacing, weight, any graphic element integrated into the type",
        "midjourney_prompt": "Full Midjourney/DALL-E prompt: '[Brand Name]' wordmark logo, [describe style, weight, letterform details, color hex codes], [mood adjectives], professional brand logo, vector, white background, high quality",
        "ideogram_prompt": "Full Ideogram prompt optimized for text rendering: '[Brand Name]' wordmark, [style], [colors as hex], [mood], logo design, vector, transparent background, professional, high quality",
        "designer_brief": "Instructions for a human designer: typeface classification, letter-spacing rules, color application, any custom letterform modifications"
      },
      "logomark_prompt": {
        "concept": "Describe the symbol/icon concept — what it represents, geometric or organic, abstract or literal, what brand value it embodies",
        "midjourney_prompt": "Full Midjourney/DALL-E prompt: abstract [shape] logo mark for [brand], [describe icon shape, negative space, geometric details], [color hex codes], minimal, professional, vector, white background",
        "ideogram_prompt": "Full Ideogram prompt: [describe icon], logo mark, [colors as hex], [style], symbol, transparent background, professional, high quality",
        "designer_brief": "Instructions for a human designer: geometry, proportions, what the icon communicates, scalability notes"
      }
    }
  ]
}

CRITICAL RULES:
- Generate EXACTLY 6 variants.
- Each variant must have a DIFFERENT visual strategy — vary from authoritative/traditional to modern/minimal to bold/energetic etc.
- Color palettes must be strategic, not random. Justify every color with brand logic.
- Wordmark and logomark prompts must be SPECIFIC and ACTIONABLE — a designer or AI tool should be able to execute them immediately.
- Use EXACT hex codes from color_palette in the prompts.
- At least 2 variants must deliberately contrast with competitor design trends (occupy visual white space).
- Fonts must be real Google Fonts.
- Return ONLY valid JSON. No markdown fences, no extra text."""


async def _collect_inspiration_links(
    variants: list[dict],
    brand_name: str,
    archetype: str,
    industry: str,
) -> list[dict]:
    """Build search queries from variants and collect inspiration links."""
    queries = []
    seen: set[str] = set()

    def _add(label: str, query: str, reason: str):
        if query not in seen:
            seen.add(query)
            queries.append({"label": label, "query": query, "reason": reason})

    for v in variants[:4]:
        vname = v.get("variant_name", "")
        style = " ".join(vname.split()[:2])
        _add(f"Pinterest – {vname}", f"site:pinterest.com {style} logo brand identity {industry}", f"Inspiration for '{vname}' direction")

    _add("Pinterest – Brand Board",    f"site:pinterest.com {archetype} brand identity logo color palette", "Archetype-aligned brand boards")
    _add("Dribbble – Logo Design",     f"site:dribbble.com {industry} logo brand identity design",          "Professional logo explorations")
    _add("Behance – Brand Identity",   f"site:behance.net {brand_name} brand identity logo case study",    "Full identity case studies")

    for v in variants[:3]:
        hfont = v.get("heading_font", "")
        if hfont:
            _add(f"Typography – {hfont}", f"site:pinterest.com {hfont} typography logo brand design", f"Logos using {hfont}")

    all_links: list[dict] = []
    for item in queries[:8]:
        results = await web_search(item["query"], num_results=5)
        for r in results:
            link = r.get("link", "")
            title = r.get("title", "")
            if link and title:
                all_links.append({
                    "title": title, "brand_name": title, "link": link,
                    "snippet": r.get("snippet", ""),
                    "query": item["query"],
                    "query_label": item["label"],
                    "platform": _domain_label(link),
                })

    # Deduplicate
    seen_links: set[str] = set()
    unique: list[dict] = []
    for item in all_links:
        if item["link"] not in seen_links:
            seen_links.add(item["link"])
            unique.append(item)

    # Pinterest-prioritize
    pinterest    = [i for i in unique if "pinterest" in i.get("platform", "").lower()]
    non_pinterest = [i for i in unique if "pinterest" not in i.get("platform", "").lower()]
    selected = (pinterest[:14] + non_pinterest)[:18]

    # Pad with direct Pinterest search URLs if under target
    for item in queries:
        if len(selected) >= 15:
            break
        url = f"https://www.pinterest.com/search/pins/?q={quote_plus(item['query'])}"
        if not any(e["link"] == url for e in selected):
            selected.append({
                "title": f"Pinterest: {item['label']}", "brand_name": item["label"],
                "link": url, "snippet": item["reason"],
                "query": item["query"], "query_label": item["label"], "platform": "Pinterest",
            })

    return selected[:18]


# ── regenerate_variant_svg kept for API compatibility (now just re-prompts) ───
async def regenerate_variant_svg(
    variant: dict,
    variant_index: int,
    brand_name: str,
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
        "wordmark_prompt.midjourney_prompt", "wordmark_prompt.ideogram_prompt",
        "wordmark_prompt.designer_brief", "wordmark_prompt.concept",
        "logomark_prompt.midjourney_prompt", "logomark_prompt.ideogram_prompt",
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
    """Generate 6 brand identity variants with rich logo prompts (wordmark + logomark)."""
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

    user_prompt = (
        f"BRAND BRIEF:\n{json.dumps(brand_brief, indent=2)}\n\n"
        + (
            f"COMPETITOR DESIGN PROFILES (avoid their visual clichés — find the white space):\n"
            f"{json.dumps(competitor_design_profiles, indent=2)}\n\n"
            if competitor_design_profiles else ""
        )
        + (
            f"INDUSTRY DESIGN TRENDS:\n{json.dumps(industry_design_trends, indent=2)}\n\n"
            if industry_design_trends else ""
        )
        + f"Brand Name to use in all prompts: {brand_name}\n"
        + (f"\nUser Feedback (apply to ALL variants): {feedback}\n" if feedback else "")
        + "\n\nGenerate 6 distinct brand identity variants with wordmark and logomark prompts for each."
    )

    # ── Call GPT-4o mini ───────────────────────────────────────────────────
    raw = await call_openai(
        system_prompt=VARIANTS_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.8,
        max_tokens=4096,
    )

    try:
        clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw.strip(), flags=re.MULTILINE)
        parsed = json.loads(clean)
        variants = parsed.get("variants", [])
    except Exception as exc:
        print(f"[visual_identity_agent] JSON parse failed: {exc} | raw[:200]: {raw[:200]}")
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
