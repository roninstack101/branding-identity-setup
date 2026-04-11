"""
Agent 6 – Visual Identity Intelligence Agent
Generates 10 brand identity variants (colors, fonts, logo prompts, SVG logos, ideogram prompts)
plus Pinterest/Behance/Dribbble inspiration links.
SVG logos are generated concurrently via Groq (free tier) to keep costs zero.
"""
import asyncio
import base64
import json
import re
from urllib.parse import quote_plus, urlparse

from app.schemas.brand_schema import AgentResult
from app.utils.llm import call_llm
from app.utils.search import web_search


# ── Semaphore: max 5 concurrent Groq calls to stay within rate limits ─────────
_SVG_SEMAPHORE = asyncio.Semaphore(5)


# ── 10-variant brand identity prompt ──────────────────────────────────────────
VARIANTS_SYSTEM_PROMPT = """You are a senior brand designer. Given the business profile and market context, create 10 DIFFERENT brand identity variants as a JSON object. Each variant should have a distinct visual direction while staying true to the brand.

Return this exact JSON structure:
{
  "variants": [
    {
      "variant_name": "Short creative name for this direction (e.g. 'Bold & Modern', 'Elegant Classic')",
      "logo_type": "One of: wordmark, lettermark, icon_mark, combination_mark, emblem, abstract_mark, mascot",
      "logo_prompt": "A detailed description of the logo concept. MUST include: the logo_type, the brand name (for wordmark/lettermark/combination_mark), the EXACT hex color codes from this variant's color_palette, specific style/shapes/iconography.",
      "color_palette": ["#hex1", "#hex2", "#hex3", "#hex4", "#hex5"],
      "color_roles": {
        "primary": "#hex1 — [role and reasoning]",
        "secondary": "#hex2 — [role and reasoning]",
        "accent": "#hex3 — [role and reasoning]",
        "light_neutral": "#hex4 — [role and reasoning]",
        "dark_neutral": "#hex5 — [role and reasoning]"
      },
      "heading_font": "Google Font name for headings",
      "body_font": "Google Font name for body text",
      "font_pairing_rationale": "Why these fonts work together for this specific brand",
      "ideogram_prompt": "A detailed, Ideogram-optimized prompt for generating this logo using AI image generation. Must include: the exact brand name as text to render (in quotes), logo style and type, EXACT hex color codes, visual elements/shapes/iconography, mood and aesthetic keywords, and end with 'logo design, vector, transparent background, professional, high quality'."
    }
  ]
}

CRITICAL RULES:
- Generate EXACTLY 10 variants in the "variants" array.
- Each variant MUST have a different logo_type. Cover at least 5 different types across: wordmark, lettermark, icon_mark, combination_mark, emblem, abstract_mark, mascot.
- Each logo_prompt MUST explicitly reference the EXACT hex color codes from that variant's color_palette.
- For wordmark/lettermark/combination_mark logo types, the logo_prompt MUST include the brand name as text to render.
- Each variant must have a UNIQUE visual direction — vary the color mood, typography style, and logo concept significantly.
- Mix approaches: some bold/modern, some classic/elegant, some playful, some minimal, some luxurious.
- If Competitor Design Profiles are provided, at least 3 variants MUST occupy the visual white space — design directions, color moods, or aesthetics that NO competitor currently uses. Call this out in the variant_name or logo_prompt.
- Colors MUST reflect the brand_archetype and tone_of_voice, but interpreted differently in each variant.
- Each color_palette array must have EXACTLY 5 hex values.
- Fonts MUST be real Google Fonts (Inter, Playfair Display, Space Grotesk, DM Sans, Lora, Outfit, Raleway, Montserrat, Poppins, Merriweather, Roboto Slab, Nunito, Oswald, Crimson Text, Work Sans, Bebas Neue, Archivo).
- Use DIFFERENT font pairings across variants.
- The ideogram_prompt MUST be self-contained and end with: logo design, vector, transparent background, professional, high quality.
- If user feedback is provided, address it DIRECTLY in ALL variants.
- Return ONLY valid JSON with no markdown fences, no extra text."""


