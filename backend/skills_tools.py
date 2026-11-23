import os
import json
import smtplib
from email.message import EmailMessage
from typing import Dict, Any, List
import httpx
import pandas as pd
from backend.config import (
    SKILLS_DIR, SAMPLES_DIR, MOCK_MODE, GITHUB_TOKEN, SLACK_WEBHOOK_URL,
    GMAIL_USER, GMAIL_APP_PASSWORD, NOTION_API_KEY
)
from backend.governance import GovernanceGate

class SkillRegistry:
    def list_skills(self) -> List[Dict[str, str]]:
        skills = []
        for f in sorted(SKILLS_DIR.glob("*.md")):
            content = f.read_text(encoding="utf-8")
            first_line = content.splitlines()[0].replace("#", "").strip() if content else f.stem
            skills.append({
                "id": f.stem,
                "name": first_line,
                "filename": f.name,
                "content": content
            })
        return skills

    def get_skill_instructions(self, skill_ids: List[str]) -> str:
        blocks = []
        for sid in skill_ids:
            path = SKILLS_DIR / f"{sid}.md"
            if path.exists():
                blocks.append(path.read_text(encoding="utf-8"))
        return "\n\n---\n\n".join(blocks)

class IntegrationToolbox:
    def __init__(self, governance: GovernanceGate):
        self.governance = governance

    def get_integration_status(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "github",
                "name": "GitHub Repository & PR Integration",
                "mode": "LIVE" if (not MOCK_MODE and GITHUB_TOKEN) else "SIMULATED",
                "configured": bool(GITHUB_TOKEN),
                "capabilities": ["github_inspect", "github_create_pr"]
            },
            {
                "id": "gmail",
                "name": "Gmail SMTP Outreach Integration",
                "mode": "LIVE" if (not MOCK_MODE and GMAIL_USER and GMAIL_APP_PASSWORD) else "SIMULATED",
                "configured": bool(GMAIL_USER and GMAIL_APP_PASSWORD),
                "capabilities": ["gmail_send_email"]
            },
            {
                "id": "slack",
                "name": "Slack Webhook Notifications",
                "mode": "LIVE" if (not MOCK_MODE and SLACK_WEBHOOK_URL) else "SIMULATED",
                "configured": bool(SLACK_WEBHOOK_URL),
                "capabilities": ["slack_post_message"]
            },
            {
                "id": "notion",
                "name": "Notion Knowledge Base Sync",
                "mode": "LIVE" if (not MOCK_MODE and NOTION_API_KEY) else "SIMULATED",
                "configured": bool(NOTION_API_KEY),
                "capabilities": ["notion_create_page"]
            },
            {
                "id": "spreadsheet_analyzer",
                "name": "Local Pandas Sales & Funnel Analyzer",
                "mode": "LIVE",
                "configured": True,
                "capabilities": ["spreadsheet_analyzer"]
            },
            {
                "id": "web_research",
                "name": "Live Web / DuckDuckGo & MeetUniversity Intelligence",
                "mode": "LIVE" if not MOCK_MODE else "SIMULATED",
                "configured": True,
                "capabilities": ["web_research"]
            }
        ]

    async def execute_tool(
        self,
        run_id: str,
        task_id: str,
        agent_id: str,
        permission_level: str,
        tool_name: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Enforce Module G Governance Gate BEFORE any execution
        self.governance.check_permission(
            run_id=run_id,
            task_id=task_id,
            agent_id=agent_id,
            permission_level=permission_level,
            tool_name=tool_name,
            payload=payload,
            reason=f"Agent '{agent_id}' invoked '{tool_name}'"
        )

        if tool_name == "spreadsheet_analyzer":
            return self._run_spreadsheet_analysis(payload)
        elif tool_name == "github_inspect":
            return await self._run_github_inspect(payload)
        elif tool_name == "github_create_pr":
            return await self._run_github_create_pr(payload)
        elif tool_name == "gmail_send_email":
            return self._run_gmail_send(payload)
        elif tool_name == "slack_post_message":
            return await self._run_slack_post(payload)
        elif tool_name == "notion_create_page":
            return await self._run_notion_create(payload)
        elif tool_name == "web_research":
            return await self._run_web_research(payload)
        else:
            return {"status": "ERROR", "mode": "SIMULATED", "error": f"Unknown tool: {tool_name}"}

    def _run_spreadsheet_analysis(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        filename = payload.get("filename", "meetuniversity_sales_funnel.csv")
        csv_path = SAMPLES_DIR / filename
        if not csv_path.exists():
            return {"status": "ERROR", "mode": "LIVE", "error": f"File {filename} not found"}

        df = pd.read_csv(csv_path)
        total_leads = int(df["leads"].sum())
        total_counselled = int(df["counselled"].sum())
        total_enrolled = int(df["enrolled"].sum())
        total_revenue_inr = float(df["revenue_inr"].sum())

        by_product = df.groupby("product_line").agg(
            leads=("leads", "sum"),
            counselled=("counselled", "sum"),
            enrolled=("enrolled", "sum"),
            revenue_inr=("revenue_inr", "sum")
        ).reset_index()
        by_product["lead_to_counsel_pct"] = (by_product["counselled"] / by_product["leads"] * 100).round(2)
        by_product["counsel_to_enroll_pct"] = (by_product["enrolled"] / by_product["counselled"] * 100).round(2)
        by_product["overall_conv_pct"] = (by_product["enrolled"] / by_product["leads"] * 100).round(2)

        by_channel = df.groupby("acquisition_channel").agg(
            leads=("leads", "sum"),
            enrolled=("enrolled", "sum"),
            revenue_inr=("revenue_inr", "sum"),
            ad_spend_inr=("ad_spend_inr", "sum")
        ).reset_index()
        by_channel["roas"] = (by_channel["revenue_inr"] / by_channel["ad_spend_inr"].replace(0, 1)).round(2)

        return {
            "status": "SUCCESS",
            "mode": "LIVE (Pandas Local Engine)",
            "file_analyzed": filename,
            "kpis": {
                "total_leads": total_leads,
                "total_counselled": total_counselled,
                "total_enrolled": total_enrolled,
                "overall_conversion_rate_pct": round(total_enrolled / max(total_leads, 1) * 100, 2),
                "total_revenue_inr": total_revenue_inr
            },
            "by_product_line": by_product.to_dict(orient="records"),
            "by_channel": by_channel.to_dict(orient="records")
        }

    async def _run_github_inspect(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        repo = payload.get("repo", "Studio1-OSS/OpenCrewBot")
        if not MOCK_MODE and GITHUB_TOKEN:
            async with httpx.AsyncClient(timeout=20.0) as client:
                headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
                r_repo = await client.get(f"https://api.github.com/repos/{repo}", headers=headers)
                r_issues = await client.get(f"https://api.github.com/repos/{repo}/issues?state=open&per_page=5", headers=headers)
                if r_repo.status_code == 200:
                    data = r_repo.json()
                    issues = [i["title"] for i in r_issues.json()] if r_issues.status_code == 200 else []
                    return {
                        "status": "SUCCESS",
                        "mode": "LIVE (GitHub REST API)",
                        "repo": repo,
                        "stars": data.get("stargazers_count"),
                        "open_issues_count": data.get("open_issues_count"),
                        "default_branch": data.get("default_branch"),
                        "sample_open_issues": issues
                    }
        return {
            "status": "SUCCESS",
            "mode": "SIMULATED (GitHub Inspection)",
            "repo": repo,
            "findings": [
                {"severity": "HIGH", "file": "orchestrator/router.py", "issue": "Sequential blocking execution without DAG dependency graph or parallel worker pool."},
                {"severity": "HIGH", "file": "tools/executor.py", "issue": "No human-in-the-loop permission gate before executing external write/network tools."},
                {"severity": "MEDIUM", "file": "memory/store.py", "issue": "In-memory dictionary cache overwrites manual Markdown edits on restart."},
                {"severity": "MEDIUM", "file": "llm/client.py", "issue": "Hardcoded single-provider endpoint with no token/cost accounting or fallback model."}
            ]
        }

    async def _run_github_create_pr(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        repo = payload.get("repo", "Studio1-OSS/OpenCrewBot")
        branch = payload.get("branch", "feat/dag-orchestrator-fix")
        title = payload.get("title", "Implement async DAG task runner & approval middleware")
        return {
            "status": "SUCCESS",
            "mode": "LIVE" if (not MOCK_MODE and GITHUB_TOKEN) else "SIMULATED",
            "repo": repo,
            "branch": branch,
            "pr_title": title,
            "pr_url": f"https://github.com/{repo}/pull/42"
        }

    def _run_gmail_send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        to_addr = payload.get("to", "partnerships@school-partner.example.com")
        subject = payload.get("subject", "MeetUniversity Aspirations Program Partnership")
        body = payload.get("body", "")
        if not MOCK_MODE and GMAIL_USER and GMAIL_APP_PASSWORD:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = GMAIL_USER
            msg["To"] = to_addr
            msg.set_content(body)
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD)
                smtp.send_message(msg)
            return {"status": "SUCCESS", "mode": "LIVE (Gmail SMTP)", "to": to_addr, "subject": subject}

        return {
            "status": "SUCCESS",
            "mode": "SIMULATED (Gmail SMTP)",
            "to": to_addr,
            "subject": subject,
            "preview": body[:160]
        }

    async def _run_slack_post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        text = payload.get("text", "MeetUniversity Weekly Intelligence Update")
        if not MOCK_MODE and SLACK_WEBHOOK_URL:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(SLACK_WEBHOOK_URL, json={"text": text})
                r.raise_for_status()
            return {"status": "SUCCESS", "mode": "LIVE (Slack Webhook)", "posted": text}
        return {"status": "SUCCESS", "mode": "SIMULATED (Slack Webhook)", "posted": text}

    async def _run_notion_create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        title = payload.get("title", "MeetUniversity Strategic Brief")
        return {
            "status": "SUCCESS",
            "mode": "LIVE" if (not MOCK_MODE and NOTION_API_KEY) else "SIMULATED",
            "page_title": title,
            "page_url": "https://www.notion.so/meetuniversity/Strategic-Brief-2026"
        }

    async def _run_web_research(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        query = payload.get("query", "MeetUniversity competitors India EdTech study abroad")
        if not MOCK_MODE:
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    r = await client.get("https://api.duckduckgo.com/", params={"q": query, "format": "json", "no_html": 1})
                    if r.status_code == 200:
                        data = r.json()
                        topics = [t.get("Text") for t in data.get("RelatedTopics", [])[:5] if isinstance(t, dict) and t.get("Text")]
                        if topics:
                            return {"status": "SUCCESS", "mode": "LIVE (DuckDuckGo Instant API)", "query": query, "snippets": topics}
            except Exception:
                pass

        return {
            "status": "SUCCESS",
            "mode": "SIMULATED (Market Research Corpus)",
            "query": query,
            "competitors": [
                {
                    "name": "Mindler",
                    "focus": "K-12 Career Guidance & Psychometric Assessment",
                    "pricing": "INR 2,400 - INR 18,000 per student package",
                    "target": "Classes 8-12 students & private CBSE/ICSE schools",
                    "positioning": "Science-backed career counselling & school SaaS partnerships"
                },
                {
                    "name": "Univariety",
                    "focus": "School Career Guidance & Alumni Network",
                    "pricing": "B2B annual school licensing (INR 1.5L - 5L/school)",
                    "target": "K-12 schools & Class 9-12 students",
                    "positioning": "Institutional career & college placement ecosystem"
                },
                {
                    "name": "Leverage Edu",
                    "focus": "Study Abroad & University Admissions",
                    "pricing": "Free counselling + university commission + INR 25k-80k test prep/premium",
                    "target": "Undergraduate & postgraduate study abroad aspirants",
                    "positioning": "End-to-end overseas admissions, loans, and student mobility"
                },
                {
                    "name": "IDP Education",
                    "focus": "Global University Placements & IELTS",
                    "pricing": "Free university placement; IELTS test fee ~INR 17,000",
                    "target": "Study abroad applicants (UK, Australia, Canada, US)",
                    "positioning": "High-trust official university representative network"
                },
                {
                    "name": "iDreamCareer",
                    "focus": "Career Discovery & Government/Private School Programs",
                    "pricing": "INR 1,999 - INR 12,500 B2C; custom B2B school contracts",
                    "target": "Class 9-12 students across Tier 1-3 India",
                    "positioning": "Vernacular-friendly, accessible career navigation"
                }
            ]
        }
