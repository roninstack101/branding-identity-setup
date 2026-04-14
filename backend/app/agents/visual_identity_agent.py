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


def _domain_label(url: str) -> str:
    host = (urlparse(url).netloc or "").lower().replace("www.", "")
    if "pinterest" in host: return "Pinterest"
    if "behance"   in host: return "Behance"
    if "dribbble"  in host: return "Dribbble"
    return host.split(".")[0].title() if host else "Source"


# ── Variant generation prompt ──────────────────────────────────────────────────
VARIANTS_SYSTEM_PROMPT = """You are a world-class brand identity designer and competitive brand strategist.

Given a brand brief with strategy, tone, market research, competitor visual profiles, and industry design trends, generate exactly 4 brand identity variants.

IMPORTANT FOR LOGO PROMPTS:
The Ideogram prompts must be RICH and SPECIFIC. They must reference:
1. The actual design trends currently dominant in this industry (from the data provided)
2. The visual styles trending for similar brands right now — e.g. if fintech brands are trending toward "clean geometric sans with teal gradients", reference that and either adopt it or deliberately subvert it
3. The emotional language of the brand (authoritative, warm, bold, etc.)
4. Exact construction details — icon shape, letterform style, negative space, stroke weight
5. Exact hex colors from the palette
These prompts must be detailed enough that pasting them directly into Ideogram AI produces a on-brand, professional logo.

Return this exact JSON (4 items in variants array):
{
  "variants": [
    {
      "variant_name": "Short evocative name (e.g. 'Authoritative Trust')",
      "visual_strategy": "2 sentences: emotion triggered in audience, market positioning claimed, key competitor differentiation.",
      "logo_motivation": "Which market trend this captures AND which competitor visual weakness it exploits. Name both specifically.",
      "brand_emotion": {
        "primary_emotion": "Single core emotion (e.g. trusted, empowered, relieved)",
        "emotional_language": "How that emotion is expressed visually — weight, spacing, form, curvature",
        "voice_translation": "How the brand's tone of voice maps to specific visual decisions",
        "audience_resonance": "Why this resonates with the target audience's psychology and pain points"
      },
      "competitive_positioning": {
        "differentiates_from": "Specific competitor name(s) this contrasts with",
        "how_different": "Specific visual differences in color, style, weight, form vs those competitors",
        "trend_captured": "Exact market/design trend from the provided data this variant owns",
        "white_space_claimed": "Visual territory no competitor currently occupies",
        "industry_standard_used": "Industry visual convention followed to build instant trust",
        "industry_standard_broken": "Industry visual cliché deliberately broken to stand out"
      },
      "color_palette": ["#hex1", "#hex2", "#hex3", "#hex4", "#hex5"],
      "color_roles": {
        "primary": "#hex1 — emotional meaning, brand value reasoning, how it differs from competitors",
        "secondary": "#hex2 — supporting role and tonal relationship to primary",
        "accent": "#hex3 — CTA, energy, contrast use",
        "light_neutral": "#hex4 — background and breathing room",
        "dark_neutral": "#hex5 — body text and grounding"
      },
      "heading_font": "Exact Google Font name",
      "body_font": "Exact Google Font name",
      "font_pairing_rationale": "Why these fonts match the brand tone and differ from typical competitors in this industry.",
      "wordmark_prompt": {
        "concept": "Lettering style, weight (e.g. bold geometric / light elegant / condensed display), custom touches, spacing, competitor aesthetic deliberately avoided.",
        "ideogram_prompt": "DETAILED Ideogram prompt — include ALL of: exact brand name in quotes, font style and weight (e.g. bold condensed geometric sans-serif), letterform details (e.g. sharp angular terminals, high x-height, tight tracking), primary color hex [#XXXXXX] on white background, current design trend reference for this industry (e.g. 'in the style of modern fintech brands using clean geometric type'), emotional quality (e.g. authoritative and trustworthy), professional wordmark logo, vector, white background, text only, no icon, high resolution — write as a flowing descriptive sentence not a list",
        "designer_brief": "Typeface classification, tracking/letter-spacing values, color application rules, custom letterform modifications, industry clichés to avoid, desired emotional first impression."
      },
      "logomark_prompt": {
        "concept": "What the symbol represents literally and metaphorically, geometric or organic construction, negative space usage, brand value embodied, contrast with competitor icons in this industry.",
        "ideogram_prompt": "DETAILED Ideogram prompt — include ALL of: precise icon description (e.g. two overlapping circles forming a lens shape, or upward-pointing chevron with rounded corners), construction details (e.g. enclosed negative space, 2px stroke, balanced proportions), primary color hex [#XXXXXX], current design trend for this industry (e.g. 'trending minimal flat icon style used by leading brands in this space'), emotional quality (e.g. stable, forward-moving, warm), logo mark icon, transparent background, no text, scalable vector, professional, high quality — write as a flowing descriptive sentence",
        "designer_brief": "Precise geometric grid construction, scalability at 16px and 500px, negative space rules, single-color version guidance, visual symbols overused in this industry to avoid."
      }
    }
  ]
}

RULES:
- Generate EXACTLY 4 variants with distinct visual directions.
- Every ideogram_prompt must be a rich, detailed paragraph — NOT a short list. Minimum 50 words per prompt.
- Every ideogram_prompt must reference a current design trend for this industry (from the data provided).
- Every ideogram_prompt must include the exact brand name (wordmark) or icon description (logomark) and exact hex codes.
- Every variant must name specific competitors and explain visual differentiation.
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

    # Flatten industry design trends into readable text for the LLM
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
        f"BRAND BRIEF:\n{json.dumps(brand_brief, indent=2)}\n\n"
        + (
            f"COMPETITOR DESIGN PROFILES — reference these in your Ideogram prompts to show differentiation:\n"
            f"{json.dumps(competitor_design_profiles, indent=2)}\n\n"
            if competitor_design_profiles else ""
        )
        + (
            f"INDUSTRY DESIGN TRENDS — embed these directly into your Ideogram prompts:\n"
            + "\n".join(f"• {t}" for t in trend_lines)
            + "\n\n"
            if trend_lines else ""
        )
        + (
            f"MARKET TRENDS — reference these in logo_motivation and ideogram prompts:\n"
            + "\n".join(f"• {t}" for t in market_trend_lines[:5])
            + "\n\n"
            if market_trend_lines else ""
        )
        + f"Brand Name to use in all prompts: {brand_name}\n"
        + (f"\nUser Feedback (apply to ALL variants): {feedback}\n" if feedback else "")
        + "\n\nGenerate exactly 4 distinct brand identity variants. Make every Ideogram prompt rich, detailed, and reference the industry trends above."
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
