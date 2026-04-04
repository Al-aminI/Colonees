"""
Use Case Templates
Pre-built configurations for common use cases that create colonees,
workspaces, and knowledge base placeholders in one step.

Each template defines a complete agent swarm configuration for a specific
domain: the colonees to create, the MCP servers to suggest, the workspace
layout, and what knowledge to upload.

Templates are read-only and registered at import time.
"""

import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class UseCaseTemplate:
    name: str                                        # slug: "customer_support"
    display_name: str                                # "Customer Support"
    description: str                                 # detailed description
    category: str                                    # e.g. "support", "legal", ...
    icon: str                                        # emoji
    color: str                                       # hex color for UI
    colonees: List[Dict[str, Any]]                   # colonee definitions
    mcp_server_suggestions: List[Dict[str, Any]]     # suggested MCP servers
    workspace_config: Dict[str, Any]                 # workspace to create
    recommended_knowledge_bases: List[str]            # descriptions of data to upload
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class TemplateRegistry:
    """Registry of pre-built use case templates."""

    def __init__(self):
        self._templates: Dict[str, UseCaseTemplate] = {}
        self._register_builtin_templates()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_templates(self, category: Optional[str] = None) -> List[UseCaseTemplate]:
        """Return all templates, optionally filtered by category."""
        templates = list(self._templates.values())
        if category:
            templates = [t for t in templates if t.category == category]
        return templates

    def get_template(self, name: str) -> Optional[UseCaseTemplate]:
        """Return a single template by slug name, or None."""
        return self._templates.get(name)

    def get_categories(self) -> List[Dict[str, str]]:
        """Return a deduplicated list of categories with counts."""
        cats: Dict[str, Dict[str, Any]] = {}
        for t in self._templates.values():
            if t.category not in cats:
                cats[t.category] = {
                    "name": t.category,
                    "display_name": t.category.replace("_", " ").title(),
                    "icon": t.icon,
                    "count": 0,
                }
            cats[t.category]["count"] += 1
        return list(cats.values())

    # ------------------------------------------------------------------
    # Built-in templates
    # ------------------------------------------------------------------

    def _register_builtin_templates(self) -> None:
        for tpl in _BUILTIN_TEMPLATES:
            self._templates[tpl.name] = tpl
        logger.info("Registered %d built-in use-case templates", len(_BUILTIN_TEMPLATES))


# ---------------------------------------------------------------------------
# Template definitions
# ---------------------------------------------------------------------------

