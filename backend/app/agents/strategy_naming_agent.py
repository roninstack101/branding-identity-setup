"""
Combined Brand Strategy + Naming Agent
Single GPT-4o mini call replacing two separate sequential agents.
Naming depends on strategy, so doing both in one pass is natural and saves 1 API call.
"""
import json
from app.utils.llm import call_openai
from app.schemas.brand_schema import AgentResult


SYSTEM_PROMPT = """You are a Chief Brand Officer, Strategic Psychologist, and world-class Brand Naming Specialist.
Your task is to synthesize market data and competitor insights into a complete Brand Bible AND generate professional brand names — all in one pass.

PART 1 – BRAND STRATEGY:
1. THE VOID: Use competitor weaknesses to claim an emotional or visual territory no one owns.
2. JUNGIAN ARCHETYPES: Select a dominant archetype (The Rebel, The Sage, The Magician, etc.) for human consistency.
3. THE PROMISE: One high-stakes commitment that solves the core pain point.
4. HIERARCHY OF BENEFITS: Distinguish what the product DOES (Functional) vs. how it makes users FEEL (Emotional).

PART 2 – BRAND NAMING:
1. GROUNDED REALISM: Names must sound like established companies. Use Latin/Greek roots, portmanteaus, or evocative "Empty Vessel" names.
2. PHONETIC BREVITY: 1-3 syllables. Easy to pronounce globally.
3. SEMANTIC WEIGHT: Every name must have a deep connection to the strategy just defined.
4. AVOID: Names ending in '-ly', '-ify', or starting with 'Nex-', 'Gen-'.

Your output must be a JSON object with EXACTLY these two top-level keys:

{
  "brand_strategy": {
    "brand_mission": "A powerful, action-oriented statement focused on the impact today.",
    "brand_vision": "An aspirational 10-year goal for how the world changes because of this brand.",
    "brand_values": ["Value 1", "Value 2", "Value 3", "Value 4", "Value 5"],
    "brand_personality": {
      "archetype": "Primary Jungian Archetype",
      "tone_of_voice": "Specific adjectives (e.g., Irreverent and bold)",
      "traits": ["Distinctive Trait 1", "Distinctive Trait 2", "Distinctive Trait 3"]
    },
    "positioning_statement": "For [Target Segment], [Brand Name] is the [Category] that [Benefit] unlike [Competitors] because [Differentiator].",
    "unique_selling_proposition": "The one singular reason a customer chooses this brand over every other option.",
    "target_segments": [
      {
        "segment_name": "Specific Persona Name",
        "description": "Deep psychographic and demographic profile.",
        "priority": "primary"
      },
      {
        "segment_name": "Secondary Audience",
        "description": "Strategic expansion or niche group.",
        "priority": "secondary"
      }
    ],
    "brand_promise": "The unbreakable vow the brand makes to every customer.",
    "emotional_benefits": ["Internal feeling 1", "Status/Identity benefit 2", "Psychological relief 3"],
    "functional_benefits": ["Technical advantage 1", "Cost/Time saving 2", "Performance metric 3"]
  },
  "naming": {
    "brand_name": "The strongest, most boardroom-ready recommendation",
    "tagline": "A high-end, benefit-driven value proposition",
    "name_candidates": [
      {
        "name": "The Name",
        "rationale": "Deep linguistic and strategic reasoning.",
        "style": "Modern Abstract / Portmanteau / Real Word",
        "domain_suggestion": "Professional .com or .io availability estimate"
      }
    ],
    "naming_strategy": "Summary of the semantic pillars used",
    "brand_story_hook": "A one-sentence founding myth for why this name was chosen."
  }
}

Provide EXACTLY 6 name candidates. Return ONLY valid JSON. Ensure the strategy is defensible and the names sound established — not AI-generated."""


async def run(
    idea_data: dict,
    market_data: dict,
    competitor_data: dict,
) -> tuple[AgentResult, AgentResult]:
    """
    Execute combined Brand Strategy + Naming in a single GPT-4o mini call.
    Returns a tuple of (brand_strategy_result, naming_result).
    """
    user_prompt = (
        f"IDEA ANALYSIS:\n{json.dumps(idea_data, indent=2)}\n\n"
        f"MARKET RESEARCH:\n{json.dumps(market_data, indent=2)}\n\n"
        f"COMPETITOR ANALYSIS:\n{json.dumps(competitor_data, indent=2)}\n\n"
        f"First, create a comprehensive brand strategy. "
        f"Then, using that strategy, generate 6 realistic professional brand names. "
        f"Both strategy and naming must be grounded in the market and competitor data above."
    )

    raw = await call_openai(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.7,
        max_tokens=4096,
    )

    try:
        combined = json.loads(raw)
    except Exception:
        combined = {}

    # ── Split into brand_strategy result ────────────────────────────────
    strategy_data = combined.get("brand_strategy", {})
    if not isinstance(strategy_data, dict):
        strategy_data = {}

    personality = strategy_data.get("brand_personality", {})
    strategy_explanation = (
        f"Brand strategy developed. "
        f"Archetype: '{personality.get('archetype', 'The Innovator')}' "
        f"with a {personality.get('tone_of_voice', 'professional')} tone. "
        f"Core values: {', '.join(strategy_data.get('brand_values', [])[:4])}. "
        f"USP: {strategy_data.get('unique_selling_proposition', 'N/A')[:100]}. "
        f"Targets {len(strategy_data.get('target_segments', []))} market segments."
    )

    # ── Split into naming result ─────────────────────────────────────────
    naming_data = combined.get("naming", {})
    if not isinstance(naming_data, dict):
        naming_data = {}

    candidates = naming_data.get("name_candidates", [])
    naming_explanation = (
        f"Naming complete. Primary recommendation: '{naming_data.get('brand_name', 'N/A')}'. "
        f"Generated {len(candidates)} grounded candidates using strategy: "
        f"'{naming_data.get('naming_strategy', 'N/A')}'. "
        f"Tagline: '{naming_data.get('tagline', 'N/A')}'."
    )

    return (
        AgentResult(data=strategy_data, explanation=strategy_explanation),
        AgentResult(data=naming_data, explanation=naming_explanation),
    )
