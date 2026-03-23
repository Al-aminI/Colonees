# Colonees

**The Autonomous Agent Swarm Platform**

Colonees is an open-source, production-grade autonomous agent swarm platform. It orchestrates a superagent with an extensible colony of specialist agents — each with its own tools, memory, constraints, and evaluation criteria — to execute complex, multi-step workflows end-to-end without human-in-the-loop bottlenecks.

The platform is **domain-agnostic** and **embeddable** — deployed with specialist agents across any vertical including healthcare, finance, legal, education, media, government, trade, logistics, research, and enterprise operations. Designed for any organisation seeking to run complex, autonomous workflows at scale without human-in-the-loop bottlenecks. Drop it into any product as a plug-and-play intelligence layer. Specialists can be created, configured, and managed entirely through the API, making dynamic agent creation a first-class feature.

---

## Architecture

Three-tier hierarchical swarm with dynamic agent discovery:

```
┌──────────────────────────────────────────────────────────┐
│                    User / API Layer                      │
│         REST API  ·  CLI  ·  SDK                        │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│           Superagent (Control Plane)                     │
│   Autonomous orchestration · Agent Directory             │
│   Safety Enforcer · Session Manager                      │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│         Specialist Colony (Capability Layer)             │
│   Domain Expert · Researcher · Analyst                   │
│   Executor · Media Producer · [User-Defined Colonees]    │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│              Tool Layer (Execution Layer)                │
│   File Provider · Compute Tools · Research Tools        │
│   Media Provider · [MCP Servers]                         │
└──────────────────────────────────────────────────────────┘
```

**Core principles:**
- Superagent orchestrates — it never executes tools directly
- Specialists reason and coordinate — they never orchestrate
- Tool agents execute — they never reason
- Emergent workflows from agent intelligence, not pre-scripted processes
- Loop prevention: max 20 steps, 30 tool calls, 5 recursion depth, 10 min runtime

---

## Quick Start

### Prerequisites

- Python 3.10+
- An LLM API key (Groq, OpenAI, Anthropic, or any OpenAI-compatible provider)
- `GEMINI_API_KEY` for image generation and TTS (media features)

### Installation

```bash
git clone https://github.com/colonees/colonees.git
cd colonees
pip install -e ".[dev]"
cp .env .env.local
# Edit .env.local — set LLM_API_KEY at minimum
```

### Run

```bash
export LLM_API_KEY=your_key_here
python app.py
# API available at http://localhost:8080
# Interactive docs at http://localhost:8080/docs
```

### Docker

```bash
docker build -t colonees .
docker run -p 8080:8080 --env-file .env colonees
```

---

## API Reference

### System

```bash
# Liveness probe
curl http://localhost:8080/health

# Platform status
curl http://localhost:8080/status
```

### Agent Swarm

```bash
# All enabled colonees are available by default
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Analyse the competitive landscape for EVs in 2025 and produce a report",
    "context": {}
  }'

# Resume an existing session
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Continue the analysis with a focus on European markets",
    "session_id": "session_20250323120000_abc12345"
  }'

# Restrict which colonees the superagent may use for this request
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Research and summarise the latest CRISPR breakthroughs",
    "colonees": ["researcher", "analyst"]
  }'

# Invoke a specific specialist directly
curl -X POST http://localhost:8080/agents/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "researcher",
    "task": "Find the latest peer-reviewed papers on CRISPR gene editing",
    "context": {}
  }'

# List registered agents
curl http://localhost:8080/agents
```

**Built-in specialist types:** `domain_expert`, `researcher`, `analyst`, `executor`, `media_producer`

---

### Colonees — Dynamic Specialist Creation

Colonees (specialist definitions) are the platform's key differentiator. Create fully-described specialists via the API — no Python code required.

**Colonee lifecycle:**
- All colonees (built-in and user-defined) have an `enabled` flag
- Disabled colonees cannot be spawned — they are invisible to the superagent
- Use enable/disable to control which specialists are active in your swarm at any time
- Per-request, you can further restrict which colonees the superagent may use via the `colonees` allowlist in `/invoke`

