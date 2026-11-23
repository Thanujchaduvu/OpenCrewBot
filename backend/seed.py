from backend.config import AGENTS_DIR, SKILLS_DIR, ROOMS_DIR, WORKFLOWS_DIR, SAMPLES_DIR, MEMORY_DIR
from backend.models import AgentProfile, ModelConfig, CollaborationRoom, ScheduledWorkflow
from backend.orchestrator import WorkforceEngine
from backend.scheduler import WorkflowScheduler

def seed_initial_data(engine: WorkforceEngine, scheduler: WorkflowScheduler):
    # 1. Seed 8 Specialized Agents (Minimum Acceptance Criteria = 8)
    default_agents = [
        AgentProfile(
            id="chief_of_staff",
            name="Aarav — Chief of Staff",
            role="Executive Orchestrator & Deliverable Synthesizer",
            persona="Strategic operations leader who decomposes complex business goals into parallel task DAGs, verifies cross-agent outputs, and ensures board-ready quality.",
            instructions="Break requests into parallelizable tasks, enforce memory constraints, resolve agent disagreements, and assemble cohesive final reports.",
            model_config_data=ModelConfig(provider="gemini", primary_model="gemini-2.5-flash", fallback_model="gemini-2.5-flash"),
            skills=["market_research", "presentation_creation", "financial_modelling"],
            allowed_tools=["web_research", "notion_create_page"],
            permission_level="CONTROLLED_ACCESS",
            output_format="Executive Summary, Structured Tables, Strategic Recommendations."
        ),
        AgentProfile(
            id="market_intel_lead",
            name="Meera — Market Intelligence Lead",
            role="K-12 & EdTech Market Researcher",
            persona="Data-driven Indian EdTech market strategist specializing in Class 9-12 student behavior, NEP 2020 career discovery, and Aspirations positioning.",
            instructions="Gather evidence-backed market intelligence on student/parent segments, pricing tiers, and product gaps.",
            model_config_data=ModelConfig(provider="gemini", primary_model="gemini-2.5-flash", fallback_model="gemini-2.5-flash"),
            skills=["market_research", "competitor_analysis"],
            allowed_tools=["web_research"],
            permission_level="FULL_ACCESS"
        ),
        AgentProfile(
            id="competitor_analyst",
            name="Rohan — Competitive Intelligence Analyst",
            role="Study Abroad & Competitor Benchmarking Specialist",
            persona="Sharp competitive analyst tracking Leverage Edu, IDP, Mindler, Univariety, and iDreamCareer.",
            instructions="Compare competitor offerings, pricing, CAC channels, and positioning against MeetUniversity product lines.",
            model_config_data=ModelConfig(provider="gemini", primary_model="gemini-2.5-flash", fallback_model="gemini-2.5-flash"),
            skills=["competitor_analysis", "market_research"],
            allowed_tools=["web_research", "slack_post_message"],
            permission_level="ASK_FIRST"
        ),
        AgentProfile(
            id="growth_marketer",
            name="Ananya — Growth & Campaign Strategist",
            role="Student Acquisition & Brand Strategist",
            persona="Creative performance marketer crafting high-converting campaigns for Class 11 students and parents.",
            instructions="Translate audience pain points into clear messaging pillars, creative hooks, and full-funnel acquisition campaigns.",
            model_config_data=ModelConfig(provider="gemini", primary_model="gemini-2.5-flash", fallback_model="gemini-2.5-flash"),
            skills=["market_research", "presentation_creation", "email_drafting"],
            allowed_tools=["web_research", "notion_create_page"],
            permission_level="CONTROLLED_ACCESS"
        ),
        AgentProfile(
            id="content_creator",
            name="Kabir — Content & Editorial Producer",
            role="30-Day Content Calendar & Copy Specialist",
            persona="Gen-Z & parent-savvy copywriter producing Instagram Reels scripts, WhatsApp school flyers, and email sequences.",
            instructions="Deliver concrete day-by-day content calendars and ready-to-publish copy drafts.",
            model_config_data=ModelConfig(provider="gemini", primary_model="gemini-2.5-flash", fallback_model="gemini-2.5-flash"),
            skills=["email_drafting", "presentation_creation"],
            allowed_tools=["notion_create_page"],
            permission_level="CONTROLLED_ACCESS"
        ),
        AgentProfile(
            id="biz_analyst",
            name="Vikram — Revenue & Funnel Analyst",
            role="Commercial Analytics & Financial Modelling Lead",
            persona="Quantitative business analyst fluent in funnel conversion metrics, cohort LTV, ROAS, and INR/USD unit economics.",
            instructions="Run exact spreadsheet computations using spreadsheet_analyzer, pinpoint funnel leakage, and quantify revenue upside.",
            model_config_data=ModelConfig(provider="gemini", primary_model="gemini-2.5-flash", fallback_model="gemini-2.5-flash"),
            skills=["data_analysis", "financial_modelling"],
            allowed_tools=["spreadsheet_analyzer"],
            permission_level="FULL_ACCESS"
        ),
        AgentProfile(
            id="tech_lead",
            name="Siddharth — Principal Software Engineer",
            role="Repository Architecture & Engineering Lead",
            persona="Pragmatic systems engineer inspecting repositories, diagnosing concurrency/security risks, and authoring clean pull requests.",
            instructions="Inspect GitHub repositories thoroughly, prioritize technical debt, and request human approval before opening PRs or modifying code.",
            model_config_data=ModelConfig(provider="gemini", primary_model="gemini-2.5-flash", fallback_model="gemini-2.5-flash"),
            skills=["code_review"],
            allowed_tools=["github_inspect", "github_create_pr"],
            permission_level="ASK_FIRST"
        ),
        AgentProfile(
            id="qa_architect",
            name="Neha — QA & Security Governance Architect",
            role="Verification, Reliability & Compliance Reviewer",
            persona="Meticulous quality and security reviewer validating engineering plans, test coverage, and permission boundaries.",
            instructions="Challenge unverified claims, review proposed code changes, and ensure zero unauthorized external side effects.",
            model_config_data=ModelConfig(provider="gemini", primary_model="gemini-2.5-flash", fallback_model="gemini-2.5-flash"),
            skills=["code_review", "data_analysis"],
            allowed_tools=["github_inspect"],
            permission_level="FULL_ACCESS"
        ),
        AgentProfile(
            id="partnerships_lead",
            name="Priya — School Partnerships & Outreach Lead",
            role="B2B School Alliances & Lead Generation",
            persona="Relationship-driven B2B education partnerships lead connecting with CBSE/ICSE school principals.",
            instructions="Identify target partner schools, draft tailored outreach emails, and always obtain human approval before sending external emails.",
            model_config_data=ModelConfig(provider="gemini", primary_model="gemini-2.5-flash", fallback_model="gemini-2.5-flash"),
            skills=["lead_generation", "email_drafting"],
            allowed_tools=["web_research", "gmail_send_email", "slack_post_message"],
            permission_level="ASK_FIRST"
        )
    ]
    for ag in default_agents:
        if not (AGENTS_DIR / f"{ag.id}.json").exists():
            engine.save_agent(ag)

    # 2. Seed 4 Collaboration Rooms (Minimum Acceptance Criteria = 4)
    default_rooms = [
        CollaborationRoom(
            id="room_market_intel",
            name="Market Intelligence War Room",
            description="Competitive benchmarking across K-12 Career Guidance (Aspirations) and Study Abroad.",
            agent_ids=["chief_of_staff", "market_intel_lead", "competitor_analyst"]
        ),
        CollaborationRoom(
            id="room_growth_studio",
            name="Aspirations Growth & Campaign Studio",
            description="Class 11 student acquisition campaigns, audience insights, and 30-day content calendars.",
            agent_ids=["chief_of_staff", "market_intel_lead", "growth_marketer", "content_creator", "partnerships_lead"]
        ),
        CollaborationRoom(
            id="room_revops_analytics",
            name="Revenue & Funnel Analytics Room",
            description="Spreadsheet diagnostics, conversion bottleneck modeling, and unit economics.",
            agent_ids=["chief_of_staff", "biz_analyst"]
        ),
        CollaborationRoom(
            id="room_engineering_ops",
            name="Engineering & Repo Ops Room",
            description="GitHub repository audits, technical roadmaps, and approval-gated pull requests.",
            agent_ids=["chief_of_staff", "tech_lead", "qa_architect"]
        )
    ]
    for rm in default_rooms:
        if not (ROOMS_DIR / f"{rm.id}.json").exists():
            engine.save_room(rm)

    # 3. Seed 8 Reusable Skills (Minimum Acceptance Criteria = 8)
    skills_catalog = {
        "market_research": "# Market Research\n1. Segment audience by demographics, decision-makers (students vs. parents vs. schools), and pain points.\n2. Ground claims in verifiable industry pricing and adoption patterns.\n3. Conclude with actionable positioning gaps.",
        "competitor_analysis": "# Competitor Analysis\n1. Evaluate direct and indirect competitors across Product, Pricing, Target Segment, and Positioning.\n2. Present a structured Markdown comparison table.\n3. Highlight exploitable strategic moats.",
        "financial_modelling": "# Financial Modelling\n1. Report currency consistently (INR Lakhs/Crores and USD where applicable).\n2. Calculate CAC, LTV, conversion rates, and ROAS explicitly.\n3. Quantify revenue upside of proposed interventions.",
        "presentation_creation": "# Presentation Creation\n1. Structure deliverables with clear executive hierarchy: Headline Insight -> Supporting Table -> Strategic Actions.\n2. Keep bullet points concise, concrete, and decision-oriented.",
        "email_drafting": "# Email Drafting\n1. Craft high-open-rate subject lines (<60 chars).\n2. Personalize value proposition to the recipient's role.\n3. Include one clear, low-friction call to action.",
        "code_review": "# Code Review\n1. Categorize issues by Severity (CRITICAL, HIGH, MEDIUM, LOW).\n2. Cite exact file paths and architectural failure modes.\n3. Require human approval before writing branches or PRs.",
        "data_analysis": "# Data Analysis\n1. Inspect raw records programmatically before drawing conclusions.\n2. Segment conversion rates across product lines and acquisition channels.\n3. Flag statistically significant drop-offs.",
        "lead_generation": "# Lead Generation\n1. Define Ideal Customer Profile (ICP) criteria (e.g., CBSE/ICSE schools with >500 senior secondary students).\n2. Prioritize high-intent triggers and compliant outreach sequences."
    }
    for sid, content in skills_catalog.items():
        path = SKILLS_DIR / f"{sid}.md"
        if not path.exists():
            path.write_text(content, encoding="utf-8")

    # 4. Seed Sample Sales Funnel CSV for Demonstration 3
    sample_csv = SAMPLES_DIR / "meetuniversity_sales_funnel.csv"
    if not sample_csv.exists():
        sample_csv.write_text(
            "month,product_line,acquisition_channel,leads,counselled,enrolled,avg_ticket_inr,revenue_inr,ad_spend_inr\n"
            "2026-08,Aspirations,Paid Social,1200,310,62,8500,527000,240000\n"
            "2026-08,Aspirations,School Partnerships,950,610,215,7500,1612500,95000\n"
            "2026-08,Study Abroad,Organic Search,640,380,92,45000,4140000,110000\n"
            "2026-08,Study Abroad,Paid Social,820,290,41,45000,1845000,480000\n"
            "2026-08,School Partnerships,Direct B2B Outreach,140,88,34,120000,4080000,85000\n"
            "2026-09,Aspirations,Paid Social,1350,340,68,8500,578000,265000\n"
            "2026-09,Aspirations,School Partnerships,1100,740,268,7500,2010000,105000\n"
            "2026-09,Study Abroad,Organic Search,710,430,108,45000,4860000,115000\n"
            "2026-09,Study Abroad,Paid Social,900,310,45,45000,2025000,520000\n"
            "2026-09,School Partnerships,Direct B2B Outreach,165,105,42,120000,5040000,90000\n",
            encoding="utf-8"
        )

    # 5. Seed Project Markdown Memory
    proj_mem = MEMORY_DIR / "projects" / "meetuniversity.md"
    if not proj_mem.exists():
        proj_mem.write_text(
            "# Project Memory: MeetUniversity\n\n"
            "### [2026-11-23 09:00:00 UTC] | Source: System Initialization\n"
            "- **Remembered:** MeetUniversity operates three core product lines: Aspirations (student career discovery), Study Abroad / University Applications, and School Partnerships.\n"
            "- **Why:** Core business domain context required across all rooms and agents.\n",
            encoding="utf-8"
        )

    # 6. Seed Default Scheduled Workflow (Demonstration 5)
    wf_path = WORKFLOWS_DIR / "wf_weekly_competitor_pulse.json"
    if not wf_path.exists():
        scheduler.save_workflow(ScheduledWorkflow(
            workflow_id="wf_weekly_competitor_pulse",
            name="Weekly Competitor & Pricing Pulse",
            description="Monitors Mindler, Univariety, Leverage Edu, and IDP Education for pricing/product updates and compiles an executive brief.",
            room_id="room_market_intel",
            instruction="Research the competitive landscape for MeetUniversity across K-12 career guidance and Study Abroad and summarize strategic shifts.",
            cron_schedule="0 9 * * 1",
            status="ACTIVE"
        ))
