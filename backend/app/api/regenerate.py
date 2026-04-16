"""
API routes for regeneration via the Feedback Agent.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Project
from app.schemas.brand_schema import RegenerateRequest
from app.workflows.brand_graph import regenerate_agents

router = APIRouter(prefix="/api/regenerate", tags=["Regenerate"])


@router.post("/")
async def regenerate(
    payload: RegenerateRequest, db: AsyncSession = Depends(get_db)
):
    """
    Regenerate specific brand elements based on user feedback.

    The Feedback Agent analyzes the feedback and decides which agent(s) to re-run.
    Supports regeneration of: visual_identity_agent, content_agent.
    """
    project = await db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    # Minimum current_step required for each regeneratable agent.
    # current_step is incremented *after* an agent runs, so it equals step+1.
    # visual_identity_agent = step 5 → current_step must be ≥ 6
    # content_agent          = step 6 → current_step must be ≥ 7
    _MIN_STEP = {"visual_identity_agent": 6, "content_agent": 7}
    min_step = _MIN_STEP.get(payload.agent_name, 6)

    if project.status != "completed" and project.current_step < min_step:
        raise HTTPException(
            400,
            f"Project must have completed the '{payload.agent_name}' stage before it can be regenerated "
            f"(current step: {project.current_step}, required: {min_step}).",
        )

    result = await regenerate_agents(db, project, payload.feedback)

    return {
        "status": "regenerated",
        "project_id": str(payload.project_id),
        "result": result,
    }
