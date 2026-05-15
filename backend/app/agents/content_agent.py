"""
Agent 8 – Brand Content Agent
Generates brand copy: mission/vision, about, tone of voice, email signature,
social media bios, messaging pillars, and CTAs.
"""
import json
from app.utils.llm import call_openai
from app.schemas.brand_schema import AgentResult


SYSTEM_PROMPT = """You are a Senior Brand Copywriter and Narrative Strategist. Your goal is to give the brand a distinct, human "Voice" that turns passive observers into loyal advocates.

COPYWRITING PRINCIPLES:
1. VOICE ALIGNMENT: Every word must strictly mirror the brand's Tone of Voice and Archetype.
2. PLATFORM NATIVE: LinkedIn = professional thought-leading; Instagram = punchy visual; X/Twitter = witty concise.
3. MESSAGING PILLARS: Bridge functional features to deep emotional benefits.
4. THE HOOK: The About Section starts with the problem (The Villain), positions the brand as the solution (The Guide).
5. MISSION vs VISION: Mission = what you do TODAY and WHY. Vision = the world you are building TOMORROW.

Your output must be a JSON object with EXACTLY these keys:
{
  "mission_statement": "One powerful sentence: 'We exist to...' or 'Our mission is to...' — ties directly to the core problem and the people served.",
  "vision_statement": "Bold aspirational future: 'A world where...' — emotionally resonant, not corporate filler.",
  "brand_stands_for": "3-4 sentences about the brand's core beliefs, non-negotiables, and its promise to the community. The North Star — what it will NEVER compromise on.",
  "about_section": "4-5 sentences: opens with the problem (The Villain), shows the brand as the solution (The Guide), ends with the transformation the customer experiences.",
  "elevator_pitch": "High-impact 30-second pitch following 'Problem → Solution → Result'. Under 60 words.",
  "mission_statement_extended": "3-4 sentence deep-dive on the brand's commitment to its community, industry, and broader world impact.",
  "tone_of_voice": {
    "character": ["Adjective 1", "Adjective 2", "Adjective 3", "Adjective 4"],
    "description": "2-3 sentences explaining the brand's writing style and what makes it instantly recognisable.",
    "write_like": [
      "Example sentence in brand voice — warm/direct/expert/witty as appropriate",
      "Second example — showing how the brand handles a customer benefit",
      "Third example — how the brand responds to a pain point"
    ],
    "avoid": [
      "Type of language or tone to avoid, with a brief reason",
      "Second thing to avoid",
      "Third thing to avoid"
    ],
    "example_hero_copy": "A full sample paragraph (3-4 sentences) written in brand voice — as if this is the homepage hero. Show, don't just tell."
  },
  "email_tagline": "A clever one-line sign-off for email signatures that reinforces the brand promise. Should feel like a natural extension of the brand voice — not the main tagline, but a complementary sign-off.",
  "social_media_bios": {
    "twitter": "Hook-driven bio under 280 characters with brand personality.",
    "instagram": "Punchy emoji-enhanced bio under 150 characters with a clear CTA.",
    "linkedin": "Professional authority-building bio (2-3 sentences) focused on value and industry impact."
  },
  "key_messaging_pillars": [
    {
      "pillar": "Pillar Name",
      "headline": "Magnetic headline for this brand value",
      "description": "How this pillar translates into a better customer experience."
    }
  ],
  "call_to_action_phrases": ["Urgent CTA", "Value-driven CTA", "Curiosity-driven CTA", "Soft CTA"],
  "brand_hashtags": ["#uniquebrandtag", "#industrytag", "#communitytag"]
}

Return ONLY valid JSON. Avoid generic corporate jargon. Every line should sound like it could ONLY belong to this brand."""


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

    # Back-fill legacy key from new field
    if not data.get("email_signature_tagline"):
        data["email_signature_tagline"] = data.get("email_tagline", "")

    pillars = data.get("key_messaging_pillars", [])
    tov     = data.get("tone_of_voice", {})
    explanation = (
        f"Brand content crafted for '{naming_data.get('brand_name', 'the brand')}'. "
        f"Mission: '{data.get('mission_statement', '')[:80]}'. "
        f"Tone of voice: {', '.join(tov.get('character', [])[:3])}. "
        f"{len(pillars)} messaging pillars defined. "
        f"Social bios, CTAs, email signature, and brand hashtags ready."
    )

    return AgentResult(data=data, explanation=explanation)
