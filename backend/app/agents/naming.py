import json
from app.utils.llm import call_openai
from app.schemas.brand_schema import AgentResult

SYSTEM_PROMPT = """You are a world-class Brand Naming Specialist and Corporate Linguist. 
Your task is to generate realistic, professional, and commercially viable brand names. 
Avoid generic 'AI-generated' sounding names (e.g., avoid names ending in '-ly', '-ify', or 'Nex-', 'Gen-').

NAMING CONSTRAINTS:
1. GROUNDED REALISM: Names must sound like established companies. Use Latin/Greek roots, portmanteaus of real words, or evocative 'Empty Vessel' names.
2. PHONETIC BREVITY: Prioritize 1-3 syllables. Ensure the 'mouthfeel' is easy to pronounce globally.
3. SEMANTIC WEIGHT: Every name must have a deep connection to the Brand Strategy. 
4. CATEGORIES TO EXPLORE:
   - RELEVANT REAL WORDS: (e.g., Slack, Square, Timber).
   - PORTMANTEAUS: (e.g., Microsoft, Instagram).
   - LATIN/GREEK ROOTS: (e.g., Volvo, Viatris).
   - MODERN ABSTRACT: (e.g., Sony, Hulu).

Your output must be a JSON object with EXACTLY these keys:
{
  "brand_name": "The strongest, most boardroom-ready recommendation",
  "tagline": "A high-end, benefit-driven value proposition",
  "name_candidates": [
    {
      "name": "The Name",
      "rationale": "Deep linguistic and strategic reasoning. Why does this sound established?",
      "style": "Modern Abstract / Portmanteau / Real Word",
      "domain_suggestion": "Professional .com or .io availability estimate"
    }
  ],
  "naming_strategy": "Summary of the semantic pillars used (e.g., 'Stability and Growth' or 'Velocity and Precision')",
  "brand_story_hook": "A one-sentence 'founding myth' for why this name was chosen."
}

Provide EXACTLY 6 candidates. Return ONLY valid JSON. No guessing or 'over-the-top' creative fluff."""

async def run(strategy_data: dict) -> AgentResult:
    """Execute the Brand Naming Agent with realistic linguistic focus."""
    user_prompt = (
        f"BRAND STRATEGY:\n{json.dumps(strategy_data, indent=2)}\n\n"
        f"Generate 6 realistic, professional brand names based on this strategy. "
        f"Avoid 'mushy' AI names. Think like a multi-million dollar naming agency."
    )

    # Temperature 0.8 is the "Golden Ratio" for naming: 
    # Creative enough for new ideas, but low enough to follow real-world spelling rules.
    raw = await call_openai(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.8,
    )

    data = json.loads(raw)

    candidates = data.get("name_candidates", [])
    explanation = (
        f"Linguistic naming analysis complete. Primary recommendation: '{data.get('brand_name', 'N/A')}'. "
        f"Generated {len(candidates)} grounded candidates using the strategy: '{data.get('naming_strategy', 'N/A')}'. "
        f"Focus was placed on phonetic brevity and real-word roots to avoid 'AI-sounding' patterns."
    )

    return AgentResult(data=data, explanation=explanation)