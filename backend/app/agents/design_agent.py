"""
Agent 6 – Design Intelligence Agent
Suggests visual identity: color palettes, typography, styling trends,
and references competitor designs via image search.
"""
import json
from urllib.parse import quote_plus

from app.utils.llm import call_llm
from app.utils.image_search import image_search
from app.schemas.brand_schema import AgentResult


SYSTEM_PROMPT = """You are a Senior Art Director and Visual Identity Strategist. Your goal is to translate brand strategy into a cohesive, high-impact visual language.

VISUAL DESIGN PRINCIPLES:
1. SEMANTIC COLOR THEORY: Choose colors based on the emotional triggers defined in the Brand Strategy. Do not just pick 'nice' colors; pick colors that psychologically align with the Brand Archetype.
2. ACCESSIBILITY: Ensure high contrast between 'neutral_light' and 'neutral_dark' for readability.
3. LOGO SYMBOLISM: Describe a logo direction that focuses on 'Silhouette' and 'Scalability'. Suggest specific symbols or metaphors (e.g., 'Abstract geometric bird' or 'Modern serif wordmark').
4. DESIGN TRENDS: Reference modern movements (e.g., Bento Grid, Neo-Brutalism, Glassmorphism, or Organic Minimalism) that fit the industry context.

Your output must be a JSON object with EXACTLY these keys:
{
  "design_style": "A specific aesthetic name (e.g., High-Tech Minimalist or Heritage Premium)",
  "color_palette": {
    "primary": {"hex": "#XXXXXX", "name": "Name", "usage": "Hero sections and brand mark"},
    "secondary": {"hex": "#XXXXXX", "name": "Name", "usage": "Supporting graphics"},
    "accent": {"hex": "#XXXXXX", "name": "Name", "usage": "High-conversion buttons and highlights"},
    "neutral_dark": {"hex": "#XXXXXX", "name": "Name", "usage": "Primary typography and depth"},
    "neutral_light": {"hex": "#XXXXXX", "name": "Name", "usage": "Clean background and negative space"}
  },
  "typography": {
    "heading_font": "Suggested high-impact font",
    "body_font": "Suggested highly-readable font",
    "accent_font": "Optional character font"
  },
  "design_trends": ["Relevant trend 1", "Relevant trend 2", "Relevant trend 3"],
  "mood_keywords": ["Keyword1", "Keyword2", "Keyword3", "Keyword4"],
  "logo_direction": "Detailed technical brief for a logo designer (concepts, shapes, feeling).",
  "imagery_style": "Detailed description for photography or AI image generation (e.g., 'Natural lighting, grain, candid, high-end')",
  "competitor_design_references": ["Visual element to learn from 1", "Visual trap to avoid 2"]
}

Return ONLY valid JSON. Ensure 'mood_keywords' are descriptive enough to inform font selection logic."""

FREE_FONT_PAIRS = {
    "minimal": {
        "heading": "Inter",
        "body": "Manrope",
        "accent": "Space Grotesk",
        "reason": "Clean, modern, and highly readable.",
    },
    "modern": {
        "heading": "Manrope",
        "body": "Inter",
        "accent": "Sora",
        "reason": "Neutral and flexible for contemporary brands.",
    },
    "premium": {
        "heading": "Playfair Display",
        "body": "Inter",
        "accent": "Cormorant Garamond",
        "reason": "Elegant editorial feel with modern readability.",
    },
    "bold": {
        "heading": "Montserrat",
        "body": "DM Sans",
        "accent": "Oswald",
        "reason": "Strong, geometric, and attention-grabbing.",
    },
    "creative": {
        "heading": "Poppins",
        "body": "Nunito Sans",
        "accent": "Syne",
        "reason": "Friendly, expressive, and versatile.",
    },
    "tech": {
        "heading": "Space Grotesk",
        "body": "Inter",
        "accent": "IBM Plex Sans",
        "reason": "Sharp, futuristic, and product-focused.",
    },
    "elegant": {
        "heading": "Cormorant Garamond",
        "body": "Source Sans 3",
        "accent": "Libre Baskerville",
        "reason": "Refined, premium, and timeless.",
    },
}


def _font_css_url(font_name: str, weights: str = "400;500;600;700;800") -> str:
    family = quote_plus(font_name).replace("%20", "+")
    return f"https://fonts.googleapis.com/css2?family={family}:wght@{weights}&display=swap"


