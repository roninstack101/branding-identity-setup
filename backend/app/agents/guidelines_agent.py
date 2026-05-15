"""
Agent 9 – Brand Guidelines Agent
Synthesizes all outputs into a comprehensive brand guidelines document.
"""
import json
from app.utils.llm import call_llm
from app.schemas.brand_schema import AgentResult


SYSTEM_PROMPT = """You are a Principal Brand Consultant and Design Systems Architect. Your goal is to codify the brand's identity into a "Rulebook" that ensures absolute consistency across all physical and digital touchpoints.

GUIDELINE PRINCIPLES:
1. LOGO INTEGRITY: Define strict rules for clear space, minimum size, and misuse.
2. COLOR PRECISION: Provide hex codes, usage logic, and accessibility (WCAG compliance).
3. COLOR & FONT RATIONALE: Explain WHY these specific colours and typefaces were chosen for THIS brand — psychology, competitor differentiation, target audience affinity.
4. BRAND RULES: 6 high-level governance rules that protect the brand's integrity in any situation.
5. VOICE CODIFICATION: Turn the tone of voice into concrete dos/don'ts a non-designer can follow.
6. TYPOGRAPHIC HIERARCHY: A clear scale developers and designers can implement immediately.

Your output must be a JSON object with EXACTLY these keys:
{
  "guidelines_version": "1.0",
  "brand_overview": {
    "mission": "The brand's driving force — pulled from the content brief.",
    "vision": "The long-term world-building aspiration.",
    "values": ["Core Value 1", "Core Value 2", "Core Value 3"]
  },
  "logo_usage": {
    "primary_usage": "Rules for placing the logo on different backgrounds.",
    "minimum_size": "Technical size (e.g., 32px digital / 1 inch print).",
    "clear_space": "The mandatory buffer zone around the logo.",
    "dont_rules": ["Don't stretch or distort", "Don't use unapproved colors", "Don't add shadows or effects", "Don't place on busy backgrounds"]
  },
  "color_guidelines": {
    "primary_colors": [{"name": "Color Name", "hex": "#XXXXXX", "rgb": "R, G, B", "usage": "Specific application context"}],
    "secondary_colors": [{"name": "Color Name", "hex": "#XXXXXX", "rgb": "R, G, B", "usage": "Specific application context"}],
    "color_combinations": ["Safe pairing 1 (text on background)", "Safe pairing 2", "Safe pairing 3"]
  },
  "color_rationale": {
    "primary_reasoning": "Why THIS specific primary color was chosen — psychological associations, emotional triggers, competitor landscape differentiation, and target audience resonance.",
    "accent_reasoning": "Why THIS accent color was chosen — its complementary role, the contrast it creates, and the emotional note it adds to the brand.",
    "palette_harmony": "How the full palette works together as a system — the mood it collectively creates and why it fits this brand's positioning."
  },
  "typography_guidelines": {
    "primary_typeface": "Heading font name and its personality description.",
    "secondary_typeface": "Body font name and its readability rationale.",
    "hierarchy": {
      "h1": "Bold, 48pt+, tracking: -2%",
      "h2": "Semibold, 32pt, tracking: -1%",
      "h3": "Semibold, 24pt",
      "body": "Regular, 16pt, leading: 150%",
      "caption": "Regular, 12pt, tracking: +2%",
      "label": "Bold, 10pt, ALL CAPS, tracking: +15%"
    }
  },
  "typography_rationale": {
    "heading_font_reason": "Why this heading typeface fits THIS brand — personality match, industry context, scalability at large sizes, and the first impression it creates.",
    "body_font_reason": "Why this body font pairs well — readability at small sizes, digital-first optimisation, brand voice alignment, and why it complements the heading font.",
    "combination_logic": "How and why these two typefaces work together — the tension or harmony they create, and what it says about the brand's character."
  },
  "brand_rules": [
    {
      "rule_number": 1,
      "rule": "Short rule name (3-5 words)",
      "description": "What this rule requires in practice.",
      "why": "Why this rule exists and what it protects about the brand's integrity."
    },
    {
      "rule_number": 2,
      "rule": "Short rule name",
      "description": "What this rule requires in practice.",
      "why": "Why this rule exists."
    },
    {
      "rule_number": 3,
      "rule": "Short rule name",
      "description": "What this rule requires in practice.",
      "why": "Why this rule exists."
    },
    {
      "rule_number": 4,
      "rule": "Short rule name",
      "description": "What this rule requires in practice.",
      "why": "Why this rule exists."
    },
    {
      "rule_number": 5,
      "rule": "Short rule name",
      "description": "What this rule requires in practice.",
      "why": "Why this rule exists."
    },
    {
      "rule_number": 6,
      "rule": "Short rule name",
      "description": "What this rule requires in practice.",
      "why": "Why this rule exists."
    }
  ],
  "voice_and_tone": {
    "personality": "Summary of the brand's character in writing.",
    "dos": ["Use active verbs", "Be transparent", "Lead with customer benefit", "Use specific examples"],
    "donts": ["Avoid passive voice", "Never use jargon without explanation", "Don't sound condescending", "Avoid empty superlatives"],
    "example_phrases": ["A phrase that embodies the brand voice", "A phrase showing how to handle a complaint in brand voice"]
  },
  "imagery_guidelines": {
    "photography_style": "Visual descriptors (e.g., Candid, High Contrast, Natural Light).",
    "illustration_style": "Visual descriptors (e.g., Abstract Line Art, Minimalist 3D).",
    "icon_style": "Technical style (e.g., Outlined, 2px stroke, Rounded corners)."
  },
  "digital_guidelines": {
    "website_style": "UX/UI direction (e.g., Ample white space, 8px grid, rounded corners).",
    "social_media": "Visual rhythm and content frequency advice.",
    "email": "Tone and layout structure for newsletters and transactional emails."
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

    # Strip heavy data that blows up the context window
    design_summary = {
        k: v for k, v in design_data.items()
        if k not in ("variants", "logo_inspiration", "search_queries", "design_concepts")
    }
    variants = design_data.get("variants", [])
    if variants:
        first = variants[0]
        design_summary["primary_variant"] = {
            "variant_name":  first.get("variant_name", ""),
            "color_palette": first.get("color_palette", []),
            "heading_font":  first.get("heading_font", ""),
            "body_font":     first.get("body_font", ""),
        }

    # Pull mission/vision from content agent if available
    mission = content_data.get("mission_statement", strategy_data.get("brand_mission", ""))
    vision  = content_data.get("vision_statement",  strategy_data.get("brand_vision",  ""))

    user_prompt = (
        f"BRAND STRATEGY:\n{json.dumps(strategy_data, indent=2)}\n\n"
        f"BRAND NAME: {naming_data.get('brand_name', 'Brand')}\n"
        f"TAGLINE: {naming_data.get('tagline', '')}\n"
        f"MISSION: {mission}\n"
        f"VISION:  {vision}\n\n"
        f"DESIGN DIRECTION (colours, fonts, style):\n{json.dumps(design_summary, indent=2)}\n\n"
        f"BRAND CONTENT (tone, pillars, about):\n{json.dumps(content_data, indent=2)}\n\n"
        f"Create comprehensive brand guidelines with full rationale for all design decisions."
    )

    raw = await call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.6,
        response_format={"type": "json_object"},
        max_tokens=4000,
    )

    try:
        data = json.loads(raw)
    except Exception:
        data = {}

    if not data:
        data = {
            "guidelines_version": "1.0",
            "brand_overview": {
                "mission": mission,
                "vision":  vision,
                "values":  strategy_data.get("brand_values", []),
            },
            "logo_usage": {
                "primary_usage": "",
                "minimum_size":  "32px digital / 1 inch print",
                "clear_space":   "Equal to logo height on all sides",
                "dont_rules":    ["Don't stretch or distort", "Don't use unapproved colors", "Don't add effects", "Don't place on busy backgrounds"],
            },
            "color_guidelines":   {"primary_colors": [], "secondary_colors": [], "color_combinations": []},
            "color_rationale":    {"primary_reasoning": "", "accent_reasoning": "", "palette_harmony": ""},
            "typography_guidelines": {
                "primary_typeface":   design_summary.get("primary_variant", {}).get("heading_font", ""),
                "secondary_typeface": design_summary.get("primary_variant", {}).get("body_font", ""),
                "hierarchy": {},
            },
            "typography_rationale": {"heading_font_reason": "", "body_font_reason": "", "combination_logic": ""},
            "brand_rules":        [],
            "voice_and_tone":     {"personality": "", "dos": [], "donts": [], "example_phrases": []},
            "imagery_guidelines": {"photography_style": "", "illustration_style": "", "icon_style": ""},
            "digital_guidelines": {"website_style": "", "social_media": "", "email": ""},
        }

    rules = data.get("brand_rules", [])
    explanation = (
        f"Comprehensive brand guidelines v{data.get('guidelines_version', '1.0')} created. "
        f"{len(rules)} brand rules defined. "
        f"Includes color rationale (why {naming_data.get('brand_name', 'the brand')} chose its palette), "
        f"typography rationale, logo usage rules, voice & tone codification, "
        f"imagery direction, and digital application standards."
    )

    return AgentResult(data=data, explanation=explanation)
