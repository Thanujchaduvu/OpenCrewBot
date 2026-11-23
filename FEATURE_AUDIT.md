# Feature Audit: Original OpenCrewBot vs. OpenCrewBot 2.0

| Subsystem | Original `Studio1-OSS/OpenCrewBot` | OpenCrewBot 2.0 Engineering Upgrade | Status |
| :--- | :--- | :--- | :--- |
| **Orchestration** | Single-turn message forwarding to static agent handlers | Intelligent Chief of Staff decomposing requests into multi-node DAGs with parallel execution and deliverable consolidation | **Extended / Upgraded** |
| **Agent Registry** | Hardcoded agent definitions in source files | JSON-backed Dynamic Agent Factory creating agents from natural language without source edits | **Newly Built** |
| **Collaboration** | Basic sequential chat log | Multi-agent Rooms with typed messages (`PLAN`, `DELEGATION`, `RESEARCH`, `CRITIQUE`, `VERIFICATION`, `DELIVERABLE`) and loop guards | **Extended** |
| **Task Execution** | Ephemeral in-memory loop without retries or recovery | Persistent JSON state machine tracking task IDs, dependencies, timestamps, retries, timeouts, restart recovery, and mid-run interruptions | **Newly Built** |
| **Memory** | Basic Markdown file read/write | Scoped Markdown memory (`agents/`, `rooms/`, `projects/`) with structured timestamps, provenance (`what`, `when`, `why`), and zero-cache disk hot-reload | **Extended** |
| **Skills & Tools** | Minimal tool stubs | 8 reusable Markdown skill playbooks + live Pandas CSV analyzer + GitHub/Gmail/Slack/Notion adapters | **Extended** |
| **Governance** | No permission tiers or approval blocking | 3 permission tiers (`ASK_FIRST`, `CONTROLLED_ACCESS`, `FULL_ACCESS`), Approval Centre UI, immutable audit log, hard rejection enforcement | **Newly Built** |
| **Automation** | None | APScheduler cron workflow engine with pause/resume, manual trigger, and execution history | **Newly Built** |
| **LLM Routing** | Single hardcoded model provider | Multi-provider `ModelRouter` (Gemini, OpenAI, Anthropic, Ollama) with per-agent config, fallbacks, and token/USD ledger | **Newly Built** |
