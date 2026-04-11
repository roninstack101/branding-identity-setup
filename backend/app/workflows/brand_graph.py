"""
Brand Identity Workflow Orchestrator
Implements a graph-based pipeline with:
  - Sequential execution for most agents
  - Single Gemini call for Market Research + Competitor Analysis (combined)
  - Single GPT-4o mini call for Brand Strategy + Naming (combined)
  - DB persistence after each step
  - Regeneration support via the Feedback Agent
"""
import asyncio
import json
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.models import AgentOutput, Project, BrandKit
from app.schemas.brand_schema import AgentResult, WorkflowState

from app.agents import (
    idea_discovery,
    market_competitor_agent,
    strategy_naming_agent,
    visual_identity_agent,
    content_agent,
    guidelines_agent,
    export_agent,
    feedback_agent,
)

# Agent execution order (index = step number)
AGENT_SEQUENCE = [
    "idea_discovery",       # 0
    "market_research",      # 1  ─┐ PARALLEL
    "competitor_analysis",  # 2  ─┘
    "brand_strategy",       # 3
    "naming",               # 4
    "visual_identity_agent",# 5
    "content_agent",        # 6
    "guidelines_agent",     # 7
    "export_agent",         # 8
]


async def _save_agent_output(
    db: AsyncSession,
    project_id: UUID,
    agent_name: str,
    result: AgentResult,
) -> None:
    """Persist an agent's output to the database, auto-incrementing version."""
    # Determine next version
    stmt = select(func.coalesce(func.max(AgentOutput.version), 0)).where(
        AgentOutput.project_id == project_id,
        AgentOutput.agent_name == agent_name,
    )
    result_row = await db.execute(stmt)
    current_max = result_row.scalar() or 0

    output = AgentOutput(
        project_id=project_id,
        agent_name=agent_name,
        output_json=result.data,
        explanation=result.explanation,
        version=current_max + 1,
    )
    db.add(output)
    await db.flush()


async def _get_latest_output(
    db: AsyncSession, project_id: UUID, agent_name: str
) -> dict | None:
    """Fetch the latest version of an agent output for a project."""
    stmt = (
        select(AgentOutput)
        .where(
            AgentOutput.project_id == project_id,
            AgentOutput.agent_name == agent_name,
        )
        .order_by(AgentOutput.version.desc())
        .limit(1)
        # populate_existing ensures we bypass the session identity-map cache
        # and always read the freshest committed row from the DB.
        .execution_options(populate_existing=True)
    )
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    if agent_name == "naming" and row:
        print(f"[build_state] naming v{row.version} brand_name={row.output_json.get('brand_name')}")
    return row.output_json if row else None


async def run_step(
    db: AsyncSession,
    project: Project,
    step: int,
    state: WorkflowState,
) -> WorkflowState:
    """Run a single step (or parallel pair) in the pipeline."""

    # ── Step 0: Idea Discovery ────────────────────────────────────────
    if step == 0:
        result = await idea_discovery.run(state.idea)
        state.idea_discovery = result.data
        await _save_agent_output(db, project.id, "idea_discovery", result)

    # ── Step 1: Market Research + Competitor Analysis (single Gemini call) ──
    elif step == 1:
        try:
            mr_result, ca_result = await market_competitor_agent.run(state.idea_discovery)
        except Exception as exc:
            print(f"[market_competitor_agent] Error: {exc}")
            mr_result = AgentResult(
                data={
                    "market_size": "Temporarily unavailable",
                    "market_trends": ["Analysis pending"],
                    "target_demographics": {
                        "primary_segment": "General audience",
                        "psychographics": ["Data pending"],
                        "behavior_patterns": ["Data pending"],
                    },
                    "market_gaps": ["Detailed market gaps unavailable due to temporary processing issue"],
                    "growth_drivers": ["Data refresh required"],
                    "key_sources": [],
                },
                explanation="Market research fallback generated because the analysis service was temporarily unavailable.",
            )
            ca_result = AgentResult(
                data={
                    "direct_competitors": [],
                    "indirect_competitors": [],
                    "competitive_advantages": ["Positioning pending refreshed competitor scan"],
                    "market_positioning_gaps": ["Detailed competitor gaps unavailable due to temporary processing issue"],
                    "recommended_positioning": "Use a differentiated value proposition while competitor scan is retried.",
                    "threat_level": "medium",
                },
                explanation="Competitor analysis fallback generated because the analysis service was temporarily unavailable.",
            )

        state.market_research = mr_result.data
        state.competitor_analysis = ca_result.data

        await _save_agent_output(db, project.id, "market_research", mr_result)
        await _save_agent_output(db, project.id, "competitor_analysis", ca_result)

    # ── Step 3: Brand Strategy + Naming (single GPT-4o mini call) ───────
    elif step == 3:
        strategy_result, naming_result = await strategy_naming_agent.run(
            state.idea_discovery,
            state.market_research,
            state.competitor_analysis,
        )
        state.brand_strategy = strategy_result.data
        state.naming = naming_result.data
        await _save_agent_output(db, project.id, "brand_strategy", strategy_result)
        await _save_agent_output(db, project.id, "naming", naming_result)

    # ── Step 4: Skipped (naming handled in step 3) ───────────────────
    elif step == 4:
        pass

    # ── Step 5: Unified Visual Identity (Design + Logo Direction + Links) ──
    elif step == 5:
        result = await visual_identity_agent.run(
            state.idea_discovery,
            state.market_research,
            state.competitor_analysis,
            state.brand_strategy,
            state.naming,
        )
        state.visual_identity_agent = result.data
        await _save_agent_output(db, project.id, "visual_identity_agent", result)

    # ── Step 6: Brand Content ────────────────────────────────────────
    elif step == 6:
        result = await content_agent.run(
            state.brand_strategy, state.naming, state.visual_identity_agent
        )
        state.content_agent = result.data
        await _save_agent_output(db, project.id, "content_agent", result)

    # ── Step 7: Brand Guidelines ─────────────────────────────────────
    elif step == 7:
        result = await guidelines_agent.run(
            state.brand_strategy, state.naming, state.visual_identity_agent, state.content_agent
        )
        state.guidelines_agent = result.data
        await _save_agent_output(db, project.id, "guidelines_agent", result)

    # ── Step 8: Export ───────────────────────────────────────────────
    elif step == 8:
        brand_data = {
            "idea_discovery": state.idea_discovery,
            "market_research": state.market_research,
            "competitor_analysis": state.competitor_analysis,
            "brand_strategy": state.brand_strategy,
            "naming": state.naming,
            "visual_identity_agent": state.visual_identity_agent,
            "content_agent": state.content_agent,
            "guidelines_agent": state.guidelines_agent,
        }
        result = await export_agent.run(str(project.id), brand_data)
        state.export_agent = result.data
        await _save_agent_output(db, project.id, "export_agent", result)

        # Save brand kit
        kit = BrandKit(
            project_id=project.id,
            final_output=brand_data,
            export_path=result.data.get("pdf_path"),
        )
        db.add(kit)

    # Update project step
    # Keep the stored value aligned with the next actual step.
    # The only non-linear transition is the parallel step 1+2, which should jump to step 3.
    if step == 1:
        project.current_step = 3
    else:
        project.current_step = step + 1
    if step >= 8:
        project.status = "completed"
    else:
        project.status = "running"
    await db.flush()

    return state