# ── SVG logo generation prompt ─────────────────────────────────────────────────
SVG_LOGO_SYSTEM_PROMPT = """You are an expert SVG logo designer. Generate a clean, professional SVG logo based on the given description.

CRITICAL SVG RULES:
- Output ONLY the raw SVG code — no markdown fences, no explanation, no extra text.
- Start with <svg and end with </svg>.
- Use viewBox="0 0 200 200" for consistent sizing.
- Include xmlns="http://www.w3.org/2000/svg" on the <svg> tag.
- Use ONLY the provided hex colors from the brand palette.
- Keep the SVG clean and minimal — avoid overly complex paths.
- For wordmark/lettermark logos: use <text> elements with appropriate font-family (Arial, Helvetica, Georgia, or the specified font).
- For icon/abstract/emblem logos: use geometric shapes (<circle>, <rect>, <polygon>, <path>) to create a visually striking mark.
- For combination marks: combine a simple icon with text.
- Ensure good contrast and visual balance.
- Do NOT use external images, links, or raster data.
- Do NOT include any JavaScript or interactive elements.
- Keep total SVG under 5KB.
- Make the logo look PROFESSIONAL — this is for a real brand.
- Center the logo within the viewBox."""


# ── Google Font helpers ────────────────────────────────────────────────────────
FREE_FONT_PAIRS = {
    "minimal": {"heading": "Inter", "body": "Manrope", "accent": "Space Grotesk", "reason": "Clean, modern, and highly readable."},
    "modern": {"heading": "Manrope", "body": "Inter", "accent": "Sora", "reason": "Neutral and flexible for contemporary brands."},
    "premium": {"heading": "Playfair Display", "body": "Inter", "accent": "Cormorant Garamond", "reason": "Elegant editorial feel with modern readability."},
    "bold": {"heading": "Montserrat", "body": "DM Sans", "accent": "Oswald", "reason": "Strong, geometric, and attention-grabbing."},
    "creative": {"heading": "Poppins", "body": "Nunito Sans", "accent": "Syne", "reason": "Friendly, expressive, and versatile."},
    "tech": {"heading": "Space Grotesk", "body": "Inter", "accent": "IBM Plex Sans", "reason": "Sharp, futuristic, and product-focused."},
}


def _font_css_url(font_name: str, weights: str = "400;500;600;700;800") -> str:
    family = quote_plus(font_name).replace("%20", "+")
    return f"https://fonts.googleapis.com/css2?family={family}:wght@{weights}&display=swap"


def _pick_font_family(design_style: str, keywords: list[str]) -> dict:
    style_text = f"{design_style} {' '.join(keywords)}".lower()
    if any(t in style_text for t in ["luxury", "premium", "elegant", "editorial", "fashion"]):
        return FREE_FONT_PAIRS["premium"]
    if any(t in style_text for t in ["tech", "ai", "software", "saas", "product", "digital"]):
        return FREE_FONT_PAIRS["tech"]
    if any(t in style_text for t in ["bold", "dynamic", "vibrant", "sport", "startup"]):
        return FREE_FONT_PAIRS["bold"]
    if any(t in style_text for t in ["creative", "playful", "art", "organic", "handmade"]):
        return FREE_FONT_PAIRS["creative"]
    if any(t in style_text for t in ["minimal", "clean", "simple", "sleek"]):
        return FREE_FONT_PAIRS["minimal"]
    return FREE_FONT_PAIRS["modern"]


def _domain_label(url: str) -> str:
    host = (urlparse(url).netloc or "").lower().replace("www.", "")
    if "pinterest" in host: return "Pinterest"
    if "behance" in host: return "Behance"
    if "dribbble" in host: return "Dribbble"
    if "instagram" in host: return "Instagram"
    if "logo" in host: return "Logo"
    return host.split(".")[0].title() if host else "Source"


def _fallback_queries(brand_name: str, archetype: str, design_style: str) -> list[dict]:
    return [
        {"label": "Pinterest Logo Grid", "query": f"site:pinterest.com {brand_name} playful logo inspiration board", "reason": "Find logo collage and inspiration grid references"},
        {"label": "Pinterest Brand Board", "query": f"site:pinterest.com {brand_name} complete brand board logo color palette typography", "reason": "Find complete mini brand identity boards"},
        {"label": "Pinterest Packaging + Logo", "query": f"site:pinterest.com {brand_name} packaging logo identity mockup {design_style}", "reason": "Get applied brand visuals with logo in context"},
        {"label": "Pinterest Handwritten Logo", "query": f"site:pinterest.com {brand_name} hand lettering logo inspiration", "reason": "Find expressive handcrafted logo styles"},
        {"label": "Dribbble Identity Boards", "query": f"site:dribbble.com {archetype} brand identity logo board", "reason": "Find professional concept boards"},
        {"label": "Behance Brand Identity", "query": f"site:behance.net {brand_name} brand identity logo case study", "reason": "Find full identity case studies"},
    ]


