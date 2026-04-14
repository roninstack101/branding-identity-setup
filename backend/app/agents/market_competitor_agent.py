"""
Combined Market Research + Competitor Analysis Agent
Uses Serper.dev for real Google search results, then Groq (Llama) to analyze
them into structured JSON. Replaces Gemini Search Grounding.
"""
import json
from app.utils.serper_search import serper_multi_search
from app.utils.llm import call_llm
from app.schemas.brand_schema import AgentResult


ANALYSIS_SYSTEM_PROMPT = """You are a Senior Market Intelligence Consultant and Competitive Intelligence Analyst.
You will be given real Google search results about a specific business/industry. Analyze them and return structured JSON.

CRITICAL RULES:
- Only include companies that are in the EXACT same industry and geography as specified.
- If the business is a fintech lender, competitors must be other lenders/NBFCs — NOT retailers or consumer brands.
- Base your analysis ONLY on the search results provided. Do not hallucinate companies or data.
- For design trends, describe what you know about the competitor's visual identity from search results.

Your output must be a JSON object with EXACTLY these two top-level keys:

{
  "market_research": {
    "market_size": "Estimated market size with CAGR based on search results",
    "market_trends": ["Trend 1 from search results", "Trend 2", "Trend 3", "Trend 4"],
    "competitor_landscape": [
      {
        "name": "Competitor Name",
        "strength": "What they do well",
        "weakness": "Their gap",
        "market_share_vibe": "Leader / Challenger / Niche"
      }
    ],
    "target_demographics": {
      "primary_segment": "Detailed profile",
      "psychographics": ["Interest 1", "Interest 2"],
      "behavior_patterns": ["Pattern 1", "Pattern 2"]
    },
    "market_gaps": ["Gap 1", "Gap 2", "Gap 3"],
    "growth_drivers": ["Driver 1", "Driver 2"],
    "key_sources": ["Source from search results 1", "Source 2"]
  },
  "competitor_analysis": {
    "direct_competitors": [
      {
        "name": "Competitor Name",
        "description": "What they do and who they serve",
        "strengths": ["Strength 1", "Strength 2"],
        "weaknesses": ["Weakness 1", "Weakness 2"],
        "estimated_market_share": "e.g., Market Leader or Niche Player",
        "website": "URL if found in search results",
        "design_trends": {
          "color_palette": "Describe their brand colors and tone",
          "typography_style": "Describe their font choices",
          "logo_style": "Describe their logo type",
          "visual_language": "Overall design aesthetic",
          "design_differentiation": "What makes their design stand out or feel dated"
        }
      }
    ],
    "indirect_competitors": [
      {
        "name": "Competitor Name",
        "description": "How they compete indirectly"
      }
    ],
    "competitive_advantages": ["Advantage 1", "Advantage 2", "Advantage 3"],
    "market_positioning_gaps": ["Gap 1", "Gap 2"],
    "recommended_positioning": "2-sentence positioning recommendation.",
    "threat_level": "low | medium | high",
    "industry_design_trends": {
      "dominant_styles": ["Most common visual style", "Secondary style"],
      "color_trends": "Industry-wide color trends",
      "typography_trends": "Font trends in this industry",
      "design_white_space": "Visual directions no competitor has claimed"
    }
  }
}

Return ONLY valid JSON. No markdown, no extra text."""


