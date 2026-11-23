from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from pathlib import Path

from backend.config import BASE_DIR, MOCK_MODE
from backend.models import AgentProfile, CollaborationRoom, ScheduledWorkflow
from backend.orchestrator import WorkforceEngine
from backend.scheduler import WorkflowScheduler

app = FastAPI(title="OpenCrewBot 2.0 — Autonomous AI Workforce", version="2.0.0")
engine = WorkforceEngine()
scheduler = WorkflowScheduler(engine)

@app.on_event("startup")
async def on_startup():
    from backend.seed import seed_initial_data
    seed_initial_data(engine, scheduler)
    scheduler.start()
    # Recover any runs that were mid-flight before a server restart
    for run in engine.list_runs():
        if run.status == "RUNNING":
            await engine.resume_run(run.run_id)

# --- Request Schemas ---
class CreateAgentNLRequest(BaseModel):
    prompt: str

class RunInstructionRequest(BaseModel):
    room_id: str
    instruction: str
    project_id: str = "meetuniversity"

class InterruptRunRequest(BaseModel):
    instruction: str

class MemoryUpdateRequest(BaseModel):
    content: str

class ApprovalDecisionRequest(BaseModel):
    decision: str  # APPROVED or REJECTED
    resolved_by: str = "Human Operator"

class CreateRoomRequest(BaseModel):
    id: str
    name: str
    description: str
    agent_ids: list[str]

class CreateWorkflowRequest(BaseModel):
    name: str
    description: str
    room_id: str
    instruction: str
    cron_schedule: str = "0 9 * * 1"

# --- System & Overview ---
@app.get("/api/system/status")
def system_status():
    return {
        "status": "ONLINE",
        "mock_mode": MOCK_MODE,
        "agents_count": len(engine.list_agents()),
        "rooms_count": len(engine.list_rooms()),
        "skills_count": len(engine.skills.list_skills()),
        "pending_approvals": len(engine.governance.list_approvals(status="PENDING")),
        "usage_summary": engine.router.get_usage_summary()
    }

# --- Module B: Agents & Dynamic Factory ---
@app.get("/api/agents")
def get_agents():
    return [a.model_dump() for a in engine.list_agents()]

@app.post("/api/agents/dynamic")
async def create_dynamic_agent(req: CreateAgentNLRequest):
    agent = await engine.create_agent_from_nl(req.prompt)
    return agent.model_dump()

@app.put("/api/agents/{agent_id}")
def update_agent(agent_id: str, agent: AgentProfile):
    agent.id = agent_id
    return engine.save_agent(agent).model_dump()

# --- Module C: Collaboration Rooms ---
@app.get("/api/rooms")
def get_rooms():
    return [r.model_dump() for r in engine.list_rooms()]

@app.get("/api/rooms/{room_id}")
def get_room(room_id: str):
    room = engine.get_room(room_id)
    if not room:
        raise HTTPException(404, "Room not found")
    return room.model_dump()

@app.post("/api/rooms")
def create_room(req: CreateRoomRequest):
    room = CollaborationRoom(id=req.id, name=req.name, description=req.description, agent_ids=req.agent_ids)
    return engine.save_room(room).model_dump()

# --- Modules A & D: Orchestration, DAG Runs & Interruptions ---
@app.get("/api/runs")
def list_runs():
    return [r.model_dump() for r in engine.list_runs()]

@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    run = engine.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return run.model_dump()

@app.post("/api/runs")
async def start_run(req: RunInstructionRequest):
    run = await engine.start_run(req.room_id, req.instruction, req.project_id)
    return run.model_dump()

@app.post("/api/runs/{run_id}/interrupt")
async def interrupt_run(run_id: str, req: InterruptRunRequest):
    run = await engine.interrupt_run(run_id, req.instruction)
    if not run:
        raise HTTPException(404, "Run not found")
    return run.model_dump()

@app.post("/api/runs/{run_id}/resume")
async def resume_run(run_id: str):
    run = await engine.resume_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return run.model_dump()

@app.post("/api/runs/{run_id}/cancel")
async def cancel_run(run_id: str):
    run = await engine.cancel_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return run.model_dump()

# --- Module E: Persistent Editable Markdown Memory ---
@app.get("/api/memory")
def list_memory_files():
    return engine.memory.list_memories()

@app.get("/api/memory/{scope}/{entity_id}")
def read_memory_file(scope: str, entity_id: str):
    if scope not in ("agents", "rooms", "projects"):
        raise HTTPException(400, "Invalid memory scope")
    return {"scope": scope, "entity_id": entity_id, "content": engine.memory.read_memory(scope, entity_id)}

@app.put("/api/memory/{scope}/{entity_id}")
def update_memory_file(scope: str, entity_id: str, req: MemoryUpdateRequest):
    if scope not in ("agents", "rooms", "projects"):
        raise HTTPException(400, "Invalid memory scope")
    updated = engine.memory.write_memory(scope, entity_id, req.content)
    return {"scope": scope, "entity_id": entity_id, "content": updated}

# --- Modules F & H: Skills & Integrations ---
@app.get("/api/skills")
def get_skills():
    return engine.skills.list_skills()

@app.get("/api/integrations")
def get_integrations():
    return engine.toolbox.get_integration_status()

# --- Module G: Human Approval Centre & Audit Logs ---
@app.get("/api/approvals")
def list_approvals(status: Optional[str] = None):
    return [a.model_dump() for a in engine.governance.list_approvals(status)]

@app.post("/api/approvals/{approval_id}")
async def resolve_approval(approval_id: str, req: ApprovalDecisionRequest):
    try:
        appr = engine.governance.resolve_approval(approval_id, req.decision, req.resolved_by)
        # Resume the blocked DAG run automatically so it either executes or handles rejection cleanly
        await engine.resume_run(appr.run_id)
        return appr.model_dump()
    except ValueError as e:
        raise HTTPException(404, str(e))

@app.get("/api/audit")
def get_audit_logs():
    return engine.governance.get_audit_logs()

# --- Module I: Scheduled Workflows ---
@app.get("/api/workflows")
def list_workflows():
    return [w.model_dump() for w in scheduler.list_workflows()]

@app.post("/api/workflows")
def create_workflow(req: CreateWorkflowRequest):
    wf = ScheduledWorkflow(
        name=req.name,
        description=req.description,
        room_id=req.room_id,
        instruction=req.instruction,
        cron_schedule=req.cron_schedule
    )
    return scheduler.save_workflow(wf).model_dump()

@app.post("/api/workflows/{workflow_id}/toggle")
def toggle_workflow(workflow_id: str):
    wf = scheduler.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(404, "Workflow not found")
    wf.status = "PAUSED" if wf.status == "ACTIVE" else "ACTIVE"
    return scheduler.save_workflow(wf).model_dump()

@app.post("/api/workflows/{workflow_id}/run")
async def run_workflow_now(workflow_id: str):
    wf = await scheduler.trigger_now(workflow_id)
    if not wf:
        raise HTTPException(404, "Workflow not found")
    return wf.model_dump()

# --- Module J: Models & Token/Cost Ledger ---
@app.get("/api/models/usage")
def get_model_usage():
    return engine.router.get_usage_summary()

# --- Serve Frontend Workspace ---
FRONTEND_DIR = BASE_DIR / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
def serve_index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))
