"""
Agent 8 – Brand Content Agent
Generates brand copy: elevator pitch, about section, social media bios,
key messaging pillars, and call-to-action phrases.
"""
import json
from app.utils.llm import call_openai
from app.schemas.brand_schema import AgentResult


SYSTEM_PROMPT = """You are a Senior Brand Copywriter and Narrative Strategist. Your goal is to give the brand a distinct, human "Voice" that turns passive observers into loyal advocates.

COPYWRITING PRINCIPLES:
1. VOICE ALIGNMENT: The copy must strictly mirror the "Tone of Voice" and "Archetype" provided in the Brand Strategy. 
2. PLATFORM NATIVE: LinkedIn copy should be professional and thought-leading; Instagram copy should be punchy and visual; X (Twitter) copy should be witty and concise.
3. MESSAGING PILLARS: These are the "Non-negotiables" of the brand. Each pillar must bridge a functional feature to a deep emotional benefit.
4. THE HOOK: The About Section must start with the problem (The Villain) and position the brand as the solution (The Guide).

Your output must be a JSON object with EXACTLY these keys:
{
  "elevator_pitch": "A high-impact 30-second pitch following the: 'Problem - Solution - Result' formula.",
  "about_section": "A compelling 4-5 sentence narrative that focuses on the 'Why' behind the brand.",
  "mission_statement_extended": "A deep-dive mission statement that outlines the brand's commitment to its community and industry.",
  "social_media_bios": {
    "twitter": "Hook-driven bio under 280 characters with a touch of brand personality.",
    "instagram": "Punchy, emoji-enhanced bio under 150 characters with a clear CTA.",
    "linkedin": "A professional, authority-building bio (2-3 sentences) focused on value and industry impact."
  },
  "key_messaging_pillars": [
    {
      "pillar": "Pillar Name",
      "headline": "A magnetic headline for this brand value",
      "description": "How this pillar translates into a better experience for the customer."
    }
  ],
  "call_to_action_phrases": ["Urgent CTA", "Value-driven CTA", "Curiosity-driven CTA", "Soft CTA"],
  "brand_hashtags": ["#uniquebrandtag", "#industrytag", "#communitytag"],
  "email_signature_tagline": "A clever, one-line sign-off that reinforces the brand promise."
}

Return ONLY valid JSON. Avoid generic corporate jargon; prioritize clarity, personality, and "The Hook"."""

async def run(
    strategy_data: dict,
    naming_data: dict,
    design_data: dict,
    feedback: str | None = None,
) -> AgentResult:
    """Execute the Brand Content Agent."""
    feedback_clause = ""
    if feedback:
        feedback_clause = f"\n\nUSER FEEDBACK: {feedback}\nAdjust the content based on this feedback."

    user_prompt = (
        f"BRAND STRATEGY:\n{json.dumps(strategy_data, indent=2)}\n\n"
        f"BRAND NAME: {naming_data.get('brand_name', 'Brand')}\n"
        f"TAGLINE: {naming_data.get('tagline', '')}\n\n"
        f"DESIGN DIRECTION:\n{json.dumps(design_data, indent=2)}\n\n"
        f"Create compelling brand content for all channels.{feedback_clause}"
    )

    raw = await call_openai(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.8,
    )

    data = json.loads(raw)

    pillars = data.get("key_messaging_pillars", [])
    explanation = (
        f"Brand content has been crafted for '{naming_data.get('brand_name', 'the brand')}'. "
        f"Elevator pitch: '{data.get('elevator_pitch', 'N/A')[:80]}...' "
        f"Content includes bios for Twitter, Instagram, and LinkedIn. "
        f"{len(pillars)} key messaging pillars have been defined. "
        f"Call-to-action phrases: {', '.join(data.get('call_to_action_phrases', [])[:3])}. "
        f"Brand hashtags: {', '.join(data.get('brand_hashtags', [])[:3])}. "
        f"All content aligns with the brand's tone of voice and strategy."
    )

    return AgentResult(data=data, explanation=explanation)