async def run(idea_data: dict) -> tuple[AgentResult, AgentResult]:
    """
    Execute combined Market Research + Competitor Analysis.
    1. Search Google via Serper for real data
    2. Analyze with Groq into structured JSON
    Returns (market_research_result, competitor_analysis_result).
    """
    refined_idea    = idea_data.get("refined_idea", "")
    industry        = idea_data.get("industry_category", "")
    business_model  = idea_data.get("business_model", "")
    problem         = idea_data.get("problem_solved", "")
    audience        = idea_data.get("target_audience", {})
    primary_audience = audience.get("primary", "") if isinstance(audience, dict) else str(audience)
    geography       = audience.get("geography", "Global") if isinstance(audience, dict) else "Global"
    competitors_hint = idea_data.get("competitive_context", "")

    # Build targeted search queries
    search_queries = [
        f"{industry} {geography} market size 2024 2025",
        f"{industry} {geography} top companies competitors",
        f"{industry} {geography} market trends growth",
    ]
    if competitors_hint:
        search_queries.append(f"{competitors_hint} {geography}")
    else:
        search_queries.append(f"{industry} {geography} leading companies")

    print(f"[market_competitor_agent] Searching: {search_queries}")
    search_results = await serper_multi_search(search_queries, num_per_query=8)
    print(f"[market_competitor_agent] Got {len(search_results)} search results")

    # Format search results for the LLM
    if search_results:
        results_text = "\n\n".join([
            f"[{i+1}] {r['title']}\n{r['link']}\n{r['snippet']}"
            for i, r in enumerate(search_results[:30])  # cap at 30 to stay in context
        ])
    else:
        results_text = "No search results available. Use your knowledge to provide best-effort analysis."

    user_prompt = (
        f"INDUSTRY: {industry}\n"
        f"GEOGRAPHY: {geography}\n"
        f"BUSINESS MODEL: {business_model}\n"
        f"BUSINESS: {refined_idea}\n"
        f"AUDIENCE: {primary_audience}\n"
        f"PROBLEM: {problem}\n\n"
        f"GOOGLE SEARCH RESULTS:\n{results_text}\n\n"
        f"Analyze the search results above and return market research + competitor analysis JSON. "
        f"Only include competitors from {industry} in {geography}."
    )

    raw = await call_llm(
        system_prompt=ANALYSIS_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=4096,
    )

    try:
        # Strip markdown fences if present
        import re
        clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw.strip(), flags=re.MULTILINE)
        combined = json.loads(clean)
        ca = combined.get("competitor_analysis", {})
        mr = combined.get("market_research", {})
        print(f"[market_competitor_agent] Parsed OK | industry={industry} | geography={geography}")
        print(f"[market_competitor_agent] direct_competitors: {[c.get('name') for c in ca.get('direct_competitors', [])]}")
        print(f"[market_competitor_agent] market_size: {mr.get('market_size', 'N/A')[:80]}")
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
        "primary_segment": primary_audience or "General audience",
        "psychographics": [],
        "behavior_patterns": [],
    })
    mr_data.setdefault("market_gaps", [])
    mr_data.setdefault("growth_drivers", [])
    mr_data.setdefault("key_sources", [])

    comps  = [c.get("name") for c in mr_data.get("competitor_landscape", []) if isinstance(c, dict) and c.get("name")]
    trends = mr_data.get("market_trends", [])
    gaps   = mr_data.get("market_gaps", [])
    mr_explanation = (
        f"Market analysis for '{industry}' via Serper + Groq. "
        f"Identified {len(comps)} key players: {', '.join(comps[:3])}. "
        f"Market size: {mr_data.get('market_size', 'TBD')}. "
        f"Trends: {', '.join(trends[:2]) if trends else 'emerging demand shifts'}. "
        f"Key gap: {gaps[0] if gaps else 'general market whitespace'}."
    )

    # ── Split into competitor_analysis result ────────────────────────────
    ca_data = combined.get("competitor_analysis", {})
    if not isinstance(ca_data, dict):
        ca_data = {}

    ca_data.setdefault("direct_competitors", [])
    ca_data.setdefault("indirect_competitors", [])
    ca_data.setdefault("competitive_advantages", [])
    ca_data.setdefault("market_positioning_gaps", [])
    ca_data.setdefault("recommended_positioning", "")
    ca_data.setdefault("threat_level", "medium")
    ca_data.setdefault("industry_design_trends", {})

    direct = ca_data.get("direct_competitors", [])
    ca_explanation = (
        f"Competitor analysis identified {len(direct)} direct competitor(s) in {industry} / {geography}. "
        f"Competitive advantages: {', '.join(ca_data.get('competitive_advantages', [])[:2])}. "
        f"Threat level: {ca_data.get('threat_level', 'medium')}."
    )

    return (
        AgentResult(data=mr_data, explanation=mr_explanation),
        AgentResult(data=ca_data, explanation=ca_explanation),
    )
