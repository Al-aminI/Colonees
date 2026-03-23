# Research Specialization

Provides research and information synthesis capabilities within the GALOS platform.

## Overview

The Research specialization focuses on research strategy, information analysis, and source validation. It designs research methodologies and coordinates with tool agents for information retrieval and data gathering.

## Architecture

```
galos/agents/research/
├── __init__.py              # Public API exports
├── README.md                # This file
├── specialist.py            # ResearchSpecialistAgent
└── tools/                   # Tool agents
    ├── __init__.py
    └── research_agent.py    # Information retrieval operations
```

## Components

### ResearchSpecialistAgent

The main specialist agent that provides research expertise.

**Capabilities:**
- `research_strategy_design` - Design research methodologies
- `information_synthesis` - Synthesize information from multiple sources
- `source_validation` - Validate source credibility
- `research_methodology` - Create research frameworks
- `data_analysis` - Analyze research data

**Domain Expertise:**
- Subject matter (configurable)
- Research methods
- Information science
- Data analysis

### Tool Agents

#### ResearchToolAgent
Executes information retrieval operations including web searches, API calls, and content fetching.

**Capabilities:** `web_search`, `information_retrieval`, `api_access`, `content_fetching`

## Usage

```python
from galos.agents.research import ResearchSpecialistAgent

# Create research specialist
researcher = ResearchSpecialistAgent(
    session_manager=session_manager,
    agent_id="research_001",
    specialization="computer_science"
)

# Design research strategy
strategy = await researcher.design_research_strategy(
    topic="machine learning optimization",
    scope="recent_advances",
    sources=["academic_papers", "technical_blogs"]
)
```

## Design Principles

1. **Separation of Concerns**: Specialist handles research strategy, tool agents handle retrieval
2. **Delegation Pattern**: Specialist delegates all information retrieval operations
3. **No Direct Tool Access**: Specialist has no tools, only research methodology expertise
4. **Agent-to-Agent Protocol**: Communication via A2A protocol for coordination

## Integration

The research specialization integrates with:
- **Agent Directory**: Registration and discovery
- **Workflow Orchestrator**: Task coordination
- **Session Manager**: State management
- **Other Specialists**: Subject experts, tutors, assessment agents

## Configuration

Research agents are configured through the SpecialistAgentFactory:

```python
from galos.agents.agent_directory import SpecialistAgentFactory

researcher = SpecialistAgentFactory.create_specialist_agent(
    specialist_type="research",
    session_manager=session_manager,
    agent_id="research_001",
    specialization="biology"
)
```