def _build_variant_queries(
    variants: list[dict],
    brand_name: str,
    archetype: str,
) -> list[dict]:
    """
    Build brand-specific Pinterest/Behance/Dribbble search queries derived
    from the generated variants — no extra API call needed.
    Produces smarter, more targeted results than the fixed fallback templates.
    """
    queries: list[dict] = []
    seen_queries: set[str] = set()

    def _add(label: str, query: str, reason: str) -> None:
        q = query.strip()
        if q and q not in seen_queries:
            seen_queries.add(q)
            queries.append({"label": label, "query": q, "reason": reason})

    # ── Variant-driven queries (most specific) ─────────────────────────
    for v in variants[:5]:  # top 5 variants are enough
        vname = v.get("variant_name", "").strip()
        ltype = v.get("logo_type", "").replace("_", " ").strip()
        # Extract 1-2 meaningful style words from variant_name
        style_words = " ".join(vname.split()[:2]) if vname else archetype

        if ltype:
            _add(
                f"Pinterest – {vname or ltype}",
                f"site:pinterest.com {style_words} {ltype} logo brand identity",
                f"Inspiration for the '{vname}' variant ({ltype} style)",
            )

    # ── Color mood queries (from first 3 variants' palette context) ────
    color_moods = []
    for v in variants[:3]:
        roles = v.get("color_roles", {})
        if isinstance(roles, dict):
            primary_desc = list(roles.values())[0] if roles else ""
            # Extract descriptive words before the dash
            mood = primary_desc.split("—")[0].replace("#", "").strip()
            if mood and len(mood) > 2:
                color_moods.append(mood)

    if color_moods:
        _add(
            "Pinterest – Color Palette Moodboard",
            f"site:pinterest.com {color_moods[0]} brand color palette identity",
            "Color-matched moodboard references from Pinterest",
        )

    # ── Archetype-driven brand board ───────────────────────────────────
    _add(
        "Pinterest – Brand Archetype Board",
        f"site:pinterest.com {archetype} archetype brand identity logo board",
        "Visual direction aligned with brand archetype",
    )

    # ── Typography queries from variant fonts ──────────────────────────
    fonts_seen: set[str] = set()
    for v in variants[:4]:
        hfont = v.get("heading_font", "").strip()
        if hfont and hfont not in fonts_seen:
            fonts_seen.add(hfont)
            _add(
                f"Pinterest – {hfont} Typography",
                f"site:pinterest.com {hfont} typography logo brand design",
                f"Logo designs using {hfont} typeface",
            )

    # ── Logo type grids (professional platforms) ───────────────────────
    logo_types_used = list({v.get("logo_type", "").replace("_", " ") for v in variants if v.get("logo_type")})[:2]
    for lt in logo_types_used:
        _add(
            f"Dribbble – {lt.title()}",
            f"site:dribbble.com {lt} logo design {archetype} brand",
            f"Professional {lt} logo explorations on Dribbble",
        )

    # ── Full brand identity case study ────────────────────────────────
    _add(
        "Behance – Brand Identity Case Study",
        f"site:behance.net {brand_name} brand identity logo case study",
        "Full identity systems and real-world branding references",
    )

    # ── Pad with fallback if under 6 queries ──────────────────────────
    if len(queries) < 6:
        for fq in _fallback_queries(brand_name, archetype, variants[0].get("variant_name", "modern") if variants else "modern"):
            _add(fq["label"], fq["query"], fq["reason"])
            if len(queries) >= 10:
                break

    return queries[:10]  # cap at 10 to limit web search calls


