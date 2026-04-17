"""
API endpoint – generate a logo image from a reference URL + brand prompt.

POST /api/logo/generate
  - Looks up the project's visual identity data (concepts, colors, brief)
  - Picks the requested concept's visual_concept description
  - Combines brand data + user prompt into a rich generation prompt
  - Calls gpt-image-1 (edit if reference supplied, generate otherwise)
  - Returns base64 PNG
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import AgentOutput, Project
from app.schemas.brand_schema import LogoGenerateRequest
from app.utils.llm import generate_logo_from_reference

router = APIRouter(prefix="/api/logo", tags=["Logo Generator"])


def _build_prompt(
    brand_name: str,
    abbreviation: str,
    tagline: str,
    industry: str,
    primary_color: str,
    accent_color: str,
    style_descriptors: str,
    concept: dict,
    user_prompt: str,
) -> str:
    visual_concept = concept.get("visual_concept", "")
    rationale      = concept.get("rationale", "")
    typography     = concept.get("typography", "")
    palette        = concept.get("palette", [])
    c_primary  = palette[0] if palette else primary_color
    c_accent   = palette[1] if len(palette) > 1 else accent_color

    lines = [
        f"Create a professional logo for {brand_name} ({abbreviation}).",
        f'Tagline: "{tagline}"' if tagline else "",
        f"Industry: {industry}" if industry else "",
        "",
        "VISUAL CONCEPT TO RENDER:",
        visual_concept,
        "",
        f"Creative rationale: {rationale}" if rationale else "",
        f"Typography: {typography}" if typography else "",
        f"Primary colour: {c_primary}",
        f"Accent colour: {c_accent}",
        f"Style: {style_descriptors}" if style_descriptors else "",
        "",
        "REQUIREMENTS:",
        "- Clean white background",
        "- Symbol mark above, brand name below in clean modern typography",
        "- Minimal, geometric, professional — suitable for business cards, app icon, signage",
        "- If a reference image is provided, adopt its composition and visual quality but redesign entirely for this brand",
        "- Do NOT copy the reference logo; use it only as a style/quality reference",
        "",
    ]
    if user_prompt.strip():
        lines += [f"Additional instructions: {user_prompt.strip()}", ""]

    return "\n".join(l for l in lines if l is not None)


@router.post("/generate")
async def generate_logo(
    payload: LogoGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a logo image for the given project + concept number.
    Accepts an optional reference_url and free-text user_prompt.
    """
    project = await db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    # ── Load visual identity data ──────────────────────────────────────────
    result = await db.execute(
        select(AgentOutput)
        .where(
            AgentOutput.project_id == payload.project_id,
            AgentOutput.agent_name == "visual_identity_agent",
        )
        .order_by(AgentOutput.version.desc())
        .limit(1)
    )
    vi_row = result.scalar_one_or_none()
    vi = vi_row.output_json if vi_row else {}

    concepts     = vi.get("design_concepts", [])
    primary      = vi.get("primary_color", "#005B80")
    accent       = vi.get("accent_color", "#FFB300")
    style_desc   = vi.get("style_descriptors", "")

    # ── Load naming data ───────────────────────────────────────────────────
    nm_result = await db.execute(
        select(AgentOutput)
        .where(
            AgentOutput.project_id == payload.project_id,
            AgentOutput.agent_name == "naming",
        )
        .order_by(AgentOutput.version.desc())
        .limit(1)
    )
    nm_row  = nm_result.scalar_one_or_none()
    nm      = nm_row.output_json if nm_row else {}
    brand_name   = nm.get("brand_name", "Brand")
    tagline      = nm.get("tagline", "")
    abbreviation = "".join(w[0].upper() for w in brand_name.split() if w)

    # ── Load idea discovery for industry ──────────────────────────────────
    id_result = await db.execute(
        select(AgentOutput)
        .where(
            AgentOutput.project_id == payload.project_id,
            AgentOutput.agent_name == "idea_discovery",
        )
        .order_by(AgentOutput.version.desc())
        .limit(1)
    )
    id_row   = id_result.scalar_one_or_none()
    id_data  = id_row.output_json if id_row else {}
    industry = id_data.get("industry_category", "")

    # ── Pick the requested concept ─────────────────────────────────────────
    concept = next(
        (c for c in concepts if c.get("number") == payload.concept_number),
        concepts[0] if concepts else {},
    )

    # ── Build the generation prompt ────────────────────────────────────────
    prompt = _build_prompt(
        brand_name=brand_name,
        abbreviation=abbreviation,
        tagline=tagline,
        industry=industry,
        primary_color=primary,
        accent_color=accent,
        style_descriptors=style_desc,
        concept=concept,
        user_prompt=payload.user_prompt,
    )

    print(f"[logo_generate] Generating for concept {payload.concept_number} of project {payload.project_id}")
    if payload.reference_url:
        print(f"[logo_generate] Reference: {payload.reference_url}")

    result = await generate_logo_from_reference(
        brand_prompt=prompt,
        reference_url=payload.reference_url or None,
    )

    if "error" in result:
        raise HTTPException(500, result["error"])

    return {
        "b64_json":  result["b64_json"],
        "model":     result.get("model", "unknown"),
        "prompt":    prompt,
        "concept":   concept,
    }
