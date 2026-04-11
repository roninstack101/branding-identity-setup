"""
Agent 1 – Idea Discovery Agent
Extracts and structures all key details from the user's raw idea prompt.
Output feeds directly into market_competitor_agent, strategy_naming_agent, and visual_identity_agent.
"""
import json
import re
from app.utils.llm import call_llm
from app.schemas.brand_schema import AgentResult


SYSTEM_PROMPT = """You are an expert Business Analyst and Brand Strategist. Your job is to deeply parse a raw business idea — no matter how short or long — and extract every meaningful detail into a structured brief that other AI agents will use downstream.

EXTRACTION FRAMEWORK:
1. READ BETWEEN THE LINES: If the user says "Uber for dogs", extract the industry (pet services), model (marketplace/on-demand), audience (pet owners), problem (finding reliable dog care), etc.
2. INFER WHAT'S MISSING: If the user doesn't mention a revenue model, infer the most likely one. If they don't name the audience, derive it from the problem.
3. BE SPECIFIC: Never use vague placeholders like "general audience" or "various industries". Always commit to a specific, defensible answer.
4. PRESERVE UNIQUE DETAILS: If the user mentions a location, technology, niche, or constraint — capture it exactly.

Your output must be a JSON object with EXACTLY these keys:

{
  "original_brand_name": "The exact business/brand name the user mentioned in their idea, or null if they did not mention one. Extract it precisely — do not modify, translate, or invent a name.",
  "refined_idea": "A 2-3 sentence restatement of the idea in professional, clear language. Captures the what, who, and why.",
  "industry_category": "The specific industry vertical (e.g., 'B2B SaaS / HR Tech', 'D2C Health & Wellness', 'Marketplace / Gig Economy')",
  "business_model": "The core business model (e.g., 'Subscription SaaS', 'Marketplace with commission', 'D2C e-commerce', 'Freemium mobile app')",
  "problem_solved": "The single most painful problem this idea solves — be specific and human (e.g., 'Freelancers waste 6+ hours/week chasing invoices with no automated solution')",
  "target_audience": {
    "primary": "Specific primary persona (Age range, job title or life situation, key trait)",
    "secondary": "Secondary audience who also benefits",
    "geography": "Target geography — infer from context or default to 'Global / English-speaking markets'"
  },
  "value_proposition": "The core promise in one sentence: what the customer gets that they can't easily get elsewhere",
  "key_differentiators": [
    "Specific differentiator 1 — what makes this unlike existing solutions",
    "Specific differentiator 2",
    "Specific differentiator 3"
  ],
  "revenue_model": "How the business makes money (e.g., '$29/mo subscription + enterprise tier', '15% marketplace commission', 'Freemium with paid add-ons')",
  "core_features": [
    "Essential feature or capability 1",
    "Essential feature or capability 2",
    "Essential feature or capability 3",
    "Essential feature or capability 4"
  ],
  "brand_tone_hints": "Words the user used (or implied) that hint at brand personality — e.g., 'smart, approachable, no-nonsense' or 'premium, aspirational, exclusive'",
  "competitive_context": "What existing solutions does this compete with? Name 2-3 if obvious (e.g., 'Competes with Notion, Confluence, and Google Docs')",
  "unique_insight": "The single sharpest observation about why this idea can win — the non-obvious angle that most people would miss"
}

CRITICAL RULES:
- Never return empty strings or null values. Always make an informed inference.
- If the idea is very short (e.g., "an app for dog walkers"), expand it intelligently using your knowledge.
- If the idea is long and detailed, distill it — don't just copy-paste.
- INDUSTRY CLASSIFICATION RULE: Classify the industry based on WHAT THE COMPANY DOES, not who its customers are.
  Example: A company that LENDS MONEY to retailers → industry is "Fintech / NBFC / B2B Lending", NOT "Retail".
  Example: A company that DELIVERS to restaurants → industry is "Logistics / Last-Mile Delivery", NOT "Food & Beverage".
  Example: A company that BUILDS SOFTWARE for hospitals → industry is "Health Tech / SaaS", NOT "Healthcare".
- The `competitive_context` field must name companies in the SAME business (same product/service), not the same customer base.
- Return ONLY valid JSON. No markdown, no explanation outside the JSON."""


async def run(idea: str) -> AgentResult:
    """Execute the Idea Discovery Agent."""

    user_prompt = (
        f"USER'S RAW IDEA:\n\"\"\"\n{idea}\n\"\"\"\n\n"
        f"Extract all key details from this idea into the required JSON structure. "
        f"Be specific, concrete, and insightful. Infer what the user hasn't stated explicitly."
    )

    raw = await call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.5,
        response_format={"type": "json_object"},
    )

    # Strip possible markdown fences
    clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw.strip(), flags=re.MULTILINE)

    try:
        data = json.loads(clean)
    except Exception:
        # Fallback: return minimal structured data so the pipeline doesn't crash
        data = {
            "refined_idea": idea,
            "industry_category": "General",
            "business_model": "To be determined",
            "problem_solved": idea,
            "target_audience": {
                "primary": "General audience",
                "secondary": "Early adopters",
                "geography": "Global",
            },
            "value_proposition": idea,
            "key_differentiators": ["Innovative approach", "User-centric design", "Market timing"],
            "revenue_model": "Subscription or freemium",
            "core_features": ["Core functionality", "User dashboard", "Integrations", "Analytics"],
            "brand_tone_hints": "modern, trustworthy",
            "competitive_context": "Existing market solutions",
            "unique_insight": "Early mover advantage in an emerging space",
        }

    # Ensure target_audience is always a dict (older runs may have a string)
    if isinstance(data.get("target_audience"), str):
        data["target_audience"] = {
            "primary": data["target_audience"],
            "secondary": "Early adopters",
            "geography": "Global",
        }

    audience = data.get("target_audience", {})
    primary_audience = audience.get("primary", "a broad audience") if isinstance(audience, dict) else str(audience)

    explanation = (
        f"Idea extracted: '{data.get('refined_idea', idea)[:80]}...' | "
        f"Industry: {data.get('industry_category', 'General')} | "
        f"Model: {data.get('business_model', 'TBD')} | "
        f"Audience: {primary_audience} | "
        f"Problem: {data.get('problem_solved', 'N/A')[:80]} | "
        f"Differentiators: {', '.join(data.get('key_differentiators', [])[:2])}"
    )

    return AgentResult(data=data, explanation=explanation)
