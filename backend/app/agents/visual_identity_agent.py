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
VARIANTS_SYSTEM_PROMPT = """You are a world-class brand identity designer, creative director, and competitive brand strategist.

You receive a full brand brief: brand strategy, tone of voice, brand values, target audience psychographics,
market research data, competitor visual profiles, and industry design trends.

Generate 6 distinct brand identity variants. Every single decision — color, type, logo form, prompt wording —
must be traceable back to: (1) the brand's emotional promise, (2) its tone of voice, (3) industry standards,
(4) a specific market trend, and (5) a gap left by named competitors.

The Midjourney and Ideogram prompts must be LONG, DETAILED, and IMMEDIATELY usable — a designer or AI tool
should be able to execute them without any additional context.

Return this exact JSON structure:
{
  "variants": [
    {
      "variant_name": "Short evocative direction name (e.g. 'Authoritative Trust', 'Kinetic Clarity')",

      "visual_strategy": "3-4 sentences covering: (1) what emotional state this triggers in the target audience, (2) what market positioning it owns, (3) which competitor(s) it differentiates from and how, (4) which industry standard or convention it follows or deliberately breaks",

      "logo_motivation": "Explain in 2-3 sentences: which specific market trend from the research this design captures, which specific competitor weakness it exploits, and what emotional language the logo speaks — e.g. does it feel reassuring, ambitious, innovative, grounded?",

      "brand_emotion": {
        "primary_emotion": "The single core emotion this logo should make the audience feel (e.g. 'trusted', 'excited', 'relieved', 'empowered')",
        "emotional_language": "Describe the visual language that carries this emotion — e.g. 'stability through horizontal weight', 'forward motion through italic lean', 'warmth through rounded terminals'",
        "voice_translation": "How the brand's tone of voice (e.g. authoritative, friendly, bold) is translated into visual form — specific decisions like weight, spacing, geometry that echo the voice",
        "audience_resonance": "Why this specific emotional direction resonates with the target audience's psychographics and pain points"
      },

      "competitive_positioning": {
        "differentiates_from": "Competitor name(s) this variant contrasts most strongly with",
        "how_different": "Specific visual differences — color psychology, style, weight, form language, tone — vs those competitors",
        "trend_captured": "The exact market trend from the research this variant owns (quote or paraphrase from the data)",
        "white_space_claimed": "The visual territory no competitor has claimed that this variant occupies",
        "industry_standard_used": "Which established industry visual convention this follows to build instant category recognition (e.g. 'fintech brands use deep navy for trust')",
        "industry_standard_broken": "Which industry visual cliché this deliberately breaks to stand out"
      },

      "color_palette": ["#hex1", "#hex2", "#hex3", "#hex4", "#hex5"],
      "color_roles": {
        "primary":       "#hex1 — name, emotional meaning, why it fits brand values, how it differs from key competitor's primary color",
        "secondary":     "#hex2 — name, role, emotional contrast or harmony with primary",
        "accent":        "#hex3 — name, role, used for CTAs and energy — why this hue specifically",
        "light_neutral": "#hex4 — name, used for backgrounds, breathing room, warmth or coolness",
        "dark_neutral":  "#hex5 — name, used for text and grounding — why this tone not pure black"
      },

      "heading_font": "Exact Google Font name",
      "body_font": "Exact Google Font name",
      "font_pairing_rationale": "Explain: (1) what personality the heading font projects and why it matches brand tone, (2) why the body font ensures readability at scale, (3) how this pairing differs from competitors' typical type choices in this industry",

      "wordmark_prompt": {
        "concept": "Detailed concept: lettering style, weight (thin/regular/bold/black), any custom letterform touches (modified terminals, ligatures, crossbars), spacing philosophy (tight/optical/wide), what brand value each decision reinforces, which competitor aesthetic is deliberately avoided and why",
        "midjourney_prompt": "'[Brand Name]' wordmark logo, [precise font weight: e.g. bold geometric sans-serif / elegant serif / condensed display], [letterform details: e.g. sharp angular terminals / rounded open apertures / high x-height], [exact hex color: e.g. primary color #XXXXXX on white], [emotional tone: e.g. authoritative and trustworthy / energetic and forward-moving / warm and approachable], [industry context: e.g. fintech / healthcare / fashion], clean minimal professional wordmark logo, vector, flat design, white background, no gradients, no shadows, high quality --ar 3:1 --style raw",
        "ideogram_prompt": "'[Brand Name]' wordmark logo text, [font style], [weight], [color #XXXXXX], [emotional adjectives], [industry: e.g. financial services / wellness / technology], professional brand logo, vector, clean white background, no icon, text only, high resolution",
        "designer_brief": "For a human designer — (1) typeface classification and specific alternatives to explore, (2) exact tracking/letter-spacing values, (3) color application rules (PMS/CMYK equivalents if relevant), (4) any custom letterform modifications to commission, (5) industry visual clichés to explicitly avoid, (6) how the final wordmark should feel when a customer sees it for the first time"
      },

      "logomark_prompt": {
        "concept": "Detailed concept: what the symbol represents literally and metaphorically, the geometric or organic construction logic, use of negative space, what brand value or emotional promise the form embodies, how it visually contrasts with competitor iconography in this industry",
        "midjourney_prompt": "[Describe icon: e.g. abstract interlocking arcs / geometric shield with cutout / minimal leaf form / bold letter initial] logo mark icon, [exact construction: e.g. two overlapping circles creating a lens / chevron pointing upward with rounded corners], [color hex codes from palette: primary #XXXXXX], [style: flat vector / minimal line / filled geometric], [emotional tone: e.g. stable and protective / dynamic and progressive / organic and human], professional brand icon, vector, white background, no text, scalable, high quality --ar 1:1 --style raw",
        "ideogram_prompt": "[Icon description in detail], logo mark symbol, [primary color #XXXXXX], [style: minimal flat / geometric / abstract], [emotional quality: e.g. trustworthy / innovative / grounded], brand icon, transparent background, no text, professional, high quality",
        "designer_brief": "For a human designer — (1) precise geometric construction (grid, ratios, anchor points), (2) what the icon must communicate at 16px favicon size vs 500px hero size, (3) negative space usage instructions, (4) color application in single-color version, (5) what the icon should emotionally communicate, (6) what visual symbols are overused in this industry and must be avoided"
      }
    }
  ]
}

CRITICAL RULES:
- Generate EXACTLY 6 variants with meaningfully different visual directions.
- EVERY variant must include brand_emotion — prompts without emotional direction produce generic logos.
- EVERY variant must name specific competitors from the provided data and explain visual differentiation.
- EVERY variant must reference a specific market trend from the provided research.
- The Midjourney and Ideogram prompts must be long and detailed — minimum 40 words each. Generic short prompts are unacceptable.
- Include EXACT hex codes from the variant's color_palette in every prompt.
- At least 2 variants must occupy visual white space no competitor has claimed.
- At least 1 variant must follow an industry visual convention to build category trust, but add a distinctive twist.
- Color palettes must be emotionally intentional — explain the psychology of each color choice.
- Fonts must be real Google Fonts available in 2024.
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
