import json
from app.utils.gemini_search import call_gemini_with_search
from app.schemas.brand_schema import AgentResult

SYSTEM_PROMPT = """You are a Senior Market Intelligence Consultant and Trend Forecaster.
Use Google Search to find real-time market data. Your goal is to synthesize current search data into a high-fidelity market landscape, focusing heavily on competitive positioning and emerging cultural shifts.

ANALYSIS FRAMEWORK:
1. COMPETITIVE BENCHMARKING: Identify who is winning, who is losing, and why.
2. TREND VELOCITY: Distinguish between short-term fads and long-term structural shifts (2024-2027).
3. CONSUMER ANTHROPOLOGY: Why do people care about this idea? What emotional gap does it fill?

Your output must be a JSON object with EXACTLY these keys:
{
  "market_size": "Detailed estimate with CAGR and global vs. local outlook",
  "market_trends": ["Emerging Tech Trend", "Consumer Behavior Shift", "Sustainability/Regulatory Trend", "Cultural Movement"],
  "competitor_landscape": [
    {
      "name": "Direct or Indirect Competitor",
      "strength": "What they do well",
      "weakness": "Their vulnerability/gap",
      "market_share_vibe": "Leader, Challenger, or Niche player"
    }
  ],
  "target_demographics": {
    "primary_segment": "Detailed profile (Age, Income, Values)",
    "psychographics": ["Interests", "Aspirations", "Pain points"],
    "behavior_patterns": ["Buying habits", "Digital platforms they frequent"]
  },
  "market_gaps": ["Specific unmet need 1", "Service friction 2", "The 'White Space' opportunity"],
  "growth_drivers": ["Short-term catalyst", "Long-term scaling factor"],
  "key_sources": ["Specific report, news article, or platform used for data"]
}

Return ONLY valid JSON. Prioritize evidence-based insights over generic observations. Search for the latest 2024/2025 data."""

async def run(idea_data: dict) -> AgentResult:
    """Execute the Market Research Agent using Gemini with Google Search grounding."""
    refined_idea = idea_data.get("refined_idea", "")
    industry = idea_data.get("industry_category", "")
    problem = idea_data.get("problem_solved", "")

    user_prompt = (
        f"BRAND IDEA: {refined_idea}\n"
        f"INDUSTRY/CATEGORY: {industry}\n"
        f"CORE PROBLEM SOLVED: {problem}\n\n"
        f"Search the web for the latest 2024/2025 data on this market. "
        f"Identify the top 3-5 competitors, market size with CAGR, key trends, "
        f"target demographics, market gaps, and growth drivers. "
        f"Provide a comprehensive market analysis grounded in real search results."
    )

    raw = await call_gemini_with_search(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.4,
    )

    try:
        data = json.loads(raw)
    except Exception:
        data = {}

    # Ensure stable schema for UI even when model output is partial.
    data.setdefault("market_size", "Temporarily unavailable")
    data.setdefault("market_trends", [])
    data.setdefault("competitor_landscape", [])
    data.setdefault("target_demographics", {
        "primary_segment": "General audience",
        "psychographics": [],
        "behavior_patterns": [],
    })
    data.setdefault("market_gaps", [])
    data.setdefault("growth_drivers", [])
    data.setdefault("key_sources", [])

    comps = [c.get("name") for c in data.get("competitor_landscape", []) if isinstance(c, dict) and c.get("name")]
    trends = data.get("market_trends", []) if isinstance(data.get("market_trends", []), list) else []
    gaps = data.get("market_gaps", []) if isinstance(data.get("market_gaps", []), list) else []
    first_gap = gaps[0] if gaps else "general market whitespace"
    explanation = (
        f"Market analysis complete for '{industry}' via Gemini + Google Search. "
        f"Identified {len(comps)} key competitors: {', '.join(comps[:3])}. "
        f"The market size is valued at {data.get('market_size', 'TBD')}. "
        f"Current trends are driven by {', '.join(trends[:2]) if trends else 'emerging demand shifts'}. "
        f"A major gap was found in {first_gap}."
    )

    return AgentResult(data=data, explanation=explanation)
