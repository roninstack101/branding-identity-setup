"""
Agent 4 – Brand Strategy Agent
Synthesizes idea discovery, market research, and competitor analysis
into a coherent brand strategy.
"""
import json
from app.utils.llm import call_openai
from app.schemas.brand_schema import AgentResult


SYSTEM_PROMPT = """You are a Chief Brand Officer and Strategic Psychologist. 
Your task is to synthesize raw market data, competitor weaknesses, and business ideas into a "Brand Bible" that defines the soul and competitive advantage of the company.

CORE STRATEGIC GUIDELINES:
1. THE VOID: Use the 'Competitor Analysis' to find a visual or emotional 'void' in the market. The strategy should claim that empty territory.
2. JUNGian ARCHETYPES: Select a dominant archetype (e.g., The Rebel, The Sage, The Magician) to ensure the brand personality feels human and consistent.
3. THE PROMISE: The Brand Promise must be a singular, high-stakes commitment that solves the core 'pain point' identified in the Market Research.
4. HIERARCHY OF BENEFITS: Distinguish clearly between what the product DOES (Functional) and how it makes the user FEEL (Emotional).

Your output must be a JSON object with EXACTLY these keys:
{
  "brand_mission": "A powerful, action-oriented statement focused on the impact today.",
  "brand_vision": "An aspirational 10-year goal for how the world changes because of this brand.",
  "brand_values": ["Uncompromising Value 1", "Uncompromising Value 2", "Uncompromising Value 3", "Uncompromising Value 4", "Uncompromising Value 5"],
  "brand_personality": {
    "archetype": "Primary Jungian Archetype",
    "tone_of_voice": "Specific adjectives (e.g., 'Irreverent and bold' or 'Calm and authoritative')",
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
}

Return ONLY valid JSON. Ensure the strategy is 'Defensible'—meaning it specifically addresses the gaps left by competitors."""

async def run(
    idea_data: dict,
    market_data: dict,
    competitor_data: dict,
) -> AgentResult:
    """Execute the Brand Strategy Agent."""
    user_prompt = (
        f"IDEA ANALYSIS:\n{json.dumps(idea_data, indent=2)}\n\n"
        f"MARKET RESEARCH:\n{json.dumps(market_data, indent=2)}\n\n"
        f"COMPETITOR ANALYSIS:\n{json.dumps(competitor_data, indent=2)}\n\n"
        f"Based on ALL the above inputs, create a comprehensive brand strategy."
    )

    raw = await call_openai(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.7,
    )

    data = json.loads(raw)

    personality = data.get("brand_personality", {})
    explanation = (
        f"A comprehensive brand strategy has been developed. "
        f"The brand archetype is '{personality.get('archetype', 'The Innovator')}' "
        f"with a {personality.get('tone_of_voice', 'professional')} tone. "
        f"Core values: {', '.join(data.get('brand_values', [])[:4])}. "
        f"The positioning statement: {data.get('positioning_statement', 'N/A')[:100]}. "
        f"USP: {data.get('unique_selling_proposition', 'N/A')[:100]}. "
        f"The strategy targets {len(data.get('target_segments', []))} market segments."
    )

    return AgentResult(data=data, explanation=explanation)
