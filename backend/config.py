import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
AGENTS_DIR = DATA_DIR / "agents"
SKILLS_DIR = DATA_DIR / "skills"
MEMORY_DIR = DATA_DIR / "memory"
ROOMS_DIR = DATA_DIR / "rooms"
WORKFLOWS_DIR = DATA_DIR / "workflows"
RUNS_DIR = DATA_DIR / "runs"
SAMPLES_DIR = DATA_DIR / "samples"

for d in [AGENTS_DIR, SKILLS_DIR, MEMORY_DIR / "agents", MEMORY_DIR / "rooms",
          MEMORY_DIR / "projects", ROOMS_DIR, WORKFLOWS_DIR, RUNS_DIR, SAMPLES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