async def build_state_from_db(db: AsyncSession, project: Project) -> WorkflowState:
    """Reconstruct the workflow state from saved DB outputs."""
    state = WorkflowState(project_id=project.id, idea=project.idea)

    for agent_name in AGENT_SEQUENCE:
        data = await _get_latest_output(db, project.id, agent_name)
        # Keep intentionally empty dict outputs (e.g. fallback "{}") so later steps
        # don't receive None and crash on `.get(...)` calls.
        if data is not None:
            setattr(state, agent_name, data)

    return state


async def run_full_workflow(db: AsyncSession, project: Project) -> WorkflowState:
    """Run ALL steps of the brand identity pipeline end-to-end."""
    state = WorkflowState(project_id=project.id, idea=project.idea)
    project.status = "running"
    await db.flush()

    # Steps: 0 → 1(parallel 1+2) → 3 → 4 → 5 → 6 → 7 → 8
    ordered_steps = [0, 1, 3, 4, 5, 6, 7, 8]
    for step in ordered_steps:
        state = await run_step(db, project, step, state)

    await db.commit()
    return state


def _next_step_from_progress(current_step: int) -> int | None:
    """Map stored progress to the next actual workflow step."""
    if current_step <= 0:
        return 0
    if current_step == 1:
        return 1
    if current_step == 2:
        return 3
    if current_step >= len(AGENT_SEQUENCE):
        return None
    return current_step


async def regenerate_agents(
    db: AsyncSession,
    project: Project,
    feedback_text: str,
) -> dict:
    """Use the Feedback Agent to interpret feedback, then re-run specified agents."""
    state = await build_state_from_db(db, project)

    current_outputs = {
        "visual_identity_agent": state.visual_identity_agent,
        "content_agent": state.content_agent,
    }

    # Step 1: Let the Feedback Agent decide what to regenerate
    fb_result = await feedback_agent.run(feedback_text, current_outputs)
    await _save_agent_output(db, project.id, "feedback_agent", fb_result)

    agents_to_regen = fb_result.data.get("agents_to_regenerate", [])
    modifications = fb_result.data.get("modifications", {})
    regenerated = {}

    # Step 2: Re-run each specified agent with modified instructions
    for agent_name in agents_to_regen:
        mod = modifications.get(agent_name, feedback_text)

        if agent_name == "visual_identity_agent":
            result = await visual_identity_agent.run(
                state.idea_discovery,
                state.market_research,
                state.competitor_analysis,
                state.brand_strategy,
                state.naming,
                feedback=mod,
            )
            state.visual_identity_agent = result.data

        elif agent_name == "content_agent":
            result = await content_agent.run(
                state.brand_strategy, state.naming, state.visual_identity_agent, feedback=mod
            )
            state.content_agent = result.data

        else:
            continue

        await _save_agent_output(db, project.id, agent_name, result)
        regenerated[agent_name] = result.model_dump()

    await db.commit()
    return {
        "feedback_analysis": fb_result.model_dump(),
        "regenerated": regenerated,
    }
