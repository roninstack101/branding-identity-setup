"""
Agent 11 – Feedback Agent
Interprets user feedback and determines which agent(s) to re-run
and how to modify the prompts.
"""
import json
from app.utils.llm import call_openai
from app.schemas.brand_schema import AgentResult


SYSTEM_PROMPT = """You are a Senior Creative Director and Brand Project Manager. Your role is to act as the "Intelligence Layer" between user feedback and the creative agents (Design and Content).

OPERATIONAL LOGIC:
1. DECONSTRUCTION: Break down the user's feedback into three categories: Aesthetic (Visuals), Semantic (Meaning/Copy), or Strategic (Positioning).
2. AGENT MAPPING: 
   - If feedback mentions "colors," "fonts," "vibe," "logo," or "style," select "visual_identity_agent".
   - If feedback mentions "wording," "pitch," "tone," "bio," or "tagline," select "content_agent".
3. TECHNICAL TRANSLATION: Do not just pass the feedback. Translate it into technical "Creative Brief" language. 
   - (e.g., If user says "it's too boring," translate to "Increase visual contrast, explore Neo-Brutalist trends, and use punchier, action-oriented verbs in the copy.")

Your output must be a JSON object with EXACTLY these keys:
{
  "agents_to_regenerate": ["visual_identity_agent", "content_agent"],
  "modifications": {
    "visual_identity_agent": "Technical brief for the design agent (e.g., Shift palette to high-saturation neons, prioritize minimalist serif typography).",
    "content_agent": "Technical brief for the content agent (e.g., Adopt a more irreverent, 'Outlaw' archetype voice; remove corporate jargon)."
  },
  "feedback_interpretation": "A professional summary of what the user is actually dissatisfied with (e.g., The user feels the brand lacks energy and feels too traditional).",
  "confidence": "high | medium | low"
}

Return ONLY valid JSON. If the feedback does not apply to an agent, leave its modification string empty and do not include it in 'agents_to_regenerate'."""
REGENERATABLE_AGENTS = {"visual_identity_agent", "content_agent"}


async def run(feedback: str, current_outputs: dict) -> AgentResult:
    """Execute the Feedback Agent to determine regeneration plan."""
    # Build context of current outputs (summaries only, not full data)
    context_summary = {}
    for agent_name in REGENERATABLE_AGENTS:
        output = current_outputs.get(agent_name, {})
        if isinstance(output, dict):
            context_summary[agent_name] = {
                k: str(v)[:200] for k, v in output.items() if k != "logo_base64"
            }

    user_prompt = (
        f"USER FEEDBACK: {feedback}\n\n"
        f"CURRENT OUTPUTS SUMMARY:\n{json.dumps(context_summary, indent=2)}\n\n"
        f"Analyze the feedback and determine what should be regenerated and how."
    )

    raw = await call_openai(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.3,
    )

    data = json.loads(raw)

    # Validate agent names
    requested = data.get("agents_to_regenerate", [])
    data["agents_to_regenerate"] = [a for a in requested if a in REGENERATABLE_AGENTS]

    explanation = (
        f"Feedback analyzed: '{feedback[:80]}...' "
        f"Interpretation: {data.get('feedback_interpretation', 'N/A')[:100]}. "
        f"Confidence level: {data.get('confidence', 'medium')}. "
        f"Agents to regenerate: {', '.join(data.get('agents_to_regenerate', []))}. "
        f"Each agent will receive modified instructions based on the feedback. "
        f"The regeneration will create new versions while preserving previous outputs."
    )

    return AgentResult(data=data, explanation=explanation)
