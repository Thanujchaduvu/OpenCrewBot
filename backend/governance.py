import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.config import DATA_DIR
from backend.models import ApprovalRequest, PermissionLevel

APPROVALS_FILE = DATA_DIR / "approvals.json"
AUDIT_LOG_FILE = DATA_DIR / "audit_log.json"

TOOL_RISK_CATALOG = {
    "web_research": "READ",
    "spreadsheet_analyzer": "READ",
    "github_inspect": "READ",
    "github_create_pr": "EXTERNAL_ACTION",
    "gmail_send_email": "EXTERNAL_ACTION",
    "slack_post_message": "EXTERNAL_ACTION",
    "notion_create_page": "WRITE"
}

class ToolRejectedError(Exception):
    pass

class ApprovalRequiredInterrupt(Exception):
    def __init__(self, approval: ApprovalRequest):
        self.approval = approval
        super().__init__(f"Approval required for {approval.tool_name} ({approval.approval_id})")

class GovernanceGate:
    def __init__(self):
        if not APPROVALS_FILE.exists():
            APPROVALS_FILE.write_text("[]", encoding="utf-8")
        if not AUDIT_LOG_FILE.exists():
            AUDIT_LOG_FILE.write_text("[]", encoding="utf-8")

    def _load_approvals(self) -> List[Dict[str, Any]]:
        return json.loads(APPROVALS_FILE.read_text(encoding="utf-8"))

    def _save_approvals(self, items: List[Dict[str, Any]]):
        APPROVALS_FILE.write_text(json.dumps(items, indent=2), encoding="utf-8")

    def log_audit(self, event_type: str, details: Dict[str, Any]):
        logs = json.loads(AUDIT_LOG_FILE.read_text(encoding="utf-8"))
        logs.append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            **details
        })
        AUDIT_LOG_FILE.write_text(json.dumps(logs[-1000:], indent=2), encoding="utf-8")

    def get_audit_logs(self) -> List[Dict[str, Any]]:
        return json.loads(AUDIT_LOG_FILE.read_text(encoding="utf-8"))

    def list_approvals(self, status: Optional[str] = None) -> List[ApprovalRequest]:
        items = [ApprovalRequest(**x) for x in self._load_approvals()]
        if status:
            return [a for a in items if a.status == status]
        return items

    def check_permission(
        self,
        run_id: str,
        task_id: str,
        agent_id: str,
        permission_level: PermissionLevel,
        tool_name: str,
        payload: Dict[str, Any],
        reason: str = "Agent requested external or sensitive tool execution"
    ) -> bool:
        risk = TOOL_RISK_CATALOG.get(tool_name, "EXTERNAL_ACTION")

        # Read-only tools pass automatically unless explicitly restricted
        if risk == "READ":
            self.log_audit("TOOL_ALLOWED", {"run_id": run_id, "task_id": task_id, "agent_id": agent_id, "tool": tool_name, "tier": permission_level})
            return True

        if permission_level == "FULL_ACCESS":
            self.log_audit("TOOL_AUTONOMOUS_EXEC", {"run_id": run_id, "task_id": task_id, "agent_id": agent_id, "tool": tool_name})
            return True

        if permission_level == "CONTROLLED_ACCESS" and risk == "WRITE":
            self.log_audit("TOOL_CONTROLLED_EXEC", {"run_id": run_id, "task_id": task_id, "agent_id": agent_id, "tool": tool_name})
            return True

        # Check if an existing approval record already exists for this task + tool
        approvals = self._load_approvals()
        for item in approvals:
            if item["task_id"] == task_id and item["tool_name"] == tool_name:
                if item["status"] == "APPROVED":
                    self.log_audit("TOOL_EXECUTED_AFTER_APPROVAL", {"approval_id": item["approval_id"], "tool": tool_name})
                    return True
                elif item["status"] == "REJECTED":
                    self.log_audit("TOOL_BLOCKED_REJECTED", {"approval_id": item["approval_id"], "tool": tool_name})
                    raise ToolRejectedError(f"Action '{tool_name}' was REJECTED by human operator. Execution strictly blocked.")
                elif item["status"] == "PENDING":
                    raise ApprovalRequiredInterrupt(ApprovalRequest(**item))

        # Create a new PENDING approval request
        req = ApprovalRequest(
            run_id=run_id,
            task_id=task_id,
            agent_id=agent_id,
            permission_level=permission_level,
            tool_name=tool_name,
            action_preview=payload,
            reason=reason
        )
        approvals.append(req.model_dump())
        self._save_approvals(approvals)
        self.log_audit("APPROVAL_REQUESTED", {"approval_id": req.approval_id, "run_id": run_id, "task_id": task_id, "tool": tool_name})
        raise ApprovalRequiredInterrupt(req)

    def resolve_approval(self, approval_id: str, decision: str, resolved_by: str = "Human Operator") -> ApprovalRequest:
        approvals = self._load_approvals()
        for item in approvals:
            if item["approval_id"] == approval_id:
                item["status"] = "APPROVED" if decision.upper() == "APPROVED" else "REJECTED"
                item["resolved_at"] = datetime.utcnow().isoformat() + "Z"
                item["resolved_by"] = resolved_by
                self._save_approvals(approvals)
                self.log_audit(f"APPROVAL_{item['status']}", {"approval_id": approval_id, "tool": item["tool_name"], "by": resolved_by})
                return ApprovalRequest(**item)
        raise ValueError(f"Approval ID {approval_id} not found")
