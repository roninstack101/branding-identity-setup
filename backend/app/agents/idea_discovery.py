"""
Agent 1 – Idea Discovery Agent
Refines and expands the raw user idea into a structured concept.
"""
import json
from app.utils.llm import call_llm
from app.schemas.brand_schema import AgentResult


SYSTEM_PROMPT = """You are a Senior Market Intelligence Consultant. Your goal is to validate the business idea against real-world 2024-2025 market trends and identify the "Total Addressable Market" (TAM).

RESEARCH FRAMEWORK:
1. PESTEL Analysis: Briefly consider Political, Economic, Social, Technological, Environmental, and Legal factors.
2. Market Maturity: Is this a "Red Ocean" (saturated) or "Blue Ocean" (new)?
3. Trend Velocity: Are the core technologies or behaviors behind this idea rising or declining?

Your output must be a JSON object with EXACTLY these keys:
{
  "market_size": "Estimated TAM/SAM/SOM or general market scale (e.g., $10B Global Market)",
  "current_trends": ["Macro trend 1", "Industry-specific trend 2", "Consumer behavior shift 3"],
  "target_demographics": "Detailed breakdown of the most profitable user segment",
  "market_gaps": ["Unmet need 1", "Underserved niche 2"],
  "growth_drivers": ["Factor accelerating adoption 1", "Factor 2"],
  "regulatory_landscape": "Potential legal or compliance hurdles",
  "swot_analysis": {
    "strengths": ["Internal advantage 1"],
    "weaknesses": ["Internal limitation 1"],
    "opportunities": ["External growth factor 1"],
    "threats": ["External risk factor 1"]
  }
}

Return ONLY valid JSON. Use the provided web search context to ground your findings in reality."""


async def run(idea: str) -> AgentResult:
    """Execute the Idea Discovery Agent."""
    user_prompt = f"Analyze and expand this business idea:\n\n{idea}"

    raw = await call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.7,
        response_format={"type": "json_object"},
    )

    data = json.loads(raw)

    explanation = (
        f"The idea '{idea[:60]}...' has been analyzed and refined. "
        f"The concept targets {data.get('target_audience', 'a broad audience')} "
        f"within the {data.get('industry_category', 'general')} industry. "
        f"The core value proposition centers on {data.get('value_proposition', 'delivering unique value')}. "
        f"Key differentiators include {', '.join(data.get('key_differentiators', [])[:3])}. "
        f"The idea primarily solves: {data.get('problem_solved', 'an identified market gap')}. "
        f"Potential revenue can be driven through {data.get('revenue_model', 'various channels')}."
    )

    return AgentResult(data=data, explanation=explanation)
