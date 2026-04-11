"""
API routes for brand identity creation and management.
"""
from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.database import get_db
from app.db.models import Project, AgentOutput, BrandKit
from app.schemas.brand_schema import (
    ProjectCreate,
    ProjectOut,
    AgentOutputOut,
    WorkflowState,
)
from app.workflows.brand_graph import (
    run_full_workflow,
    run_step,
    build_state_from_db,
    AGENT_SEQUENCE,
    _next_step_from_progress,
)
from app.agents.visual_identity_agent import regenerate_variant_svg


class SelectNameRequest(BaseModel):
    brand_name: str


class VariantRegenerateRequest(BaseModel):
    variant_index: int
    color_palette: List[str]        # 5 hex strings
    heading_font:  str | None = None
    body_font:     str | None = None


router = APIRouter(prefix="/api/brand", tags=["Brand"])


# ── Create Project ────────────────────────────────────────────────────
@router.post("/project", response_model=ProjectOut, status_code=201)
async def create_project(
    payload: ProjectCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new brand identity project."""
    project = Project(idea=payload.idea, user_id=payload.user_id)
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


# ── Run Full Workflow ─────────────────────────────────────────────────
@router.post("/project/{project_id}/run")
async def run_workflow(project_id: UUID, db: AsyncSession = Depends(get_db)):
    """Run the entire brand identity pipeline for a project."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if project.status == "completed":
        raise HTTPException(400, "Project workflow already completed")

    state = await run_full_workflow(db, project)
    return {
        "status": "completed",
        "project_id": str(project_id),
        "state": state.model_dump(),
    }


# ── Run Next Step ─────────────────────────────────────────────────────
@router.post("/project/{project_id}/step")
async def run_next_step(project_id: UUID, db: AsyncSession = Depends(get_db)):
    """Run the next step in the pipeline (for step-by-step approval)."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if project.status == "completed":
        raise HTTPException(400, "Workflow already completed")

    current = project.current_step or 0

    step = _next_step_from_progress(current)
    if step is None:
        raise HTTPException(400, "All steps completed")
    state = await build_state_from_db(db, project)
    state = await run_step(db, project, step, state)
    await db.commit()

    return {
        "step_completed": step,
        "next_step": None if project.status == "completed" else project.current_step,
        "status": project.status,
        "state": state.model_dump(),
    }


# ── Select Brand Name ─────────────────────────────────────────────────
@router.post("/project/{project_id}/select-name")
async def select_brand_name(
    project_id: UUID,
    body: SelectNameRequest,
    db: AsyncSession = Depends(get_db),
):
    """Save the user's chosen brand name as a new version of the naming output.
    All subsequent agents read brand_name from this output, so they will
    automatically use the selected name."""
    if not body.brand_name or not body.brand_name.strip():
        raise HTTPException(400, "brand_name must not be empty")

    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    # Fetch latest naming output
    stmt = (
        select(AgentOutput)
        .where(
            AgentOutput.project_id == project_id,
            AgentOutput.agent_name == "naming",
        )
        .order_by(AgentOutput.version.desc())
        .limit(1)
    )
    row = (await db.execute(stmt)).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Naming output not found. Run the naming step first.")

    # Merge: keep all existing naming data, just override brand_name
    updated_data = dict(row.output_json)
    previous_name = updated_data.get("brand_name", "")
    updated_data["brand_name"] = body.brand_name.strip()

    # Save as a new version so history is preserved
    max_stmt = select(func.coalesce(func.max(AgentOutput.version), 0)).where(
        AgentOutput.project_id == project_id,
        AgentOutput.agent_name == "naming",
    )
    current_max = (await db.execute(max_stmt)).scalar() or 0

    new_row = AgentOutput(
        project_id=project_id,
        agent_name="naming",
        output_json=updated_data,
        explanation=f"Brand name selected by user: '{body.brand_name}' (was '{previous_name}').",
        version=current_max + 1,
    )
    db.add(new_row)
    await db.commit()
    print(f"[select-name] project={project_id} saved brand_name='{body.brand_name}' as version {current_max + 1}")

    return {"brand_name": body.brand_name, "version": current_max + 1}


# ── Get Project State ─────────────────────────────────────────────────
@router.get("/project/{project_id}")
async def get_project(project_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get the current state of a project including all agent outputs."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    stmt = (
        select(AgentOutput)
        .where(AgentOutput.project_id == project_id)
        .order_by(AgentOutput.agent_name, AgentOutput.version.desc())
    )
    result = await db.execute(stmt)
    outputs = result.scalars().all()

    # Group by agent_name, keep latest version
    latest: dict = {}
    for o in outputs:
        if o.agent_name not in latest:
            latest[o.agent_name] = {
                "agent_name": o.agent_name,
                "output_json": o.output_json,
                "explanation": o.explanation,
                "version": o.version,
                "created_at": str(o.created_at),
            }

    return {
        "project": {
            "id": str(project.id),
            "idea": project.idea,
            "current_step": project.current_step,
            "status": project.status,
            "created_at": str(project.created_at),
        },
        "agent_outputs": latest,
    }


# ── List Projects ────────────────────────────────────────────────────
@router.get("/projects")
async def list_projects(db: AsyncSession = Depends(get_db)):
    """List all projects."""
    stmt = select(Project).order_by(Project.created_at.desc())
    result = await db.execute(stmt)
    projects = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "idea": p.idea[:100],
            "status": p.status,
            "current_step": p.current_step,
            "created_at": str(p.created_at),
        }
        for p in projects
    ]


# ── Download Brand Kit ───────────────────────────────────────────────
@router.get("/project/{project_id}/export")
async def get_export(project_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get export file paths for a completed project."""
    stmt = select(BrandKit).where(BrandKit.project_id == project_id)
    result = await db.execute(stmt)
    kit = result.scalar_one_or_none()

    if not kit:
        raise HTTPException(404, "Brand kit not found. Run the full workflow first.")

    return {
        "project_id": str(project_id),
        "export_path": kit.export_path,
        "created_at": str(kit.created_at),
    }


# ── Variant Colour Regeneration ───────────────────────────────────────
@router.post("/project/{project_id}/variant-regenerate")
async def variant_regenerate(
    project_id: UUID,
    body: VariantRegenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Regenerate a single variant's SVG logo with a new colour palette."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    if len(body.color_palette) != 5:
        raise HTTPException(400, "color_palette must contain exactly 5 hex values")

    # ── Fetch latest visual_identity output ──────────────────────────
    vi_stmt = (
        select(AgentOutput)
        .where(
            AgentOutput.project_id == project_id,
            AgentOutput.agent_name == "visual_identity_agent",
        )
        .order_by(AgentOutput.version.desc())
        .limit(1)
    )
    vi_row = (await db.execute(vi_stmt)).scalar_one_or_none()
    if not vi_row:
        raise HTTPException(404, "Visual identity not generated yet")

    output_data = dict(vi_row.output_json)
    variants = list(output_data.get("variants", []))

    if body.variant_index < 0 or body.variant_index >= len(variants):
        raise HTTPException(400, f"variant_index {body.variant_index} out of range (0–{len(variants)-1})")

    # ── Get brand name from naming output ────────────────────────────
    naming_stmt = (
        select(AgentOutput)
        .where(
            AgentOutput.project_id == project_id,
            AgentOutput.agent_name == "naming",
        )
        .order_by(AgentOutput.version.desc())
        .limit(1)
    )
    naming_row = (await db.execute(naming_stmt)).scalar_one_or_none()
    brand_name = (naming_row.output_json or {}).get("brand_name", "Brand") if naming_row else "Brand"

    # ── Regenerate the single variant ────────────────────────────────
    updated_variant = await regenerate_variant_svg(
        variant=variants[body.variant_index],
        variant_index=body.variant_index,
        brand_name=brand_name,
        new_color_palette=body.color_palette,
        heading_font=body.heading_font,
        body_font=body.body_font,
    )
    variants[body.variant_index] = updated_variant
    output_data["variants"] = variants

    # If it's the hero variant (index 0), update top-level color_palette too
    if body.variant_index == 0:
        c = body.color_palette
        output_data["color_palette"] = {
            "primary":      {"hex": c[0], "name": "Primary",      "usage": "Main brand color"},
            "secondary":    {"hex": c[1], "name": "Secondary",    "usage": "Supporting elements"},
            "accent":       {"hex": c[2], "name": "Accent",       "usage": "CTAs and highlights"},
            "neutral_dark": {"hex": c[3], "name": "Dark Neutral", "usage": "Primary text"},
            "neutral_light":{"hex": c[4], "name": "Light Neutral","usage": "Backgrounds"},
        }

    # ── Save new version ──────────────────────────────────────────────
    max_stmt = select(func.coalesce(func.max(AgentOutput.version), 0)).where(
        AgentOutput.project_id == project_id,
        AgentOutput.agent_name == "visual_identity_agent",
    )
    current_max = (await db.execute(max_stmt)).scalar() or 0

    new_output = AgentOutput(
        project_id=project_id,
        agent_name="visual_identity_agent",
        output_json=output_data,
        explanation=f"Variant {body.variant_index} regenerated with custom colour palette {body.color_palette}.",
        version=current_max + 1,
    )
    db.add(new_output)
    await db.commit()

    return {
        "variant_index": body.variant_index,
        "variant": updated_variant,
        "output_json": output_data,
    }
