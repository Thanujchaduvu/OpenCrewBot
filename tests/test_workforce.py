import asyncio
import pytest
from backend.orchestrator import WorkforceEngine
from backend.scheduler import WorkflowScheduler
from backend.seed import seed_initial_data

@pytest.mark.asyncio
async def test_end_to_end_workforce():
    engine = WorkforceEngine()
    scheduler = WorkflowScheduler(engine)
    seed_initial_data(engine, scheduler)

    # 1. Verify Minimum Acceptance Criteria Counts
    assert len(engine.list_agents()) >= 8
    assert len(engine.list_rooms()) >= 4
    assert len(engine.skills.list_skills()) >= 8

    # 2. Test Dynamic Agent Creation (Module B)
    new_agent = await engine.create_agent_from_nl(
        "Create an EdTech Pricing Specialist named VikramJr with controlled access and financial modelling skills"
    )
    assert engine.get_agent(new_agent.id) is not None

    # 3. Test Demo 3: Live Pandas Spreadsheet Analysis
    run_biz = await engine.start_run(
        "room_revops_analytics",
        "Analyse the MeetUniversity sales spreadsheet and identify conversion bottlenecks."
    )
    for _ in range(30):
        if engine.get_run(run_biz.run_id).status in ('COMPLETED', 'FAILED'): break
        await asyncio.sleep(0.5)
    completed_biz = engine.get_run(run_biz.run_id)
    assert completed_biz.status == "COMPLETED"
    assert "Aspirations" in completed_biz.final_deliverable

    # 4. Test Demo 7: Human Approval Gate & Rejection Enforcement
    run_ext = await engine.start_run(
        "room_growth_studio",
        "Send email outreach to principal@dps-partner.example.com for MeetUniversity Aspirations."
    )
    for _ in range(30):
        if engine.get_run(run_ext.run_id).status in ('PAUSED_APPROVAL', 'COMPLETED', 'FAILED'): break
        await asyncio.sleep(0.5)
    paused_run = engine.get_run(run_ext.run_id)
    assert paused_run.status == "PAUSED_APPROVAL"

    pending = [a for a in engine.governance.list_approvals("PENDING") if a.run_id == run_ext.run_id]
    assert len(pending) == 1

    # Reject the action and verify it NEVER executes
    engine.governance.resolve_approval(pending[0].approval_id, "REJECTED", "Test Auditor")
    await engine.resume_run(run_ext.run_id)
    for _ in range(30):
        if engine.get_run(run_ext.run_id).status in ('PAUSED_APPROVAL', 'COMPLETED', 'FAILED'): break
        await asyncio.sleep(0.5)
    final_ext = engine.get_run(run_ext.run_id)
    assert final_ext.status == "FAILED"
    assert "REJECTED" in final_ext.tasks[-1].error

    # 5. Test Demo 6: Persistent Editable Markdown Memory
    engine.memory.write_memory(
        "projects", "meetuniversity",
        "# Project Memory\n- **Remembered:** Always highlight Hyderabad and Bangalore regional hubs.\n"
    )
    reloaded = engine.memory.read_memory("projects", "meetuniversity")
    assert "Hyderabad and Bangalore" in reloaded
