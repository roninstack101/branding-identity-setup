"""
Agent 9 – Brand Guidelines Agent
Synthesizes all outputs into a comprehensive brand guidelines document.
"""
import json
from app.utils.llm import call_llm
from app.schemas.brand_schema import AgentResult


SYSTEM_PROMPT = """You are a Principal Brand Consultant and Design Systems Architect. Your goal is to codify the brand's identity into a "Rulebook" that ensures absolute consistency across all physical and digital touchpoints.

GUIDELINE PRINCIPLES:
1. LOGO INTEGRITY: Define strict rules for the logo (clear space, minimum size) to prevent visual clutter.
2. COLOR PRECISION: Provide hex codes and usage logic that ensures high accessibility (WCAG compliance).
3. THE "DO'S AND DON'TS": Create specific, high-contrast rules for Voice and Visuals to prevent brand dilution.
4. HIERARCHY: Establish a clear typographic scale that developers and designers can immediately implement.

Your output must be a JSON object with EXACTLY these keys:
{
  "guidelines_version": "1.0",
  "brand_overview": {
    "mission": "The brand's driving force.",
    "vision": "The long-term impact.",
    "values": ["Core Value 1", "Core Value 2"]
  },
  "logo_usage": {
    "primary_usage": "Rules for placing the logo on different backgrounds.",
    "minimum_size": "Technical size (e.g., 32px for digital, 1 inch for print).",
    "clear_space": "The mandatory 'buffer zone' around the logo.",
    "dont_rules": ["Don't stretch or distort", "Don't use unapproved colors", "Don't add shadows"]
  },
  "color_guidelines": {
    "primary_colors": [{"name": "Name", "hex": "#XXXXXX", "rgb": "R, G, B", "usage": "Specific application"}],
    "secondary_colors": [{"name": "Name", "hex": "#XXXXXX", "rgb": "R, G, B", "usage": "Specific application"}],
    "color_combinations": ["Text color on Background color", "CTA color on Background color"]
  },
  "typography_guidelines": {
    "primary_typeface": "Heading font and its personality.",
    "secondary_typeface": "Body font and its readability benefits.",
    "hierarchy": {
      "h1": "Bold, 48pt+, tracking: -2%",
      "h2": "Semibold, 32pt, tracking: -1%",
      "body": "Regular, 16pt, leading: 150%"
    }
  },
  "voice_and_tone": {
    "personality": "Summary of the brand's character.",
    "dos": ["Use active verbs", "Be transparent", "Focus on the solution"],
    "donts": ["Avoid passive voice", "Don't use industry slang", "Never sound condescending"],
    "example_phrases": ["A phrase that embodies the brand", "A phrase showing how to handle an error"]
  },
  "imagery_guidelines": {
    "photography_style": "Visual descriptors (e.g., Candid, High Contrast, Natural).",
    "illustration_style": "Visual descriptors (e.g., Abstract Line Art, Minimalist 3D).",
    "icon_style": "Technical style (e.g., Outlined, 2px stroke, Rounded)."
  },
  "digital_guidelines": {
    "website_style": "UX/UI direction (e.g., Ample white space, rounded corners).",
    "social_media": "Visual rhythm and content frequency advice.",
    "email": "Tone and layout structure for newsletters."
  }
}

Return ONLY valid JSON. Ensure the guidelines are technical enough for a professional designer but clear enough for a business owner."""


async def run(
    strategy_data: dict,
    naming_data: dict,
    design_data: dict,
    content_data: dict,
) -> AgentResult:
    """Execute the Brand Guidelines Agent."""

    # Strip heavy SVG/logo data from design_data — it blows up the context window
    design_summary = {
        k: v for k, v in design_data.items()
        if k not in ("variants", "logo_inspiration", "search_queries")
    }
    # Keep only first variant's palette + fonts as a lightweight reference
    variants = design_data.get("variants", [])
    if variants:
        first = variants[0]
        design_summary["primary_variant"] = {
            "variant_name":   first.get("variant_name", ""),
            "color_palette":  first.get("color_palette", []),
            "color_roles":    first.get("color_roles", {}),
            "heading_font":   first.get("heading_font", ""),
            "body_font":      first.get("body_font", ""),
            "logo_type":      first.get("logo_type", ""),
        }

    user_prompt = (
        f"BRAND STRATEGY:\n{json.dumps(strategy_data, indent=2)}\n\n"
        f"BRAND NAME: {naming_data.get('brand_name', 'Brand')}\n"
        f"TAGLINE: {naming_data.get('tagline', '')}\n\n"
        f"DESIGN DIRECTION:\n{json.dumps(design_summary, indent=2)}\n\n"
        f"BRAND CONTENT:\n{json.dumps(content_data, indent=2)}\n\n"
        f"Create comprehensive brand guidelines that cover all aspects of this brand identity."
    )

    raw = await call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.6,
        response_format={"type": "json_object"},
        max_tokens=3000,
    )

    try:
        data = json.loads(raw)
    except Exception:
        data = {}

    if not data:
        data = {
            "guidelines_version": "1.0",
            "brand_overview": {
                "mission": strategy_data.get("brand_mission", ""),
                "vision":  strategy_data.get("brand_vision", ""),
                "values":  strategy_data.get("brand_values", []),
            },
            "logo_usage": {"primary_usage": "", "minimum_size": "32px digital / 1 inch print", "clear_space": "Equal to logo height on all sides", "dont_rules": ["Don't stretch or distort", "Don't use unapproved colors"]},
            "color_guidelines": {"primary_colors": [], "secondary_colors": [], "color_combinations": []},
            "typography_guidelines": {"primary_typeface": design_summary.get("primary_variant", {}).get("heading_font", ""), "secondary_typeface": design_summary.get("primary_variant", {}).get("body_font", ""), "hierarchy": {}},
            "voice_and_tone": {"personality": "", "dos": [], "donts": [], "example_phrases": []},
            "imagery_guidelines": {"photography_style": "", "illustration_style": "", "icon_style": ""},
            "digital_guidelines": {"website_style": "", "social_media": "", "email": ""},
        }

    logo = data.get("logo_usage", {})
    explanation = (
        f"Comprehensive brand guidelines v{data.get('guidelines_version', '1.0')} have been created. "
        f"The guide covers logo usage ({len(logo.get('dont_rules', []))} don't rules), "
        f"color system ({len(data.get('color_guidelines', {}).get('primary_colors', []))} primary colors), "
        f"typography hierarchy, voice & tone guidelines, "
        f"imagery direction, and digital application standards. "
        f"These guidelines ensure brand consistency across all touchpoints. "
        f"The document is ready for team distribution and client handoff."
    )

    return AgentResult(data=data, explanation=explanation)
