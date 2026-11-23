from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

PermissionLevel = Literal["ASK_FIRST", "CONTROLLED_ACCESS", "FULL_ACCESS"]
TaskStatus = Literal["PENDING", "READY", "RUNNING", "AWAITING_APPROVAL", "COMPLETED", "FAILED", "CANCELLED"]
ApprovalStatus = Literal["PENDING", "APPROVED", "REJECTED"]

class ModelConfig(BaseModel):
    provider: str = "gemini"  # openai, gemini, anthropic, ollama, mock
    primary_model: str = "gemini-2.5-flash"
    fallback_model: str = "gpt-4o-mini"
    temperature: float = 0.3

class AgentProfile(BaseModel):
    id: str
    name: str
    role: str
    persona: str
    instructions: str
    model_config_data: ModelConfig = Field(default_factory=ModelConfig)
    skills: List[str] = Field(default_factory=list)
    allowed_tools: List[str] = Field(default_factory=list)
    permission_level: PermissionLevel = "ASK_FIRST"
    output_format: str = "Structured Markdown report with executive summary and action items."
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

class TaskNode(BaseModel):
    task_id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    title: str
    description: str
    assigned_agent: str
    dependencies: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    requires_approval: bool = False
    status: TaskStatus = "PENDING"
    retries: int = 0
    max_retries: int = 2
    timeout_seconds: int = 60
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    output: Optional[str] = None
    error: Optional[str] = None

class RoomMessage(BaseModel):
    id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:8]}")
    room_id: str
    sender: str
    msg_type: Literal["USER", "PLAN", "DELEGATION", "RESEARCH", "CRITIQUE", "VERIFICATION", "SYSTEM", "DELIVERABLE"]
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

class CollaborationRoom(BaseModel):
    id: str
    name: str
    description: str
    project_id: str = "meetuniversity"
    agent_ids: List[str] = Field(default_factory=list)
    max_turns_per_task: int = 6
    max_delegation_depth: int = 3
    messages: List[RoomMessage] = Field(default_factory=list)

class ExecutionRun(BaseModel):
    run_id: str = Field(default_factory=lambda: f"run_{uuid.uuid4().hex[:8]}")
    room_id: str
    project_id: str = "meetuniversity"
    instruction: str
    status: Literal["PLANNING", "RUNNING", "PAUSED_APPROVAL", "INTERRUPTED", "COMPLETED", "FAILED", "CANCELLED"] = "PLANNING"
    tasks: List[TaskNode] = Field(default_factory=list)
    final_deliverable: Optional[str] = None
    interruptions: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

class ApprovalRequest(BaseModel):
    approval_id: str = Field(default_factory=lambda: f"appr_{uuid.uuid4().hex[:8]}")
    run_id: str
    task_id: str
    agent_id: str
    permission_level: PermissionLevel
    tool_name: str
    action_preview: Dict[str, Any]
    reason: str
    status: ApprovalStatus = "PENDING"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None

class ScheduledWorkflow(BaseModel):
    workflow_id: str = Field(default_factory=lambda: f"wf_{uuid.uuid4().hex[:8]}")
    name: str
    description: str
    room_id: str
    instruction: str
    cron_schedule: str = "0 9 * * 1"  # Every Monday at 9 AM
    status: Literal["ACTIVE", "PAUSED"] = "ACTIVE"
    last_run_at: Optional[str] = None
    last_run_id: Optional[str] = None
    last_status: Optional[str] = None
    run_history: List[Dict[str, Any]] = Field(default_factory=list)
