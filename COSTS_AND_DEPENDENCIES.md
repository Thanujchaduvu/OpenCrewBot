# External Dependencies, Licences & Cost Breakdown

## 1. Software Dependencies & Licence Verification
- **Original Repository:** `Studio1-OSS/OpenCrewBot` — **MIT License** (retained in `LICENSE` and `README.md`).
- **FastAPI / Uvicorn / Pydantic / HTTPX / Pytest:** MIT / BSD Licenses.
- **Pandas / OpenPyXL:** BSD-3-Clause / MIT Licenses.
- **APScheduler:** MIT License.
- **Tailwind CSS (CDN):** MIT License.

## 2. Model & API Cost Breakdown (Estimated per 1,000 Tokens)
| Provider | Model | Input Cost / 1K | Output Cost / 1K | Role in OpenCrewBot 2.0 |
| :--- | :--- | :--- | :--- | :--- |
| **Google** | `gemini-2.5-pro` | $0.00125 | $0.00500 | Chief of Staff planning & complex synthesis |
| **Google** | `gemini-2.5-flash` | $0.000075 | $0.00030 | High-speed research, content & outreach agents |
| **OpenAI** | `gpt-4o` | $0.00250 | $0.01000 | Quantitative & financial analysis fallback |
| **OpenAI** | `gpt-4o-mini` | $0.00015 | $0.00060 | Fast classification & fallback |
| **Anthropic** | `claude-3-5-sonnet` | $0.00300 | $0.01500 | Code review & repository architecture |
| **Local (Ollama)** | `ollama/llama3` | $0.00000 | $0.00000 | Zero-cost offline local inference |

## 3. Infrastructure & Known Limitations
- **Infrastructure Cost:** $0.00 locally (SQLite/JSON + Markdown filesystem storage requires zero external cloud databases).
- **Known Limitations:**
  1. JSON/Markdown file locking assumes single-node deployment; high-concurrency multi-worker deployments should swap storage adapters to PostgreSQL.
  2. Live external integrations (`GitHub`, `Gmail`, `Slack`, `Notion`) gracefully fall back to `[SIMULATED]` mode when API keys are omitted from `.env`.
