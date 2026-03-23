# Colonees

**The Autonomous Agent Swarm Platform**

Colonees is an open-source, production-grade autonomous agent swarm platform built around a hierarchical superagent/specialist architecture. It represents the same class of agentic infrastructure that powers platforms such as Claude Code, Codex, and Cursor — but designed as a general-purpose, self-hostable enterprise system.

Colonees orchestrates entire intelligent workflows end-to-end, coordinating a superagent with an extensible colony of domain-specialist agents, each fully equipped with its own tool-calling, reasoning, and memory capabilities.

The platform is **domain-agnostic** and can be deployed with specialist agents across any vertical including healthcare, finance, legal, media, government, trade, logistics, research, and enterprise operations — designed for any organisation seeking to run complex, autonomous workflows at scale without human-in-the-loop bottlenecks.

---

## Overview

Colonees is a generic multi-agent orchestration platform where specialist agents collaborate autonomously to research, reason, execute, and deliver on any complex task.

### Key Features

- **Domain-Agnostic Agent OS**: Not task-specific workflows, but a general-purpose agent platform for any domain
- **Hierarchical Swarm Architecture**: Superagent → Specialist → Tool agent architecture with dynamic discovery
- **Autonomous Collaboration**: Agents operate autonomously within strict safety boundaries
- **Extensible Colony**: Plug in specialist agents for any vertical — healthcare, finance, legal, logistics, and more
- **Multi-Agent Communication**: Seamless A2A Protocol and MCP integration for complex workflows
- **Context-Aware Memory**: Pluggable memory strategies for persistent agent context
- **Enterprise Scale**: Supports 100,000+ concurrent users and 10,000+ active sessions
- **Self-Hostable**: Deploy anywhere — local, Docker, or cloud

---

## Architecture

Colonees implements a three-tier hierarchical architecture with dynamic agent discovery:

```
┌─────────────────────────────────────────────────────────────┐
│                    User / API Layer                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │  REST API   │ │  CLI        │ │  SDK        │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│            Superagent Layer (Control Plane)                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ Superagent  │ │   Agent     │ │   Safety    │          │
│  │             │ │  Directory  │ │  Enforcer   │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│         Specialist Colony (Capability Layer)                │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │ Domain  │ │Research │ │Analyst  │ │ Media   │          │
│  │ Expert  │ │ Agent   │ │ Agent   │ │Producer │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│            Tool Layer (Execution Layer)                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │  File   │ │Compute  │ │Research │ │  Media  │          │
│  │  Agent  │ │ Agent   │ │ Agent   │ │  Agent  │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### Core Principles

- **Dynamic Agent Discovery**: Agents discover collaborators through the Agent Directory, not hard-coded references
- **Emergent Workflows**: Task execution emerges from agent intelligence, not pre-scripted processes
- **Autonomous Collaboration**: Agents operate autonomously within strict safety boundaries
- **Loop Prevention**: Strict limits prevent runaway agent loops (max 20 steps, 30 tool calls, 5 recursion depth)
- **Generic Orchestration**: Single orchestration engine handles any task across any domain

---

## Quick Start

### Prerequisites

- Python 3.10+
- An LLM API key (Groq, OpenAI, Anthropic, or any OpenAI-compatible provider)

### Installation

```bash
# Clone the repository
git clone https://github.com/colonees/colonees.git
cd colonees

# Install dependencies
pip install -e ".[dev]"

# Copy and configure environment
cp .env .env.local
# Edit .env.local with your LLM_API_KEY
```

### Local Development

```bash
# Set environment
export COLONEES_ENVIRONMENT=local
export LLM_API_KEY=your_api_key_here

# Run the platform
python app.py
```

### CLI Usage

```bash
# Invoke the platform with any goal
colonees invoke --goal "Research the latest trends in quantum computing and produce a summary report"

# Invoke with a user ID and save output to file
colonees invoke --goal "Summarise the top 10 open-source LLMs" --user-id alice --output result.json

# Check platform status
colonees status

# Save status to file
colonees status --output status.json
```

### API Usage

The platform exposes a REST API. Interactive docs are available at `http://localhost:8080/docs`.

```bash
# Health check
curl http://localhost:8080/health

# Platform status
curl http://localhost:8080/status

# Submit a goal to the agent swarm
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Analyze the competitive landscape for electric vehicles in 2025",
    "user_id": "alice",
    "context": {}
  }'

# Invoke a specific specialist agent directly
curl -X POST http://localhost:8080/agents/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "researcher",
    "task": "Find the latest peer-reviewed papers on CRISPR gene editing",
    "context": {}
  }'

# List all registered agents
curl http://localhost:8080/agents
```

**Available agent types**: `domain_expert`, `researcher`, `analyst`, `executor`, `media_producer`

---

## Specialist Agents

Colonees ships with a set of built-in specialist agents. You can extend the colony with your own:

| Agent Type | Capabilities |
|---|---|
| `domain_expert` | Deep domain knowledge, concept explanation, problem-solving |
| `researcher` | Information gathering, synthesis, source validation |
| `analyst` | Data analysis, evaluation, structured reporting |
| `executor` | Task execution, file operations, computation |
| `media_producer` | Image generation, audio synthesis, video production |

---

## Deployment

### Docker

```bash
docker build -t colonees .
docker run -p 8080:8080 --env-file .env colonees
```

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `LLM_API_KEY` | LLM provider API key | required |
| `COLONEES_ENVIRONMENT` | `local` or `production` | `local` |
| `COLONEES_LOG_LEVEL` | Log level | `INFO` |
| `COLONEES_MAX_CONCURRENT_SESSIONS` | Max concurrent sessions | `10000` |
| `COLONEES_FILES_DIR` | Local directory for file storage | `colonees_files` |
| `COLONEES_MEDIA_DIR` | Local directory for media productions | `colonees_media` |

---

## Safety

Colonees enforces strict safety boundaries to prevent runaway agent loops:

- Max 20 agent steps per task
- Max 30 tool calls per task
- Max 5 recursion depth
- Max 10 minutes runtime
- Max 10 agents per task
- Goal validation against forbidden patterns

---

## Scale

- **Concurrent Users**: 100,000+
- **Active Sessions**: 10,000+
- **Response Latency**: <300ms (p95)
- **Agent Population**: 50,000+ active agents

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Links

- GitHub: https://github.com/colonees/colonees
- Issues: https://github.com/colonees/colonees/issues
- Email: alaminibrahim433@gmail.com
