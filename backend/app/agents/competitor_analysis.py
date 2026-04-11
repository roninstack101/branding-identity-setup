"""
Agent 3 – Competitor Analysis Agent
Uses Gemini + Google Search grounding to identify and analyze competitors in real time.
Runs IN PARALLEL with Market Research Agent.
"""
import json
from app.utils.gemini_search import call_gemini_with_search
from app.schemas.brand_schema import AgentResult


SYSTEM_PROMPT = """You are a Senior Competitive Intelligence Analyst. Use Google Search to find real-time competitor data. Your goal is to map the "Battlefield" for this business idea by deconstructing the existing players and finding the "Line of Least Resistance" for entry.

ANALYTICAL FRAMEWORK:
1. DIRECT VS. INDIRECT: Distinguish between those who solve the SAME problem (Direct) and those who solve the same problem DIFFERENTLY (Indirect).
2. SWOT FROM THE OUTSIDE: Identify strengths/weaknesses based on search results, user reviews, and pricing transparency.
3. FEATURE FATIGUE: Look for competitors that have become too complex, leaving room for a simpler, "cleaner" alternative.
4. VULNERABILITY MAPPING: Specifically identify what customers HATE about the top 3 competitors (e.g., bad support, high price, outdated UI).

Your output must be a JSON object with EXACTLY these keys:
{
  "direct_competitors": [
    {
      "name": "Competitor Name",
      "description": "Strategic overview of their market offering",
      "strengths": ["Unique advantage 1", "Unique advantage 2"],
      "weaknesses": ["Vulnerability 1", "Vulnerability 2"],
      "estimated_market_share": "e.g., Dominant Leader (40%) or Niche Player (5%)",
      "website": "URL"
    }
  ],
  "indirect_competitors": [
    {
      "name": "Competitor Name",
      "description": "How their alternative solution steals customer attention"
    }
  ],
  "competitive_advantages": ["Unfair advantage 1", "Moat opportunity 2", "Cost/Speed benefit 3"],
  "market_positioning_gaps": ["Underserved customer segment", "Missing feature set", "Pricing vacuum"],
  "recommended_positioning": "A 2-sentence tactical recommendation on how to pivot away from competitor strengths.",
  "threat_level": "low | medium | high"
}

Return ONLY valid JSON. Focus on identifying 'Vulnerabilities' that the new brand can exploit. Search for the most current competitor data available."""

async def run(idea_data: dict) -> AgentResult:
    """Execute the Competitor Analysis Agent using Gemini with Google Search grounding."""
    refined_idea = idea_data.get("refined_idea", "")
    industry = idea_data.get("industry_category", "")

    user_prompt = (
        f"Refined Idea: {refined_idea}\n"
        f"Industry: {industry}\n\n"
        f"Search the web for the top direct and indirect competitors in this space. "
        f"Find their strengths, weaknesses, pricing, and what customers complain about. "
        f"Produce a comprehensive competitor analysis with vulnerability mapping."
    )

    raw = await call_gemini_with_search(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.5,
    )

    try:
        data = json.loads(raw)
    except Exception:
        data = {}

    direct = data.get("direct_competitors", [])
    explanation = (
        f"Competitor analysis via Gemini + Google Search identified {len(direct)} direct competitor(s) "
        f"in the {industry} space. "
        f"Key competitive advantages for this idea include: "
        f"{', '.join(data.get('competitive_advantages', [])[:3])}. "
        f"The overall threat level is assessed as {data.get('threat_level', 'medium')}. "
        f"Recommended positioning: {data.get('recommended_positioning', 'differentiate on innovation')}. "
        f"Market positioning gaps found: {', '.join(data.get('market_positioning_gaps', [])[:2])}."
    )

    return AgentResult(data=data, explanation=explanation)
