"""
Combined Market Research + Competitor Analysis Agent
Single Gemini + Google Search call replacing two separate agents.
Saves 1 search grounding request ($0.035) per brand analysis run.
"""
import json
from app.utils.gemini_search import call_gemini_with_search
from app.schemas.brand_schema import AgentResult


SYSTEM_PROMPT = """You are a Senior Market Intelligence Consultant and Competitive Intelligence Analyst.
Use Google Search to find real-time data. Your goal is to deliver BOTH a full market landscape AND a competitor battlefield map in a single, comprehensive research pass.

RESEARCH FRAMEWORK:
1. MARKET ANALYSIS: Market size (TAM/SAM with CAGR), key trends (2024-2027), target demographics, market gaps, growth drivers.
2. COMPETITOR MAPPING: Direct competitors (same problem), indirect competitors (different solution), SWOT from the outside, vulnerability mapping (what customers hate about the top players).
3. TREND VELOCITY: Distinguish short-term fads from long-term structural shifts.

Your output must be a JSON object with EXACTLY these two top-level keys:

{
  "market_research": {
    "market_size": "Detailed estimate with CAGR and global vs. local outlook",
    "market_trends": ["Emerging Tech Trend", "Consumer Behavior Shift", "Sustainability/Regulatory Trend", "Cultural Movement"],
    "competitor_landscape": [
      {
        "name": "Competitor Name",
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
    "market_gaps": ["Specific unmet need 1", "Service friction 2", "The White Space opportunity"],
    "growth_drivers": ["Short-term catalyst", "Long-term scaling factor"],
    "key_sources": ["Specific report, news article, or platform used for data"]
  },
  "competitor_analysis": {
    "direct_competitors": [
      {
        "name": "Competitor Name",
        "description": "Strategic overview of their market offering",
        "strengths": ["Unique advantage 1", "Unique advantage 2"],
        "weaknesses": ["Vulnerability 1", "Vulnerability 2"],
        "estimated_market_share": "e.g., Dominant Leader (40%) or Niche Player (5%)",
        "website": "URL",
        "design_trends": {
          "color_palette": "Describe their dominant brand colors and emotional tone (e.g., 'bold reds and blacks — aggressive, high-energy')",
          "typography_style": "Describe their font choices (e.g., 'geometric sans-serif for modernity, heavy weights for authority')",
          "logo_style": "Describe their logo type and style (e.g., 'wordmark with custom letterforms, minimalist icon mark')",
          "visual_language": "Overall design aesthetic (e.g., 'flat design, whitespace-heavy, photo-forward')",
          "design_differentiation": "What makes their visual identity stand out or feel dated"
        }
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
    "threat_level": "low | medium | high",
    "industry_design_trends": {
      "dominant_styles": ["Most common visual style in this industry", "Secondary aesthetic trend"],
      "color_trends": "Industry-wide color palette trends (e.g., 'earthy tones replacing neon in wellness brands')",
      "typography_trends": "Font trends across the industry (e.g., 'variable fonts and humanist sans replacing rigid geometric types')",
      "design_white_space": "Visual design directions that NO major competitor has claimed yet — opportunity to differentiate visually"
    }
  }
}

Return ONLY valid JSON. Search for the latest 2024/2025 data. Prioritize evidence-based insights."""


