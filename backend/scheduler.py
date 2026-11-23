import json
from datetime import datetime
from typing import List, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.config import WORKFLOWS_DIR
from backend.models import ScheduledWorkflow
from backend.orchestrator import WorkforceEngine

class WorkflowScheduler:
    def __init__(self, engine: WorkforceEngine):
        self.engine = engine
        self.scheduler = AsyncIOScheduler()

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            for wf in self.list_workflows():
                if wf.status == "ACTIVE":
                    self._register_job(wf)

    def list_workflows(self) -> List[ScheduledWorkflow]:
        items = []
        for f in sorted(WORKFLOWS_DIR.glob("*.json")):
            items.append(ScheduledWorkflow(**json.loads(f.read_text(encoding="utf-8"))))
        return items

    def get_workflow(self, workflow_id: str) -> Optional[ScheduledWorkflow]:
        path = WORKFLOWS_DIR / f"{workflow_id}.json"
        if path.exists():
            return ScheduledWorkflow(**json.loads(path.read_text(encoding="utf-8")))
        return None

    def save_workflow(self, wf: ScheduledWorkflow) -> ScheduledWorkflow:
        path = WORKFLOWS_DIR / f"{wf.workflow_id}.json"
        path.write_text(json.dumps(wf.model_dump(), indent=2), encoding="utf-8")
        if wf.status == "ACTIVE":
            self._register_job(wf)
        else:
            self._remove_job(wf.workflow_id)
        return wf

    def _register_job(self, wf: ScheduledWorkflow):
        self._remove_job(wf.workflow_id)
        parts = wf.cron_schedule.split()
        if len(parts) == 5:
            minute, hour, day, month, dow = parts
            self.scheduler.add_job(
                self.trigger_now,
                "cron",
                id=wf.workflow_id,
                args=[wf.workflow_id],
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=dow,
                replace_existing=True
            )

    def _remove_job(self, workflow_id: str):
        if self.scheduler.get_job(workflow_id):
            self.scheduler.remove_job(workflow_id)

    async def trigger_now(self, workflow_id: str) -> Optional[ScheduledWorkflow]:
        wf = self.get_workflow(workflow_id)
        if not wf:
            return None
        run = await self.engine.start_run(wf.room_id, wf.instruction)
        now = datetime.utcnow().isoformat() + "Z"
        wf.last_run_at = now
        wf.last_run_id = run.run_id
        wf.last_status = "TRIGGERED"
        wf.run_history.append({
            "triggered_at": now,
            "run_id": run.run_id,
            "status": "TRIGGERED",
            "instruction": wf.instruction
        })
        self.save_workflow(wf)
        return wf