_BUILTIN_TEMPLATES: List[UseCaseTemplate] = [
    # ── 1. Customer Support ──────────────────────────────────────────────
    UseCaseTemplate(
        name="customer_support",
        display_name="Customer Support",
        description=(
            "A complete customer support swarm that handles FAQs, classifies "
            "incoming tickets, escalates complex issues, and analyzes customer "
            "feedback to surface actionable insights."
        ),
        category="support",
        icon="\U0001f3a7",   # headphones
        color="#3b82f6",
        colonees=[
            {
                "name": "faq_agent",
                "display_name": "FAQ Agent",
                "description": "Answers frequently asked questions from the knowledge base",
                "specialist_type": "researcher",
                "system_prompt": (
                    "You are a FAQ specialist for {specialization}. Your primary role is to "
                    "answer customer questions accurately by searching the knowledge base. "
                    "Always cite the specific article or document that supports your answer. "
                    "If the answer is not in the knowledge base, clearly state that you do not "
                    "have that information and suggest the customer contact a human agent. "
                    "Keep responses concise, friendly, and solution-oriented. Avoid jargon "
                    "unless the customer uses it first."
                ),
                "capabilities": ["faq_answering", "knowledge_search", "customer_communication"],
                "built_in_tools": ["file", "research"],
                "tags": ["customer_support", "faq"],
            },
            {
                "name": "ticket_classifier",
                "display_name": "Ticket Classifier",
                "description": "Classifies and prioritizes incoming support tickets",
                "specialist_type": "analyst",
                "system_prompt": (
                    "You are a support ticket classification specialist for {specialization}. "
                    "Analyze each incoming ticket to determine its category, priority level, "
                    "and the appropriate team or agent to handle it. Use categories such as "
                    "billing, technical, account, product feedback, and general inquiry. "
                    "Assign priority as critical, high, medium, or low based on business impact "
                    "and customer sentiment. Provide a brief rationale for your classification "
                    "so routing decisions are transparent and auditable."
                ),
                "capabilities": ["text_classification", "sentiment_analysis", "ticket_routing"],
                "built_in_tools": ["computation"],
                "tags": ["customer_support", "classification"],
            },
            {
                "name": "escalation_handler",
                "display_name": "Escalation Handler",
                "description": "Manages complex issues that require escalation to human agents",
                "specialist_type": "domain_expert",
                "system_prompt": (
                    "You are an escalation specialist for {specialization}. You handle "
                    "tickets that automated agents could not resolve or that customers have "
                    "flagged as urgent. Gather all relevant context from prior interactions, "
                    "summarize the issue clearly, and prepare a handoff brief for the human "
                    "support team. Include the customer's history, attempted resolutions, and "
                    "your recommended next steps. Always maintain an empathetic, professional "
                    "tone and keep the customer informed about the escalation timeline."
                ),
                "capabilities": ["escalation_management", "context_gathering", "handoff_preparation"],
                "built_in_tools": ["file", "research"],
                "tags": ["customer_support", "escalation"],
            },
            {
                "name": "feedback_analyzer",
                "display_name": "Feedback Analyzer",
                "description": "Analyzes customer feedback to surface trends and insights",
                "specialist_type": "analyst",
                "system_prompt": (
                    "You are a customer feedback analyst for {specialization}. Aggregate "
                    "feedback from surveys, support tickets, and direct messages to identify "
                    "recurring themes, sentiment trends, and product improvement opportunities. "
                    "Produce structured reports with quantified findings: top complaint categories, "
                    "NPS drivers, and satisfaction trends over time. Highlight urgent issues that "
                    "need immediate attention and suggest concrete product or process improvements "
                    "backed by data."
                ),
                "capabilities": ["sentiment_analysis", "trend_detection", "report_generation"],
                "built_in_tools": ["computation", "file"],
                "tags": ["customer_support", "analytics"],
            },
        ],
        mcp_server_suggestions=[
            {"name": "zendesk", "description": "Connect to Zendesk for ticket management and customer history", "transport": "streamable_http"},
            {"name": "slack", "description": "Send escalation notifications and updates to Slack channels", "transport": "streamable_http"},
            {"name": "intercom", "description": "Access Intercom conversations and customer profiles", "transport": "streamable_http"},
        ],
        workspace_config={
            "display_name": "Customer Support",
            "description": "Workspace for customer support operations with FAQ, ticketing, escalation, and feedback analysis.",
            "icon": "\U0001f3a7",
            "color": "#3b82f6",
        },
        recommended_knowledge_bases=[
            "Product documentation and FAQ articles",
            "Internal support playbooks and troubleshooting guides",
            "Common issue resolution templates",
            "SLA policies and escalation procedures",
        ],
        tags=["customer_support", "support", "tickets", "feedback"],
    ),

    # ── 2. Legal ─────────────────────────────────────────────────────────
    UseCaseTemplate(
        name="legal",
        display_name="Legal",
        description=(
            "A legal operations swarm that reviews contracts, checks regulatory "
            "compliance, conducts legal research, and produces concise case summaries "
            "for attorneys and compliance teams."
        ),
        category="legal",
        icon="\u2696\ufe0f",   # scales
        color="#8b5cf6",
        colonees=[
            {
                "name": "contract_analyzer",
                "display_name": "Contract Analyzer",
                "description": "Reviews and analyzes contracts for risks, obligations, and key terms",
                "specialist_type": "analyst",
                "system_prompt": (
                    "You are a contract analysis specialist for {specialization}. Review "
                    "contracts to identify key clauses, obligations, termination conditions, "
                    "liability caps, indemnification terms, and potential risks. Flag unusual "
                    "or non-standard language and compare terms against company benchmarks. "
                    "Produce a structured summary listing parties, effective dates, key obligations, "
                    "risk areas, and recommended negotiation points. Always note which clauses "
                    "deviate from standard templates."
                ),
                "capabilities": ["contract_review", "risk_identification", "clause_extraction", "document_analysis"],
                "built_in_tools": ["file", "research"],
                "tags": ["legal", "contracts"],
            },
            {
                "name": "compliance_checker",
                "display_name": "Compliance Checker",
                "description": "Checks documents and processes against regulatory requirements",
                "specialist_type": "domain_expert",
                "system_prompt": (
                    "You are a regulatory compliance specialist for {specialization}. Evaluate "
                    "documents, policies, and processes against applicable regulations such as "
                    "GDPR, SOX, HIPAA, or industry-specific frameworks. Identify gaps, non-compliant "
                    "language, and missing disclosures. Provide actionable remediation recommendations "
                    "with specific regulatory references. Maintain a checklist-driven approach so "
                    "that compliance status can be tracked systematically across the organization."
                ),
                "capabilities": ["regulatory_analysis", "compliance_assessment", "gap_identification"],
                "built_in_tools": ["file", "research"],
                "tags": ["legal", "compliance"],
            },
            {
                "name": "legal_researcher",
                "display_name": "Legal Researcher",
                "description": "Conducts legal research on case law, statutes, and regulations",
                "specialist_type": "researcher",
                "system_prompt": (
                    "You are a legal research specialist for {specialization}. Conduct thorough "
                    "research on case law, statutes, regulatory guidance, and legal precedents "
                    "relevant to the matter at hand. Synthesize findings into well-organized "
                    "memoranda with proper citations. Identify supporting and opposing authorities, "
                    "note jurisdictional differences, and assess the strength of legal arguments. "
                    "Present your findings in a format suitable for attorney review with clear "
                    "headings and citation formatting."
                ),
                "capabilities": ["legal_research", "case_law_analysis", "citation_management", "memorandum_drafting"],
                "built_in_tools": ["research", "file"],
                "tags": ["legal", "research"],
            },
            {
                "name": "case_summarizer",
                "display_name": "Case Summarizer",
                "description": "Produces concise summaries of legal cases, filings, and proceedings",
                "specialist_type": "analyst",
                "system_prompt": (
                    "You are a case summarization specialist for {specialization}. Read "
                    "court filings, depositions, and case documents to produce clear, concise "
                    "summaries for attorneys and stakeholders. Extract the key facts, legal "
                    "issues, holdings, and reasoning. Highlight relevant precedents cited by "
                    "the court and note any dissenting opinions. Keep summaries structured "
                    "with sections for facts, procedural history, issues, holding, and "
                    "practical implications."
                ),
                "capabilities": ["document_summarization", "key_fact_extraction", "legal_writing"],
                "built_in_tools": ["file", "research"],
                "tags": ["legal", "summarization"],
            },
        ],
        mcp_server_suggestions=[
            {"name": "westlaw", "description": "Search Westlaw for case law, statutes, and legal commentary", "transport": "streamable_http"},
            {"name": "docusign", "description": "Access and manage contracts through DocuSign", "transport": "streamable_http"},
            {"name": "sharepoint", "description": "Access internal legal document repositories", "transport": "streamable_http"},
        ],
        workspace_config={
            "display_name": "Legal Operations",
            "description": "Workspace for legal operations including contract review, compliance, research, and case management.",
            "icon": "\u2696\ufe0f",
            "color": "#8b5cf6",
        },
        recommended_knowledge_bases=[
            "Standard contract templates and clause libraries",
            "Applicable regulatory frameworks and compliance checklists",
            "Internal legal policies and procedures",
            "Prior case summaries and research memoranda",
        ],
        tags=["legal", "contracts", "compliance", "research"],
    ),

    # ── 3. Finance ───────────────────────────────────────────────────────
    UseCaseTemplate(
        name="finance",
        display_name="Finance",
        description=(
            "A finance swarm that performs financial analysis, assesses risk, "
            "generates reports, and conducts market research to support "
            "investment decisions and financial planning."
        ),
        category="finance",
        icon="\U0001f4b0",   # money bag
        color="#10b981",
        colonees=[
            {
                "name": "financial_analyst",
                "display_name": "Financial Analyst",
                "description": "Analyzes financial data, statements, and metrics",
                "specialist_type": "analyst",
                "system_prompt": (
                    "You are a financial analysis specialist for {specialization}. Analyze "
                    "financial statements, key performance indicators, and operational metrics "
                    "to assess company health and performance. Calculate and interpret ratios "
                    "such as ROE, ROIC, debt-to-equity, and margin trends. Build financial "
                    "models and projections when requested. Present findings in structured "
                    "reports with tables, charts, and clear executive summaries. Always state "
                    "your assumptions and data sources explicitly."
                ),
                "capabilities": ["financial_analysis", "ratio_analysis", "financial_modeling", "report_generation"],
                "built_in_tools": ["computation", "file"],
                "tags": ["finance", "analysis"],
            },
            {
                "name": "risk_assessor",
                "display_name": "Risk Assessor",
                "description": "Evaluates financial and operational risks",
                "specialist_type": "domain_expert",
                "system_prompt": (
                    "You are a risk assessment specialist for {specialization}. Identify, "
                    "quantify, and prioritize financial, operational, and market risks. Evaluate "
                    "exposure across credit, liquidity, interest rate, and operational dimensions. "
                    "Use scenario analysis and stress testing to model potential outcomes. Produce "
                    "risk matrices and mitigation recommendations ranked by likelihood and impact. "
                    "Communicate risk findings clearly to both technical and non-technical "
                    "stakeholders."
                ),
                "capabilities": ["risk_analysis", "scenario_modeling", "stress_testing", "risk_reporting"],
                "built_in_tools": ["computation", "research"],
                "tags": ["finance", "risk"],
            },
            {
                "name": "report_generator",
                "display_name": "Report Generator",
                "description": "Generates financial reports, summaries, and presentations",
                "specialist_type": "executor",
                "system_prompt": (
                    "You are a financial report generation specialist for {specialization}. "
                    "Compile data from multiple sources into professional financial reports, "
                    "board presentations, and investor updates. Structure reports with executive "
                    "summaries, detailed findings, supporting data tables, and appendices. "
                    "Ensure numerical accuracy by cross-referencing source data. Adapt tone "
                    "and depth based on the target audience: board members, investors, or "
                    "internal management teams."
                ),
                "capabilities": ["report_generation", "data_compilation", "presentation_creation"],
                "built_in_tools": ["file", "computation", "media"],
                "tags": ["finance", "reporting"],
            },
            {
                "name": "market_researcher",
                "display_name": "Market Researcher",
                "description": "Researches market trends, competitors, and economic indicators",
                "specialist_type": "researcher",
                "system_prompt": (
                    "You are a market research specialist for {specialization}. Monitor and "
                    "analyze market trends, competitive landscapes, and macroeconomic indicators "
                    "relevant to investment decisions. Gather data from public filings, industry "
                    "reports, and news sources. Produce competitive analysis reports, market "
                    "sizing estimates, and trend summaries. Cite all sources and clearly "
                    "distinguish between established data and forward-looking projections or "
                    "your own analysis."
                ),
                "capabilities": ["market_research", "competitive_analysis", "trend_analysis", "information_synthesis"],
                "built_in_tools": ["research", "computation"],
                "tags": ["finance", "market_research"],
            },
        ],
        mcp_server_suggestions=[
            {"name": "bloomberg", "description": "Access Bloomberg financial data and market feeds", "transport": "streamable_http"},
            {"name": "quickbooks", "description": "Connect to QuickBooks for accounting data", "transport": "streamable_http"},
            {"name": "plaid", "description": "Access banking and transaction data via Plaid", "transport": "streamable_http"},
        ],
        workspace_config={
            "display_name": "Finance",
            "description": "Workspace for financial analysis, risk assessment, reporting, and market research.",
            "icon": "\U0001f4b0",
            "color": "#10b981",
        },
        recommended_knowledge_bases=[
            "Historical financial statements and earnings reports",
            "Internal risk policies and tolerance thresholds",
            "Industry benchmarks and peer comparison data",
            "Market research reports and economic forecasts",
        ],
        tags=["finance", "analysis", "risk", "market_research"],
    ),

    # ── 4. Research ──────────────────────────────────────────────────────
    UseCaseTemplate(
        name="research",
        display_name="Research",
        description=(
            "An academic and corporate research swarm that reviews literature, "
            "analyzes data, generates hypotheses, and manages citations to "
            "accelerate the research process."
        ),
        category="research",
        icon="\U0001f52c",   # microscope
        color="#6366f1",
        colonees=[
            {
                "name": "literature_reviewer",
                "display_name": "Literature Reviewer",
                "description": "Searches, filters, and synthesizes academic and industry literature",
                "specialist_type": "researcher",
                "system_prompt": (
                    "You are a literature review specialist for {specialization}. Systematically "
                    "search and evaluate academic papers, preprints, industry reports, and technical "
                    "documentation relevant to the research question. Assess each source for "
                    "methodology quality, relevance, and recency. Synthesize findings into "
                    "thematic summaries that identify consensus, contradictions, and gaps in the "
                    "existing body of work. Use proper academic citation format and maintain a "
                    "bibliography for every review you produce."
                ),
                "capabilities": ["literature_search", "source_evaluation", "thematic_synthesis", "citation_formatting"],
                "built_in_tools": ["research", "file"],
                "tags": ["research", "literature_review"],
            },
            {
                "name": "data_analyst_research",
                "display_name": "Data Analyst",
                "description": "Performs statistical analysis and data exploration for research",
                "specialist_type": "analyst",
                "system_prompt": (
                    "You are a research data analyst for {specialization}. Clean, explore, and "
                    "analyze datasets using appropriate statistical methods. Select the right "
                    "tests and models based on data characteristics: normality, sample size, "
                    "and variable types. Produce reproducible analysis with clear documentation "
                    "of your methodology, assumptions, and limitations. Visualize results using "
                    "charts and tables that communicate findings effectively. Flag any data "
                    "quality issues you discover during analysis."
                ),
                "capabilities": ["statistical_analysis", "data_exploration", "visualization", "methodology_design"],
                "built_in_tools": ["computation", "file"],
                "tags": ["research", "data_analysis"],
            },
            {
                "name": "hypothesis_generator",
                "display_name": "Hypothesis Generator",
                "description": "Generates and evaluates research hypotheses based on existing evidence",
                "specialist_type": "domain_expert",
                "system_prompt": (
                    "You are a hypothesis generation specialist for {specialization}. Given a "
                    "research question and existing findings, propose testable hypotheses that "
                    "address gaps in current knowledge. For each hypothesis, articulate the "
                    "rationale, identify the variables involved, suggest experimental or "
                    "observational designs to test it, and predict expected outcomes. Evaluate "
                    "feasibility considering available data, tools, and resources. Rank hypotheses "
                    "by potential impact and testability."
                ),
                "capabilities": ["hypothesis_formulation", "experimental_design", "critical_evaluation", "research_planning"],
                "built_in_tools": ["research", "computation"],
                "tags": ["research", "hypothesis"],
            },
            {
                "name": "citation_manager",
                "display_name": "Citation Manager",
                "description": "Organizes references, formats citations, and checks bibliographic accuracy",
                "specialist_type": "executor",
                "system_prompt": (
                    "You are a citation and reference management specialist for {specialization}. "
                    "Collect, organize, and format bibliographic references in any required style "
                    "(APA, MLA, Chicago, IEEE, Vancouver). Verify citation accuracy by cross-referencing "
                    "DOIs, titles, and author names against source databases. Detect duplicate "
                    "references and inconsistent formatting. Generate formatted bibliographies "
                    "and in-text citations ready for insertion into manuscripts. Maintain a "
                    "structured reference library for the project."
                ),
                "capabilities": ["citation_formatting", "reference_management", "bibliography_generation", "duplicate_detection"],
                "built_in_tools": ["file", "research"],
                "tags": ["research", "citations"],
            },
        ],
        mcp_server_suggestions=[
            {"name": "semantic_scholar", "description": "Search academic papers via Semantic Scholar API", "transport": "streamable_http"},
            {"name": "zotero", "description": "Manage references and bibliographies in Zotero", "transport": "streamable_http"},
            {"name": "google_scholar", "description": "Search Google Scholar for academic literature", "transport": "streamable_http"},
            {"name": "jupyter", "description": "Execute data analysis in Jupyter notebooks", "transport": "stdio"},
        ],
        workspace_config={
            "display_name": "Research",
            "description": "Workspace for academic and corporate research with literature review, data analysis, and hypothesis generation.",
            "icon": "\U0001f52c",
            "color": "#6366f1",
        },
        recommended_knowledge_bases=[
            "Collected papers and references for the research domain",
            "Datasets and data dictionaries",
            "Prior research notes and draft manuscripts",
            "Methodology guidelines and statistical references",
        ],
        tags=["research", "academic", "data_analysis", "literature"],
    ),

    # ── 5. Software Engineering ──────────────────────────────────────────
    UseCaseTemplate(
        name="software_engineering",
        display_name="Software Engineering",
        description=(
            "A software engineering swarm that reviews code, investigates bugs, "
            "writes documentation, and generates tests to improve code quality "
            "and developer productivity."
        ),
        category="engineering",
        icon="\U0001f4bb",   # laptop
        color="#f59e0b",
        colonees=[
            {
                "name": "code_reviewer",
                "display_name": "Code Reviewer",
                "description": "Reviews code for quality, security, and adherence to best practices",
                "specialist_type": "analyst",
                "system_prompt": (
                    "You are a code review specialist for {specialization}. Review code changes "
                    "for correctness, readability, performance, and security vulnerabilities. "
                    "Check adherence to the project's coding standards, naming conventions, and "
                    "architectural patterns. Identify potential bugs, race conditions, and edge "
                    "cases. Provide constructive feedback with specific suggestions and code "
                    "examples. Prioritize your comments by severity: blocking issues first, "
                    "then improvements, then style nits."
                ),
                "capabilities": ["code_review", "security_analysis", "performance_review", "best_practices"],
                "built_in_tools": ["file", "computation"],
                "tags": ["engineering", "code_review"],
            },
            {
                "name": "bug_investigator",
                "display_name": "Bug Investigator",
                "description": "Investigates bugs by analyzing logs, stack traces, and code paths",
                "specialist_type": "researcher",
                "system_prompt": (
                    "You are a bug investigation specialist for {specialization}. Analyze bug "
                    "reports, error logs, and stack traces to identify root causes. Trace code "
                    "execution paths to understand how the bug manifests. Reproduce issues when "
                    "possible and document the exact conditions under which they occur. Propose "
                    "targeted fixes with an assessment of potential side effects. Include "
                    "regression test suggestions to prevent the issue from recurring."
                ),
                "capabilities": ["debugging", "log_analysis", "root_cause_analysis", "reproduction_steps"],
                "built_in_tools": ["file", "research", "computation"],
                "tags": ["engineering", "debugging"],
            },
            {
                "name": "documentation_writer",
                "display_name": "Documentation Writer",
                "description": "Writes and maintains technical documentation, API docs, and guides",
                "specialist_type": "executor",
                "system_prompt": (
                    "You are a technical documentation specialist for {specialization}. Write "
                    "clear, accurate documentation for APIs, libraries, architecture decisions, "
                    "and developer guides. Analyze source code to generate accurate API references "
                    "with parameter descriptions, return types, and usage examples. Keep documentation "
                    "consistent in style and tone with existing project docs. Include code samples "
                    "that compile and run correctly. Update documentation when code changes are "
                    "detected."
                ),
                "capabilities": ["technical_writing", "api_documentation", "tutorial_creation", "documentation_maintenance"],
                "built_in_tools": ["file", "research"],
                "tags": ["engineering", "documentation"],
            },
            {
                "name": "test_generator",
                "display_name": "Test Generator",
                "description": "Generates unit tests, integration tests, and test plans",
                "specialist_type": "executor",
                "system_prompt": (
                    "You are a test generation specialist for {specialization}. Analyze source "
                    "code to generate comprehensive test suites covering happy paths, edge cases, "
                    "error conditions, and boundary values. Write tests that follow the project's "
                    "existing test framework and conventions. Aim for high branch coverage while "
                    "keeping tests maintainable and readable. Generate both unit tests for "
                    "isolated functions and integration tests for component interactions. Include "
                    "clear test descriptions that document the expected behavior."
                ),
                "capabilities": ["test_generation", "test_planning", "coverage_analysis", "test_design"],
                "built_in_tools": ["file", "computation"],
                "tags": ["engineering", "testing"],
            },
            {
                "name": "architecture_advisor",
                "display_name": "Architecture Advisor",
                "description": "Advises on system architecture, design patterns, and technical decisions",
                "specialist_type": "domain_expert",
                "system_prompt": (
                    "You are a software architecture advisor for {specialization}. Evaluate "
                    "system designs, propose architectural patterns, and assess trade-offs for "
                    "technical decisions. Consider scalability, maintainability, reliability, "
                    "and cost when making recommendations. Draw on established patterns like "
                    "microservices, event-driven architecture, CQRS, and domain-driven design "
                    "where appropriate. Produce architecture decision records (ADRs) that document "
                    "context, options considered, and rationale for the chosen approach."
                ),
                "capabilities": ["architecture_review", "design_patterns", "trade_off_analysis", "decision_documentation"],
                "built_in_tools": ["file", "research"],
                "tags": ["engineering", "architecture"],
            },
        ],
        mcp_server_suggestions=[
            {"name": "github", "description": "Access GitHub repositories, PRs, and issues", "transport": "streamable_http"},
            {"name": "jira", "description": "Connect to Jira for issue tracking and sprint management", "transport": "streamable_http"},
            {"name": "sentry", "description": "Pull error reports and stack traces from Sentry", "transport": "streamable_http"},
            {"name": "docker", "description": "Manage containers and inspect runtime environments", "transport": "stdio"},
        ],
        workspace_config={
            "display_name": "Software Engineering",
            "description": "Workspace for software development with code review, debugging, documentation, and testing.",
            "icon": "\U0001f4bb",
            "color": "#f59e0b",
        },
        recommended_knowledge_bases=[
            "Project source code and architecture documentation",
            "Coding standards and style guides",
            "API specifications and design documents",
            "Past incident reports and post-mortems",
        ],
        tags=["engineering", "code_review", "testing", "documentation"],
    ),

    # ── 6. Marketing ─────────────────────────────────────────────────────
    UseCaseTemplate(
        name="marketing",
        display_name="Marketing",
        description=(
            "A marketing swarm that creates content, optimizes SEO, plans "
            "campaigns, and researches target audiences to drive growth "
            "and engagement."
        ),
        category="marketing",
        icon="\U0001f4e3",   # megaphone
        color="#ec4899",
        colonees=[
            {
                "name": "content_creator",
                "display_name": "Content Creator",
                "description": "Creates blog posts, social media copy, emails, and marketing collateral",
                "specialist_type": "executor",
                "system_prompt": (
                    "You are a marketing content creation specialist for {specialization}. "
                    "Write compelling blog posts, social media copy, email campaigns, and "
                    "marketing collateral that align with brand voice and messaging guidelines. "
                    "Tailor tone and format to the target platform and audience segment. Use "
                    "storytelling techniques, clear calls to action, and data-backed claims. "
                    "Produce multiple variations when requested for A/B testing. Ensure all "
                    "content is original, fact-checked, and optimized for the intended channel."
                ),
                "capabilities": ["content_writing", "copywriting", "brand_voice", "multi_channel_content"],
                "built_in_tools": ["file", "research", "media"],
                "tags": ["marketing", "content"],
            },
            {
                "name": "seo_analyst",
                "display_name": "SEO Analyst",
                "description": "Analyzes and optimizes content for search engine visibility",
                "specialist_type": "analyst",
                "system_prompt": (
                    "You are an SEO analysis specialist for {specialization}. Conduct keyword "
                    "research, analyze search intent, and evaluate content for on-page SEO factors "
                    "including title tags, meta descriptions, heading structure, and internal linking. "
                    "Audit existing content for optimization opportunities and recommend improvements. "
                    "Track ranking performance and provide actionable recommendations to improve "
                    "organic visibility. Stay current with search algorithm changes and adjust "
                    "strategies accordingly."
                ),
                "capabilities": ["keyword_research", "seo_audit", "content_optimization", "ranking_analysis"],
                "built_in_tools": ["research", "computation"],
                "tags": ["marketing", "seo"],
            },
            {
                "name": "campaign_strategist",
                "display_name": "Campaign Strategist",
                "description": "Plans and analyzes marketing campaigns across channels",
                "specialist_type": "domain_expert",
                "system_prompt": (
                    "You are a marketing campaign strategy specialist for {specialization}. "
                    "Design multi-channel marketing campaigns with clear objectives, target "
                    "audiences, messaging frameworks, channel mix, budget allocations, and "
                    "success metrics. Analyze past campaign performance to inform future strategy. "
                    "Create campaign briefs, content calendars, and measurement plans. Consider "
                    "customer journey stages when planning touchpoints and ensure messaging "
                    "consistency across all channels."
                ),
                "capabilities": ["campaign_planning", "channel_strategy", "budget_allocation", "performance_analysis"],
                "built_in_tools": ["computation", "file"],
                "tags": ["marketing", "campaigns"],
            },
            {
                "name": "audience_researcher",
                "display_name": "Audience Researcher",
                "description": "Researches target audiences, personas, and market segments",
                "specialist_type": "researcher",
                "system_prompt": (
                    "You are an audience research specialist for {specialization}. Analyze "
                    "demographic data, behavioral signals, and market segments to build detailed "
                    "buyer personas and audience profiles. Identify audience needs, pain points, "
                    "preferred channels, and content consumption habits. Use survey data, analytics, "
                    "and competitive intelligence to validate assumptions. Produce persona documents "
                    "and segmentation frameworks that marketing teams can use to target messaging "
                    "effectively."
                ),
                "capabilities": ["audience_analysis", "persona_development", "market_segmentation", "behavioral_analysis"],
                "built_in_tools": ["research", "computation"],
                "tags": ["marketing", "audience_research"],
            },
        ],
        mcp_server_suggestions=[
            {"name": "google_analytics", "description": "Access website analytics and user behavior data", "transport": "streamable_http"},
            {"name": "hubspot", "description": "Manage contacts, campaigns, and marketing automation", "transport": "streamable_http"},
            {"name": "semrush", "description": "Access SEO and competitive analysis data", "transport": "streamable_http"},
            {"name": "mailchimp", "description": "Manage email campaigns and subscriber data", "transport": "streamable_http"},
        ],
        workspace_config={
            "display_name": "Marketing",
            "description": "Workspace for marketing operations with content creation, SEO, campaign strategy, and audience research.",
            "icon": "\U0001f4e3",
            "color": "#ec4899",
        },
        recommended_knowledge_bases=[
            "Brand guidelines, voice and tone documentation",
            "Past campaign performance reports and learnings",
            "Target audience personas and segmentation data",
            "Competitor analysis and market positioning research",
        ],
        tags=["marketing", "content", "seo", "campaigns"],
    ),

    # ── 7. Education ─────────────────────────────────────────────────────
    UseCaseTemplate(
        name="education",
        display_name="Education",
        description=(
            "An education swarm with an adaptive tutor, curriculum designer, "
            "quiz generator, and progress tracker to create personalized "
            "learning experiences."
        ),
        category="education",
        icon="\U0001f393",   # graduation cap
        color="#14b8a6",
        colonees=[
            {
                "name": "tutor",
                "display_name": "Tutor",
                "description": "Provides adaptive, conversational tutoring across subjects",
                "specialist_type": "domain_expert",
                "system_prompt": (
                    "You are an adaptive tutoring specialist for {specialization}. Engage "
                    "learners in Socratic dialogue, adjusting explanations to their knowledge "
                    "level and learning style. Break complex concepts into manageable steps, use "
                    "analogies and real-world examples, and check for understanding before moving "
                    "on. When a learner is stuck, provide hints rather than direct answers to "
                    "build problem-solving skills. Track misconceptions and revisit them in "
                    "future interactions. Maintain an encouraging, patient tone throughout."
                ),
                "capabilities": ["adaptive_teaching", "concept_explanation", "misconception_detection", "socratic_dialogue"],
                "built_in_tools": ["research", "computation", "media"],
                "tags": ["education", "tutoring"],
            },
            {
                "name": "curriculum_designer",
                "display_name": "Curriculum Designer",
                "description": "Designs structured learning paths and course outlines",
                "specialist_type": "analyst",
                "system_prompt": (
                    "You are a curriculum design specialist for {specialization}. Create "
                    "structured learning paths with clear objectives, prerequisite mappings, "
                    "lesson sequences, and assessment milestones. Align curriculum to learning "
                    "standards or competency frameworks when applicable. Design each module with "
                    "estimated time, key concepts, activities, and resources. Ensure progressive "
                    "difficulty and logical sequencing. Incorporate varied instructional strategies "
                    "including direct instruction, project-based learning, and peer collaboration."
                ),
                "capabilities": ["curriculum_design", "learning_path_creation", "standards_alignment", "module_planning"],
                "built_in_tools": ["file", "research"],
                "tags": ["education", "curriculum"],
            },
            {
                "name": "quiz_generator",
                "display_name": "Quiz Generator",
                "description": "Generates quizzes, assessments, and practice exercises",
                "specialist_type": "executor",
                "system_prompt": (
                    "You are an assessment creation specialist for {specialization}. Generate "
                    "quizzes, tests, and practice exercises aligned with learning objectives. "
                    "Create diverse question types: multiple choice, short answer, fill-in-the-blank, "
                    "matching, and open-ended problems. Provide answer keys with detailed explanations "
                    "for each correct answer. Calibrate difficulty levels and tag each question with "
                    "the concept it assesses. Include distractors that target common misconceptions "
                    "to make assessments diagnostically useful."
                ),
                "capabilities": ["question_generation", "assessment_design", "difficulty_calibration", "answer_key_creation"],
                "built_in_tools": ["file", "computation"],
                "tags": ["education", "assessment"],
            },
            {
                "name": "progress_tracker",
                "display_name": "Progress Tracker",
                "description": "Tracks learner progress, identifies gaps, and recommends next steps",
                "specialist_type": "analyst",
                "system_prompt": (
                    "You are a learning progress tracking specialist for {specialization}. "
                    "Analyze assessment results, engagement patterns, and learning activities "
                    "to measure learner progress against objectives. Identify knowledge gaps, "
                    "struggling areas, and mastered topics. Generate progress reports with "
                    "visualizations showing growth over time. Recommend personalized next steps: "
                    "topics to review, practice exercises, or advanced material. Flag learners "
                    "who may need additional support or are ready for acceleration."
                ),
                "capabilities": ["progress_analysis", "gap_identification", "personalized_recommendations", "reporting"],
                "built_in_tools": ["computation", "file"],
                "tags": ["education", "progress_tracking"],
            },
        ],
        mcp_server_suggestions=[
            {"name": "google_classroom", "description": "Integrate with Google Classroom for assignments and grades", "transport": "streamable_http"},
            {"name": "canvas", "description": "Connect to Canvas LMS for course management", "transport": "streamable_http"},
            {"name": "notion", "description": "Organize course materials and notes in Notion", "transport": "streamable_http"},
        ],
        workspace_config={
            "display_name": "Education",
            "description": "Workspace for education with adaptive tutoring, curriculum design, assessments, and progress tracking.",
            "icon": "\U0001f393",
            "color": "#14b8a6",
        },
        recommended_knowledge_bases=[
            "Course materials, textbooks, and reference resources",
            "Learning standards and competency frameworks",
            "Assessment item banks and grading rubrics",
            "Learner profiles and historical performance data",
        ],
        tags=["education", "tutoring", "curriculum", "assessment"],
    ),

    # ── 8. Healthcare ────────────────────────────────────────────────────
    UseCaseTemplate(
        name="healthcare",
        display_name="Healthcare",
        description=(
            "A healthcare operations swarm that analyzes symptoms, aggregates "
            "medical research, reviews clinical data, and assists with patient "
            "communication -- all in a HIPAA-conscious, evidence-based manner."
        ),
        category="healthcare",
        icon="\U0001fa7a",   # stethoscope
        color="#ef4444",
        colonees=[
            {
                "name": "symptom_analyzer",
                "display_name": "Symptom Analyzer",
                "description": "Analyzes reported symptoms against clinical knowledge to suggest differentials",
                "specialist_type": "domain_expert",
                "system_prompt": (
                    "You are a clinical symptom analysis specialist for {specialization}. "
                    "Analyze reported symptoms, patient history, and relevant vitals to produce "
                    "a ranked list of differential diagnoses supported by clinical evidence. "
                    "Always include prevalence, key distinguishing features, and recommended "
                    "diagnostic workups for each differential. Flag any red-flag symptoms that "
                    "require urgent attention. Clearly state that your analysis is for informational "
                    "support only and does not replace clinical judgment or a licensed provider."
                ),
                "capabilities": ["symptom_analysis", "differential_diagnosis", "clinical_reasoning", "triage_assessment"],
                "built_in_tools": ["research", "computation"],
                "tags": ["healthcare", "clinical"],
            },
            {
                "name": "medical_research_aggregator",
                "display_name": "Research Aggregator",
                "description": "Aggregates and summarizes medical research literature",
                "specialist_type": "researcher",
                "system_prompt": (
                    "You are a medical research aggregation specialist for {specialization}. "
                    "Search and synthesize clinical studies, systematic reviews, and practice "
                    "guidelines relevant to the clinical question. Evaluate evidence quality "
                    "using frameworks such as GRADE or Oxford CEBM levels of evidence. Summarize "
                    "findings with effect sizes, confidence intervals, and number needed to treat "
                    "when available. Highlight conflicting evidence and note limitations. Provide "
                    "full citations in a format suitable for clinical documentation."
                ),
                "capabilities": ["literature_search", "evidence_grading", "clinical_synthesis", "citation_management"],
                "built_in_tools": ["research", "file"],
                "tags": ["healthcare", "research"],
            },
            {
                "name": "clinical_data_reviewer",
                "display_name": "Clinical Data Reviewer",
                "description": "Reviews clinical data, lab results, and patient records for patterns",
                "specialist_type": "analyst",
                "system_prompt": (
                    "You are a clinical data review specialist for {specialization}. Analyze "
                    "lab results, imaging reports, vital sign trends, and structured clinical "
                    "data to identify patterns, anomalies, and clinically significant changes. "
                    "Flag values outside normal ranges and correlate findings across data sources. "
                    "Present findings in a structured format suitable for clinical review: "
                    "abnormal findings first, then trends, then stable values. Maintain strict "
                    "attention to units, reference ranges, and temporal context."
                ),
                "capabilities": ["data_analysis", "trend_detection", "anomaly_detection", "clinical_reporting"],
                "built_in_tools": ["computation", "file"],
                "tags": ["healthcare", "data_review"],
            },
            {
                "name": "patient_communicator",
                "display_name": "Patient Communicator",
                "description": "Drafts clear, empathetic patient communications and education materials",
                "specialist_type": "executor",
                "system_prompt": (
                    "You are a patient communication specialist for {specialization}. Draft "
                    "clear, empathetic communications for patients including appointment summaries, "
                    "care instructions, medication guides, and educational materials. Use plain "
                    "language at a sixth-grade reading level, avoiding medical jargon unless "
                    "defined in context. Structure information with headers, bullet points, and "
                    "action items so patients can easily follow instructions. Include appropriate "
                    "disclaimers and encourage patients to contact their provider with questions."
                ),
                "capabilities": ["patient_education", "health_literacy", "communication_drafting", "material_creation"],
                "built_in_tools": ["file", "media"],
                "tags": ["healthcare", "communication"],
            },
        ],
        mcp_server_suggestions=[
            {"name": "epic_fhir", "description": "Access patient data via Epic FHIR APIs (requires authorization)", "transport": "streamable_http"},
            {"name": "pubmed", "description": "Search PubMed for medical literature and clinical studies", "transport": "streamable_http"},
            {"name": "drug_interactions", "description": "Check drug interactions and contraindications", "transport": "streamable_http"},
        ],
        workspace_config={
            "display_name": "Healthcare",
            "description": "Workspace for healthcare operations with symptom analysis, medical research, clinical data review, and patient communication.",
            "icon": "\U0001fa7a",
            "color": "#ef4444",
        },
        recommended_knowledge_bases=[
            "Clinical practice guidelines and standard protocols",
            "Drug formulary and interaction databases",
            "Patient education templates and consent forms",
            "Internal policies for HIPAA compliance and data handling",
        ],
        tags=["healthcare", "clinical", "research", "patient_communication"],
    ),
]