def _pick_font_family(design_style: str, keywords: list[str]) -> dict:
    style_text = f"{design_style} {' '.join(keywords)}".lower()

    if any(token in style_text for token in ["luxury", "premium", "elegant", "editorial", "fashion"]):
        return FREE_FONT_PAIRS["premium"]
    if any(token in style_text for token in ["tech", "ai", "software", "saas", "product", "digital"]):
        return FREE_FONT_PAIRS["tech"]
    if any(token in style_text for token in ["bold", "dynamic", "vibrant", "sport", "startup"]):
        return FREE_FONT_PAIRS["bold"]
    if any(token in style_text for token in ["creative", "playful", "art", "brand", "modern"]):
        return FREE_FONT_PAIRS["creative"]
    if any(token in style_text for token in ["minimal", "clean", "simple", "sleek"]):
        return FREE_FONT_PAIRS["minimal"]

    return FREE_FONT_PAIRS["modern"]


async def run(
    strategy_data: dict,
    naming_data: dict,
    feedback: str | None = None,
) -> AgentResult:
    """Execute the Design Intelligence Agent."""
    brand_name = naming_data.get("brand_name", "")
    industry = strategy_data.get("brand_personality", {}).get("archetype", "")

    # Gather visual trends via image search
    search_queries = [
        f"{brand_name} brand design inspiration",
        f"{industry} modern logo design trends 2024",
        f"premium brand identity design {strategy_data.get('brand_values', ['innovative'])[0]}",
    ]

    image_refs = []
    for q in search_queries:
        imgs = await image_search(q, num_results=3)
        image_refs.extend(imgs)

    image_context = "\n".join(
        f"- {img.get('title', 'Design reference')} | Image: {img.get('imageUrl', '')} | Source: {img.get('link', '') or img.get('source', '')}"
        for img in image_refs[:8]
    )

    feedback_clause = ""
    if feedback:
        feedback_clause = f"\n\nUSER FEEDBACK FOR REDESIGN: {feedback}\nAdjust the design direction based on this feedback."

    user_prompt = (
        f"BRAND STRATEGY:\n{json.dumps(strategy_data, indent=2)}\n\n"
        f"BRAND NAME: {brand_name}\n\n"
        f"VISUAL TREND REFERENCES:\n{image_context}\n\n"
        f"Create a complete design direction for this brand.{feedback_clause}"
    )

    raw = await call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.7,
        response_format={"type": "json_object"},
    )

    data = json.loads(raw)
    free_fonts = _pick_font_family(data.get("design_style", "modern"), data.get("mood_keywords", []))
    typography = data.get("typography", {})
    heading_font = free_fonts["heading"]
    body_font = free_fonts["body"]
    accent_font = free_fonts["accent"]
    data["typography"] = {
        "heading_font": heading_font,
        "body_font": body_font,
        "accent_font": accent_font,
        "font_provider": "Google Fonts (free)",
        "font_reason": free_fonts["reason"],
        "heading_font_url": _font_css_url(heading_font),
        "body_font_url": _font_css_url(body_font),
        "accent_font_url": _font_css_url(accent_font),
        "google_fonts_specimen": {
            "heading": f"https://fonts.google.com/specimen/{heading_font.replace(' ', '+')}",
            "body": f"https://fonts.google.com/specimen/{body_font.replace(' ', '+')}",
            "accent": f"https://fonts.google.com/specimen/{accent_font.replace(' ', '+')}",
        },
        "original_llm_typography": typography,
    }
    data["image_references"] = [
        {
            "title": img.get("title", ""),
            "imageUrl": img.get("imageUrl", ""),
            "link": img.get("link", "") or img.get("source", ""),
            "source": img.get("source", ""),
            "thumbnailUrl": img.get("thumbnailUrl", ""),
        }
        for img in image_refs[:6]
    ]
    data["reference_links"] = [
        {
            "title": img.get("title", ""),
            "url": img.get("link", "") or img.get("source", ""),
        }
        for img in image_refs[:6]
        if img.get("link") or img.get("source")
    ]

    palette = data.get("color_palette", {})
    primary_hex = palette.get("primary", {}).get("hex", "N/A")
    explanation = (
        f"Design direction established: '{data.get('design_style', 'modern')}' style. "
        f"Primary color is {palette.get('primary', {}).get('name', 'N/A')} ({primary_hex}). "
        f"Typography pairs {data.get('typography', {}).get('heading_font', 'N/A')} headers "
        f"with {data.get('typography', {}).get('body_font', 'N/A')} body text using free Google Fonts. "
        f"Current design trends applied: {', '.join(data.get('design_trends', [])[:3])}. "
        f"Logo direction: {data.get('logo_direction', 'N/A')[:80]}. "
        f"{len(image_refs)} competitor/trend design references were analyzed."
    )

    return AgentResult(data=data, explanation=explanation)