```bash
# Create a custom specialist
curl -X POST http://localhost:8080/colonees \
  -H "Content-Type: application/json" \
  -d '{
    "name": "legal_researcher",
    "display_name": "Legal Researcher",
    "description": "Researches case law, statutes, and legal precedents.",
    "specialist_type": "researcher",
    "system_prompt": "You are a Legal Research Specialist for {specialization}. Use your tools to find relevant case law, statutes, and legal commentary. Always cite sources with URLs.",
    "capabilities": ["legal_research", "case_law_analysis", "statute_interpretation"],
    "built_in_tools": ["research", "file"],
    "mcp_servers": [],
    "constraints": {
      "max_tool_calls": 20,
      "forbidden_topics": ["medical advice", "financial advice"],
      "output_format": "markdown"
    },
    "evaluation": {
      "require_sources": true,
      "quality_threshold": 0.8
    },
    "tags": ["legal", "research"]
  }'

# List all colonees (built-in + user-defined)
curl http://localhost:8080/colonees

# Filter by tag
curl "http://localhost:8080/colonees?tag=legal"

# Filter enabled only
curl "http://localhost:8080/colonees?enabled_only=true"

# Get a specific colonee
curl http://localhost:8080/colonees/legal_researcher

# Update a colonee
curl -X PUT http://localhost:8080/colonees/legal_researcher \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description",
    "constraints": { "max_tool_calls": 30 }
  }'

# Enable / disable (works on built-ins too)
curl -X POST http://localhost:8080/colonees/legal_researcher/enable
curl -X POST http://localhost:8080/colonees/legal_researcher/disable

# Disable a built-in colonee (e.g. remove media_producer from the swarm)
curl -X POST http://localhost:8080/colonees/media_producer/disable

# Delete (user-defined only — built-ins are protected from deletion)
curl -X DELETE http://localhost:8080/colonees/legal_researcher
```

**Per-request colonee selection**

You can restrict which colonees the superagent may spawn for a specific request using the `colonees` field in `/invoke`. This is useful when you want to scope a task to a subset of your swarm — for example, only allowing research and analysis colonees for a data task, or presenting a curated set of specialists to an end user before they submit a request.

```bash
# Only allow researcher and analyst for this request
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Analyse the competitive landscape for EVs in 2025 and produce a report",
    "colonees": ["researcher", "analyst"]
  }'

# Omit colonees entirely — all enabled colonees are available (default)
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Produce a 2-minute explainer video on quantum computing"
  }'
```

Rules:
- Only enabled colonees can appear in the allowlist — disabled ones are silently filtered out
- If `colonees` is omitted, all enabled colonees are available
- If `colonees` is an empty list, the superagent has no specialists to spawn and will fail gracefully
- Built-in colonees behave identically to user-defined ones — they can be disabled and excluded from requests

**Colonee fields:**

| Field | Description |
|---|---|
| `name` | Unique slug — used to spawn the agent |
| `specialist_type` | Base type: `researcher`, `domain_expert`, `analyst`, `executor`, `media_producer` |
| `system_prompt` | Full system prompt. Use `{specialization}` as a placeholder |
| `built_in_tools` | Tool sets to enable: `file`, `computation`, `research`, `media` |
| `mcp_servers` | Named MCP servers to attach (registered via `/mcp/servers`) |
| `capabilities` | Capability strings — used by the superagent for discovery |
| `constraints` | `max_tool_calls`, `max_runtime_seconds`, `forbidden_topics`, `output_format` |
| `memory` | `enabled`, `strategy` (`basic`/`semantic`/`episodic`), `max_size_mb` |
| `evaluation` | `quality_threshold`, `require_sources`, `require_structured_output`, `custom_criteria` |
| `tags` | Free-form tags for filtering |
| `enabled` | Whether this colonee can be spawned (default `true`) |

**Built-in colonees** (ship with the platform, cannot be deleted, but can be disabled):

| Name | Type | Tools |
|---|---|---|
| `researcher` | researcher | research, computation |
| `domain_expert` | domain_expert | media, computation, research |
| `analyst` | analyst | file, media, computation |
| `executor` | executor | file, media, computation |
| `media_producer` | media_producer | media |

---

### MCP Servers — External Tool Integration

Register external MCP servers to inject tools into specialists at spawn time.