async def run(idea_data: dict) -> tuple[AgentResult, AgentResult]:
    """
    Execute the combined Market Research + Competitor Analysis in a single Gemini call.
    Returns a tuple of (market_research_result, competitor_analysis_result).
    """
    refined_idea   = idea_data.get("refined_idea", "")
    industry       = idea_data.get("industry_category", "")
    problem        = idea_data.get("problem_solved", "")
    business_model = idea_data.get("business_model", "")
    differentiators = idea_data.get("key_differentiators", [])
    competitors_hint = idea_data.get("competitive_context", "")
    audience = idea_data.get("target_audience", {})
    primary_audience = audience.get("primary", "") if isinstance(audience, dict) else str(audience)
    geography = audience.get("geography", "Global") if isinstance(audience, dict) else "Global"

    user_prompt = (
        f"BRAND IDEA: {refined_idea}\n"
        f"INDUSTRY/CATEGORY: {industry}\n"
        f"BUSINESS MODEL: {business_model}\n"
        f"CORE PROBLEM SOLVED: {problem}\n"
        f"PRIMARY AUDIENCE: {primary_audience}\n"
        f"TARGET GEOGRAPHY: {geography}\n"
        f"KEY DIFFERENTIATORS: {', '.join(differentiators)}\n"
        f"KNOWN COMPETITORS (from idea brief): {competitors_hint}\n\n"
        f"Search the web for the latest 2024/2025 data on this market and its competitors. "
        f"Identify market size with CAGR, key trends, top 3-5 direct competitors with their "
        f"strengths/weaknesses, indirect competitors, target demographics, market gaps, "
        f"and what customers hate about existing solutions. "
        f"For each direct competitor, also analyze their VISUAL DESIGN IDENTITY: brand colors and "
        f"emotional tone, typography choices, logo style, overall visual language, and what makes "
        f"their design stand out or feel dated. "
        f"Finally, identify industry-wide design trends and any visual white space (design directions "
        f"no competitor has claimed) that could be a differentiation opportunity."
    )

    raw = await call_gemini_with_search(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.4,
    )

    try:
        combined = json.loads(raw)
        print(f"[market_competitor_agent] Parsed OK — keys: {list(combined.keys())}")
        ca = combined.get("competitor_analysis", {})
        print(f"[market_competitor_agent] direct_competitors count: {len(ca.get('direct_competitors', []))}")
    except Exception as exc:
        print(f"[market_competitor_agent] JSON parse failed: {exc} | raw[:300]: {raw[:300]}")
        combined = {}

    # ── Split into market_research result ───────────────────────────────
    mr_data = combined.get("market_research", {})
    if not isinstance(mr_data, dict):
        mr_data = {}

    mr_data.setdefault("market_size", "Temporarily unavailable")
    mr_data.setdefault("market_trends", [])
    mr_data.setdefault("competitor_landscape", [])
    mr_data.setdefault("target_demographics", {
        "primary_segment": "General audience",
        "psychographics": [],
        "behavior_patterns": [],
    })
    mr_data.setdefault("market_gaps", [])
    mr_data.setdefault("growth_drivers", [])
    mr_data.setdefault("key_sources", [])

    comps = [c.get("name") for c in mr_data.get("competitor_landscape", []) if isinstance(c, dict) and c.get("name")]
    trends = mr_data.get("market_trends", [])
    gaps = mr_data.get("market_gaps", [])
    mr_explanation = (
        f"Market analysis complete for '{industry}' via Gemini + Google Search. "
        f"Identified {len(comps)} key competitors: {', '.join(comps[:3])}. "
        f"Market size: {mr_data.get('market_size', 'TBD')}. "
        f"Trends: {', '.join(trends[:2]) if trends else 'emerging demand shifts'}. "
        f"Key gap: {gaps[0] if gaps else 'general market whitespace'}."
    )

    # ── Split into competitor_analysis result ────────────────────────────
    ca_data = combined.get("competitor_analysis", {})
    if not isinstance(ca_data, dict):
        ca_data = {}

    direct = ca_data.get("direct_competitors", [])
    ca_explanation = (
        f"Competitor analysis via Gemini + Google Search identified {len(direct)} direct competitor(s) "
        f"in the {industry} space. "
        f"Competitive advantages: {', '.join(ca_data.get('competitive_advantages', [])[:3])}. "
        f"Threat level: {ca_data.get('threat_level', 'medium')}. "
        f"Positioning: {ca_data.get('recommended_positioning', 'differentiate on innovation')}."
    )

    return (
        AgentResult(data=mr_data, explanation=mr_explanation),
        AgentResult(data=ca_data, explanation=ca_explanation),
    )