async def _collect_links(search_queries: list[dict], target_count: int = 18) -> list[dict]:
    all_links: list[dict] = []
    for item in search_queries:
        query = item.get("query", "").strip()
        if not query:
            continue
        results = await web_search(query, num_results=6)
        for result in results:
            link = result.get("link", "")
            title = result.get("title", "")
            if not link or not title:
                continue
            all_links.append({
                "title": title, "brand_name": title, "link": link,
                "snippet": result.get("snippet", ""), "query": query,
                "query_label": item.get("label", "Visual Search"),
                "platform": _domain_label(link),
            })

    seen: set[str] = set()
    unique_links: list[dict] = []
    for item in all_links:
        if item["link"] in seen:
            continue
        seen.add(item["link"])
        unique_links.append(item)

    pinterest = [i for i in unique_links if "pinterest" in i.get("platform", "").lower()]
    non_pinterest = [i for i in unique_links if "pinterest" not in i.get("platform", "").lower()]
    preferred = pinterest[:14] + non_pinterest
    final_count = max(15, min(target_count, 20))
    selected = preferred[:final_count]

    if len(selected) < 15:
        for item in search_queries:
            if len(selected) >= 15:
                break
            query = (item.get("query", "") or "").strip()
            if not query:
                continue
            search_url = f"https://www.pinterest.com/search/pins/?q={quote_plus(query)}"
            if any(e.get("link") == search_url for e in selected):
                continue
            selected.append({
                "title": f"Pinterest search: {item.get('label', 'Visual Inspiration')}",
                "brand_name": item.get("label", "Pinterest Inspiration"),
                "link": search_url,
                "snippet": item.get("reason", "Curated Pinterest search for brand-board style references."),
                "query": query, "query_label": item.get("label", "Pinterest Search"), "platform": "Pinterest",
            })

    return selected[:final_count]


# ── SVG generation ─────────────────────────────────────────────────────────────
async def _generate_svg_logo(variant: dict, index: int, brand_name: str) -> str | None:
    """Generate a single SVG logo via Groq. Returns raw SVG string or None."""
    logo_prompt = variant.get("logo_prompt", "")
    logo_type = variant.get("logo_type", "abstract_mark")
    colors = variant.get("color_palette", [])

    user_prompt = (
        f"Brand name: {brand_name}\n"
        f"Logo type: {logo_type}\n"
        f"Color palette: {', '.join(colors)}\n"
        f"Logo concept: {logo_prompt}\n\n"
        f"Generate the SVG logo now. Output ONLY the raw SVG code."
    )

    async with _SVG_SEMAPHORE:
        try:
            raw = await call_llm(
                system_prompt=SVG_LOGO_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.9,
                max_tokens=2000,
            )
            svg_match = re.search(r'<svg[\s\S]*?</svg>', raw, re.IGNORECASE)
            if not svg_match:
                return None
            svg = svg_match.group(0)
            if 'xmlns=' not in svg:
                svg = svg.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
            return svg
        except Exception as exc:
            print(f"[visual_identity] SVG variant {index + 1} error: {exc}")
            return None