```bash
# HTTP server with API key auth (X-API-Key header)
curl -X POST http://localhost:8080/mcp/servers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pubmed",
    "transport": "streamable_http",
    "url": "https://pubmed-mcp.example.com/mcp/",
    "headers": { "X-API-Key": "your-api-key-here" },
    "specialist_types": ["researcher"]
  }'

# SSE server with bearer token auth
curl -X POST http://localhost:8080/mcp/servers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "legal_db",
    "transport": "sse",
    "url": "https://legal-mcp.example.com/sse/",
    "headers": { "Authorization": "Bearer eyJ..." },
    "specialist_types": ["analyst", "researcher"]
  }'

# stdio server — secrets passed as env vars to the server process
curl -X POST http://localhost:8080/mcp/servers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "postgres",
    "transport": "stdio",
    "command": "python",
    "args": ["db_server.py"],
    "env": { "DB_PASSWORD": "secret", "DB_HOST": "localhost" },
    "specialist_types": ["analyst", "researcher"]
  }'

# Register a server available to ALL specialists (omit specialist_types)
curl -X POST http://localhost:8080/mcp/servers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "logging",
    "transport": "streamable_http",
    "url": "http://localhost:8003/mcp/"
  }'

# List registered MCP servers (header values are masked in the response)
curl http://localhost:8080/mcp/servers

# Remove a server
curl -X DELETE http://localhost:8080/mcp/servers/pubmed
```

**Auth patterns by transport:**

| Transport | Auth mechanism | Field |
|---|---|---|
| `streamable_http` | API key, bearer token, custom headers | `headers` |
| `sse` | API key, bearer token, custom headers | `headers` |
| `stdio` | Env vars passed to the server process | `env` |

The `headers` field accepts any key-value pairs — pass whatever the MCP server expects:
- `{"X-API-Key": "sk-..."}` — API key header
- `{"Authorization": "Bearer eyJ..."}` — bearer token
- `{"X-API-Key": "key", "X-Tenant-ID": "org-123"}` — multiple headers

Header values are masked (`***`) in `GET /mcp/servers` responses so secrets are never leaked through the API.

**MCP tool scoping:**
- `specialist_types: ["researcher"]` — only the researcher gets these tools
- `specialist_types: ["analyst", "researcher"]` — both get them
- `specialist_types: []` (or omitted) — all specialists get them
- A colonee's `mcp_servers` list takes priority over global scoping — if a colonee names specific servers, only those are used

**Supported transports:** `streamable_http`, `sse`, `stdio`

---

### CLI

```bash
# Submit a goal
colonees invoke --goal "Research the latest trends in quantum computing"

# With user ID and output file
colonees invoke --goal "Summarise the top 10 open-source LLMs" --user-id alice --output result.json

# Platform status
colonees status

# Save status
colonees status --output status.json
```

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `LLM_API_KEY` | LLM provider API key | required |
| `GEMINI_API_KEY` | Google Gemini API key (image gen + TTS) | required for media |
| `COLONEES_ENVIRONMENT` | `local` or `production` | `local` |
| `COLONEES_LOG_LEVEL` | Log level | `INFO` |
| `COLONEES_FILES_DIR` | Local directory for file storage | `colonees_files` |
| `COLONEES_MEDIA_DIR` | Local directory for media productions | `colonees_media` |
| `COLONEES_REGISTRY_PATH` | Path for colonee registry JSON | `colonees_files/colonee_registry.json` |
| `COLONEES_MAX_USERS` | Max concurrent users | `100000` |
| `COLONEES_MAX_SESSIONS` | Max active sessions | `10000` |
| `PORT` | HTTP server port | `8080` |

---

## Embedding Colonees

Colonees is designed to be embedded into any product as a plug-and-play intelligence layer.

```python
from colon.core.platform import ColoneesPlatform
from colon.core.config import CologeesConfig

config = CologeesConfig.from_environment()
platform = ColoneesPlatform(config)
await platform.initialize()

# Register MCP servers at startup
platform.agent_manager.mcp.add_server(
    "my_db", "stdio",
    command="python", args=["db_server.py"],
    specialist_types=["analyst"]
)

# Submit a goal
result = await platform.handle_request(
    user_goal="Analyse Q3 sales data and produce a summary",
    context={"user_id": "alice"}
)
```

---

## Safety

- Max 20 agent steps per task
- Max 30 tool calls per task
- Max 5 recursion depth
- Max 10 minutes runtime per task
- Max 10 agents per task
- Goal validation against forbidden patterns
- Per-colonee `forbidden_topics` enforced via system prompt

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Links

- GitHub: https://github.com/colonees/colonees
- Issues: https://github.com/colonees/colonees/issues
- Email: alaminibrahim433@gmail.com
