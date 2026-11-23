# OpenCrewBot 2.0 — System Architecture

## 1. High-Level Component Diagram

```
+-------------------------------------------------------------------+
|               Web Product Interface (frontend/index.html)         |
|  Rooms | DAG Dashboard | Approval Centre | Memory | Agents | Cost |
+---------------------------------+---------------------------------+
                                  | REST / JSON
+---------------------------------v---------------------------------+
|                   FastAPI Gateway (backend/main.py)               |
+--------+----------------+----------------+---------------+--------+
         |                |                |               |
+--------v--------+ +-----v------+ +-------v-------+ +-----v--------+
| WorkforceEngine | | Governance | | MemoryManager | |  Workflow    |
| (Chief of Staff | |    Gate    | |  (Disk-First  | |  Scheduler   |
|  & DAG Runner)  | | (3 Tiers)  | |   Markdown)   | | (APScheduler)|
+--------+--------+ +-----+------+ +-------+-------+ +--------------+
         |                |                |
         +-------+--------+--------+-------+
                 |                 |
        +--------v--------+ +------v-----------+
        |   ModelRouter   | | IntegrationTools |
        | Gemini / OpenAI | | GitHub / Gmail / |
        | Anthropic/Ollama| | Slack / Pandas   |
        +-----------------+ +------------------+
```

## 2. Execution Flow & Approval Enforcement
1. **Planning:** User submits an objective to a Collaboration Room. `WorkforceEngine.plan_dag()` decomposes the goal into a `TaskNode` DAG with explicit `dependencies`.
2. **Parallel Scheduling:** `_execute_dag_loop()` identifies all `PENDING` tasks whose `dependencies` are `COMPLETED` and executes them concurrently via `asyncio.gather()`.
3. **Governance Interception:** Before any tool runs, `IntegrationToolbox.execute_tool()` calls `GovernanceGate.check_permission()`.
   - If the agent's tier is `ASK_FIRST` and the tool is an external action (`gmail_send_email`, `github_create_pr`, `slack_post_message`), execution raises `ApprovalRequiredInterrupt`, transitions the task to `AWAITING_APPROVAL`, and publishes an Action Preview to the Approval Centre.
   - If rejected, `ToolRejectedError` is raised and the underlying network/API call is **never invoked**.
4. **Live Disk Memory Hot-Reload:** At the start of every task turn, `MemoryManager.build_context_bundle()` reads `/data/memory/{projects,rooms,agents}/*.md` directly from disk so any human edits apply immediately.
5. **Mid-Run Interruption:** Calling `/api/runs/{run_id}/interrupt` injects a dynamic adaptation node into the active DAG and re-wires downstream synthesis tasks without losing completed upstream work.