async def _generate_all_svg_logos(variants: list[dict], brand_name: str) -> None:
    """Generate SVG logos for all variants concurrently. Mutates variants in-place."""
    tasks = [_generate_svg_logo(v, i, brand_name) for i, v in enumerate(variants)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(results):
        if isinstance(result, Exception) or result is None:
            variants[i]["logo_url"] = None
            variants[i]["logo_svg"] = None
        else:
            variants[i]["logo_svg"] = result
            svg_b64 = base64.b64encode(result.encode("utf-8")).decode("utf-8")
            variants[i]["logo_url"] = f"data:image/svg+xml;base64,{svg_b64}"


async def regenerate_variant_svg(
    variant: dict,
    variant_index: int,
    brand_name: str,
    new_color_palette: list[str],
    heading_font: str | None = None,
    body_font: str | None = None,
) -> dict:
    """
    Regenerate a single variant's SVG with a new colour palette and/or new fonts.
    Returns an updated copy of the variant dict.
    """
    updated = dict(variant)
    old_palette = list(variant.get("color_palette", []))
    updated["color_palette"] = new_color_palette

    # Apply font overrides
    if heading_font:
        updated["heading_font"] = heading_font
    if body_font:
        updated["body_font"] = body_font

    # Patch hex codes in logo_prompt and ideogram_prompt
    for field in ("logo_prompt", "ideogram_prompt"):
        text = updated.get(field, "")
        for old_hex, new_hex in zip(old_palette, new_color_palette):
            text = text.replace(old_hex, new_hex)
        # Patch old font name references in prompts
        if heading_font and variant.get("heading_font"):
            text = text.replace(variant["heading_font"], heading_font)
        if body_font and variant.get("body_font"):
            text = text.replace(variant["body_font"], body_font)
        updated[field] = text

    # Patch color_roles descriptions
    roles = dict(variant.get("color_roles", {}))
    for key, desc in roles.items():
        for old_hex, new_hex in zip(old_palette, new_color_palette):
            desc = desc.replace(old_hex, new_hex)
        roles[key] = desc
    updated["color_roles"] = roles

    # Regenerate SVG
    new_svg = await _generate_svg_logo(updated, variant_index, brand_name)
    if new_svg:
        updated["logo_svg"] = new_svg
        svg_b64 = base64.b64encode(new_svg.encode("utf-8")).decode("utf-8")
        updated["logo_url"] = f"data:image/svg+xml;base64,{svg_b64}"
    else:
        updated["logo_svg"] = variant.get("logo_svg")
        updated["logo_url"] = variant.get("logo_url")

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
    """Generate 10 brand identity variants with SVG logos + inspiration links."""
    idea_discovery_data = idea_discovery_data if isinstance(idea_discovery_data, dict) else {}
    market_research_data = market_research_data if isinstance(market_research_data, dict) else {}
    competitor_data = competitor_data if isinstance(competitor_data, dict) else {}
    strategy_data = strategy_data if isinstance(strategy_data, dict) else {}
    naming_data = naming_data if isinstance(naming_data, dict) else {}

    brand_name = naming_data.get("brand_name", "Brand")
    tagline = naming_data.get("tagline", "")
    brand_personality = strategy_data.get("brand_personality", {}) if isinstance(strategy_data.get("brand_personality"), dict) else {}
    archetype = brand_personality.get("archetype", "modern")

    # Build business profile for the prompt
    business_profile = {
        "business_name": brand_name,
        "tagline": tagline,
        "brand_archetype": archetype,
        "tone_of_voice": brand_personality.get("tone_of_voice", ""),
        "brand_values": strategy_data.get("brand_values", []),
        "positioning_statement": strategy_data.get("positioning_statement", ""),
        "unique_selling_proposition": strategy_data.get("unique_selling_proposition", ""),
        "target_segments": strategy_data.get("target_segments", []),
        "industry": idea_discovery_data.get("industry_category", ""),
        "business_model": idea_discovery_data.get("business_model", ""),
        "problem_solved": idea_discovery_data.get("problem_solved", ""),
        "value_proposition": idea_discovery_data.get("value_proposition", ""),
        "brand_tone_hints": idea_discovery_data.get("brand_tone_hints", ""),
        "core_features": idea_discovery_data.get("core_features", []),
        "market_gaps": market_research_data.get("market_gaps", []),
        "competitor_weaknesses": [
            c.get("weaknesses", []) for c in competitor_data.get("direct_competitors", [])[:3]
            if isinstance(c, dict)
        ],
    }

    market_trends = market_research_data.get("market_trends", [])

    # ── Competitor design analysis ─────────────────────────────────────
    competitor_design_profiles = [
        {
            "name": c.get("name", ""),
            "design_trends": c.get("design_trends", {}),
        }
        for c in competitor_data.get("direct_competitors", [])[:4]
        if isinstance(c, dict) and c.get("design_trends")
    ]
    industry_design_trends = competitor_data.get("industry_design_trends", {})

    user_prompt = (
        f"Business Profile:\n{json.dumps(business_profile, indent=2)}\n\n"
        f"Market Trends:\n{json.dumps(market_trends, indent=2)}\n\n"
        + (
            f"Competitor Design Profiles (use these to DIFFERENTIATE — avoid their visual clichés):\n"
            f"{json.dumps(competitor_design_profiles, indent=2)}\n\n"
            if competitor_design_profiles else ""
        )
        + (
            f"Industry Design Trends (reference the white space to find unexplored visual directions):\n"
            f"{json.dumps(industry_design_trends, indent=2)}\n\n"
            if industry_design_trends else ""
        )
        + f"Brand Name: {brand_name}\n"
        f"Tagline: {tagline}\n"
        + (f"\nUser Feedback (address in ALL variants): {feedback}" if feedback else "")
        + "\n\nGenerate 10 distinct brand identity variants. Use the competitor design profiles "
        "to ensure at least 3 variants deliberately occupy the visual white space — directions "
        "no existing competitor has claimed."
    )

    # ── Step 1: Generate 10 variants (1 Groq call) ─────────────────────
    raw = await call_llm(
        system_prompt=VARIANTS_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.8,
        max_tokens=4096,
    )

    try:
        # Strip possible markdown fences
        clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw.strip(), flags=re.MULTILINE)
        parsed = json.loads(clean)
        variants = parsed.get("variants", [])
    except Exception:
        variants = []

    if not isinstance(variants, list):
        variants = []

    # ── Step 2: Generate SVG logos concurrently (10 Groq calls, free) ──
    if variants:
        await _generate_all_svg_logos(variants, brand_name)

    # ── Step 3: Build variant-driven search queries (no extra API call) ─
    first_variant = variants[0] if variants else {}
    design_style = first_variant.get("variant_name", "modern")

    if variants:
        search_queries = _build_variant_queries(variants, brand_name, archetype)
    else:
        search_queries = _fallback_queries(brand_name, archetype, design_style)

    # ── Step 4: Collect inspiration links via web search ────────────────
    inspiration_links = await _collect_links(search_queries, target_count=18)

    # ── Step 5: Build backwards-compatible output ────────────────────────
    # Derive top-level keys from first variant so existing agents/UI still work
    first_colors = first_variant.get("color_palette", ["#000000", "#ffffff", "#cccccc", "#333333", "#f5f5f5"])
    font_bundle = _pick_font_family(design_style, [archetype])

    data: dict = {
        # Existing keys (kept for compatibility with guidelines_agent, UI, etc.)
        "design_style": design_style,
        "mood_keywords": [archetype, "professional", "distinctive", "modern"],
        "design_trends": design_trends[:4],
        "imagery_style": f"Visual identity built around {archetype} archetype with {design_style} direction.",
        "logo_direction": {
            "summary": first_variant.get("logo_prompt", f"A {design_style} logo for {brand_name}.")[:200],
            "best_logo_types": list({v.get("logo_type") for v in variants[:5] if v.get("logo_type")}),
            "style_words": [design_style, archetype, "distinctive"],
            "avoid_words": ["generic", "clip-art", "overused gradients"],
            "why_it_fits": f"Designed to reflect the {archetype} archetype and stand out in the {business_profile.get('industry', 'market')}.",
        },
        "color_palette": {
            "primary": {"hex": first_colors[0] if len(first_colors) > 0 else "#000000", "name": "Primary", "usage": "Main brand color"},
            "secondary": {"hex": first_colors[1] if len(first_colors) > 1 else "#ffffff", "name": "Secondary", "usage": "Supporting elements"},
            "accent": {"hex": first_colors[2] if len(first_colors) > 2 else "#cccccc", "name": "Accent", "usage": "CTAs and highlights"},
            "neutral_dark": {"hex": first_colors[3] if len(first_colors) > 3 else "#333333", "name": "Dark Neutral", "usage": "Primary text"},
            "neutral_light": {"hex": first_colors[4] if len(first_colors) > 4 else "#f5f5f5", "name": "Light Neutral", "usage": "Backgrounds"},
        },
        "typography": {
            "heading_font": first_variant.get("heading_font") or font_bundle["heading"],
            "body_font": first_variant.get("body_font") or font_bundle["body"],
            "accent_font": font_bundle["accent"],
            "font_provider": "Google Fonts (free)",
            "font_reason": first_variant.get("font_pairing_rationale") or font_bundle["reason"],
            "heading_font_url": _font_css_url(first_variant.get("heading_font") or font_bundle["heading"]),
            "body_font_url": _font_css_url(first_variant.get("body_font") or font_bundle["body"]),
            "accent_font_url": _font_css_url(font_bundle["accent"]),
        },
        "search_queries": search_queries,
        "logo_inspiration_notes": [
            "Explore at least 3 logo types across the variants",
            "Consider scalability — test at 32px and 512px",
            "Avoid gradients in primary mark; use flat colors for versatility",
        ],
        "reference_brands": [
            {"name": item.get("title", "Reference"), "website": item.get("link", ""), "reason": item.get("query_label", "Inspiration")}
            for item in inspiration_links[:10]
        ],
        "logo_inspiration": inspiration_links,
        "competitor_logo_brands": [
            {"name": item.get("title", "Reference"), "website": item.get("link", ""), "reason": item.get("query_label", "")}
            for item in inspiration_links[:12]
        ],
        # New key: 10 variants with SVG logos
        "variants": variants,
        "combined_summary": (
            f"Visual identity output for {brand_name}: {len(variants)} variants generated "
            f"({sum(1 for v in variants if v.get('logo_svg'))} with SVG logos), "
            f"{len(inspiration_links)} inspiration links."
        ),
    }

    svgs_generated = sum(1 for v in variants if v.get("logo_svg"))
    explanation = (
        f"Visual identity generated for '{brand_name}': {len(variants)} brand variants created, "
        f"{svgs_generated} with SVG logos rendered. "
        f"Each variant has a unique logo type, color palette, font pairing, and ideogram prompt. "
        f"{len(inspiration_links)} inspiration links collected (Pinterest-prioritized). "
        f"Backwards-compatible design direction derived from the top variant. "
        f"All SVG logos encoded as base64 data URIs for direct rendering."
    )

    return AgentResult(data=data, explanation=explanation)
