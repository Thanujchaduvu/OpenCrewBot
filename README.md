# OpenCrewBot 2.0 — Autonomous AI Workforce Operating System
loom video Link: https://www.loom.com/share/edc286f6e6bd4f498a166d2316264519

## Quick Start (Local Setup)

### 1. Prerequisites
- Python 3.10+
- Optional: API keys for OpenAI, Google Gemini, Anthropic, or a local Ollama server (`MOCK_MODE=true` works out-of-the-box with zero external keys).

### 2. Installation & Run
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment variables (keep secrets outside source code)
cp .env.example .env

# Start the OpenCrewBot 2.0 Workforce Server
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Open **http://127.0.0.1:8000** in your browser to access the OpenCrewBot 2.0 Product Interface.

### 3. Running Automated Verification Tests
```bash
pytest -v
```

---

## Implemented Modules (A–J)
- **Module A — Intelligent Chief of Staff (`backend/orchestrator.py`):** Decomposes natural-language objectives into multi-node Directed Acyclic Graphs (DAGs), assigns specialized agents, executes independent branches concurrently, and synthesizes final deliverables.
- **Module B — Dynamic Agent Creation:** Generates new agent profiles (role, persona, model, tools, skills, permission tier, output schema) from plain English and hot-loads them without code changes.
- **Module C — Multi-Agent Collaboration Rooms:** Shared rooms (`Market Intelligence`, `Aspirations Growth`, `Revenue Analytics`, `Engineering Ops`) supporting structured delegation, research sharing, peer critique, and loop prevention.
- **Module D — Autonomous DAG Task Execution Engine:** Persistent task state machine (`PENDING -> READY -> RUNNING -> AWAITING_APPROVAL -> COMPLETED/FAILED/CANCELLED`) with retries, timeouts, server-restart recovery, and mid-run user interruption handling.
- **Module E — Persistent Provenance Markdown Memory (`backend/memory_manager.py`):** Disk-backed Markdown files under `/data/memory/{agents,rooms,projects}/` recording *what* was remembered, *when*, and *why*. Hot-reloads on every agent turn so manual edits take effect immediately.
- **Module F — Reusable Skills & Tools (`backend/skills_tools.py`):** 8 Markdown skill playbooks (`market_research`, `competitor_analysis`, `financial_modelling`, `presentation_creation`, `email_drafting`, `code_review`, `data_analysis`, `lead_generation`) plus live Pandas spreadsheet analysis.
- **Module G — Human Approval & Autonomy (`backend/governance.py`):** Enforces `ASK_FIRST`, `CONTROLLED_ACCESS`, and `FULL_ACCESS` tiers with action previews, approve/reject controls, immutable audit logging, and hard execution blocks on rejected actions.
- **Module H — Integrations:** Working adapters with `[LIVE]` vs. `[SIMULATED]` status badges for **GitHub**, **Gmail SMTP**, **Slack Webhooks**, **Notion**, **Pandas Data Analyzer**, and **Web Research**.
- **Module I — Scheduled AI Workflows (`backend/scheduler.py`):** Persistent APScheduler cron engine with pause/resume, manual trigger, and execution history.
- **Module J — Multi-Model Intelligence (`backend/model_router.py`):** Configurable per-agent provider/model routing (OpenAI, Gemini, Anthropic, Ollama) with task-complexity routing, fallback models, and token/USD cost ledger.

---

## Live vs. Simulated Feature Matrix
| Component | Default (`MOCK_MODE=true`) | Live Mode (`MOCK_MODE=false` + Keys) |
| :--- | :--- | :--- |
| **DAG Orchestration, Memory, Approvals, Scheduler** | **LIVE** (Full local state & enforcement) | **LIVE** |
| **Pandas Sales Spreadsheet Analyzer** | **LIVE** (Real CSV computation) | **LIVE** |
| **LLM Completions** | **SIMULATED** (Domain-aware synthesis) | **LIVE** (Gemini / OpenAI / Anthropic / Ollama) |
| **GitHub Repo Inspection & PRs** | **SIMULATED** | **LIVE** (GitHub REST API via `GITHUB_TOKEN`) |
| **Gmail & Slack Outreach** | **SIMULATED** | **LIVE** (Gmail SMTP / Slack Webhook) |
| **Web Research** | **SIMULATED** | **LIVE** (DuckDuckGo API) |
<img width="1920" height="1080" alt="Screenshot (89)" src="https://github.com/user-attachments/assets/079bea92-10fb-42d0-82a2-0041879299ea" />
<img width="1920" height="1080" alt="Screenshot (90)" src="https://github.com/user-attachments/assets/9407cc1f-b293-4218-bc9f-792eedb4938b" />
<img width="1920" height="1080" alt="Screenshot (91)" src="https://github.com/user-attachments/assets/719e0ad6-1238-4eed-a971-51375f807f3d" />
<img width="1920" height="1080" alt="Screenshot (92)" src="https://github.com/user-attachments/assets/2a0751ae-83f7-4832-ad72-08bce8c9bc9d" />
<img width="1920" height="1080" alt="Screenshot (93)" src="https://github.com/user-attachments/assets/12a8e98d-862e-4442-a60d-d86e05b0cee1" />
<img width="1920" height="1080" alt="Screenshot (94)" src="https://github.com/user-attachments/assets/e17fa91f-c888-4987-85be-31dbc63ddabf" />
<img width="1920" height="1080" alt="Screenshot (95)" src="https://github.com/user-attachments/assets/326722dc-3b0f-4a68-b4d2-fed94c782f05" />
