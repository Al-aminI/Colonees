# Subject Expertise Specialization

Provides domain expertise and knowledge capabilities within the GALOS platform.

## Overview

The Subject Expertise specialization focuses on deep domain knowledge, concept explanation, and problem analysis. It provides expert-level understanding of specific subject areas and coordinates with tool agents for computational and visual support.

## Architecture

```
galos/agents/subject_expertise/
├── __init__.py              # Public API exports
├── README.md                # This file
├── specialist.py            # SubjectExpertSpecialistAgent
└── tools/                   # Tool agents
    ├── __init__.py
    ├── computation_agent.py # Calculations and code execution
    └── media_agent.py       # Media generation and processing
```

## Components

### SubjectExpertSpecialistAgent

The main specialist agent that provides domain expertise.

**Capabilities:**
- `domain_knowledge_provision` - Provide accurate domain knowledge
- `concept_explanation` - Explain complex concepts clearly
- `problem_analysis` - Analyze domain-specific problems
- `solution_validation` - Validate solutions and approaches
- `expert_guidance` - Guide problem-solving strategies

**Domain Expertise:**
- Subject matter (configurable)
- Subject theory
- Subject applications

**Key Methods:**
- `explain_concept(concept, complexity_level, context)` - Provide expert explanations

### Tool Agents

#### ComputationToolAgent
Executes calculations and code for domain demonstrations and problem-solving.

**Capabilities:** `python_execution`, `calculations`, `code_interpreter`, `mathematical_computation`

#### MediaToolAgent
Generates and processes media for concept visualization and explanation.

**Capabilities:** `image_generation`, `video_processing`, `text_to_speech`, `diagram_creation`, `media_processing`

## Usage

```python
from galos.agents.subject_expertise import SubjectExpertSpecialistAgent

# Create subject expert
expert = SubjectExpertSpecialistAgent(
    session_manager=session_manager,
    agent_id="expert_physics_001",
    specialization="physics"
)

# Explain a concept
explanation = await expert.explain_concept(
    concept="quantum entanglement",
    complexity_level="undergraduate",
    context={
        "prerequisites": ["quantum_mechanics_basics"],
        "learning_goal": "understand_applications"
    }
)
```

## Design Principles

1. **Separation of Concerns**: Specialist handles domain reasoning, tool agents handle execution
2. **Delegation Pattern**: Specialist delegates all computational and media operations
3. **No Direct Tool Access**: Specialist has no tools, only domain expertise
4. **Agent-to-Agent Protocol**: Communication via A2A protocol for coordination

## Integration

The subject expertise specialization integrates with:
- **Agent Directory**: Registration and discovery
- **Workflow Orchestrator**: Task coordination
- **Session Manager**: State management
- **Other Specialists**: Tutors, research agents, assessment agents

## Configuration

Subject expert agents are configured through the SpecialistAgentFactory:

```python
from galos.agents.agent_directory import SpecialistAgentFactory

expert = SpecialistAgentFactory.create_specialist_agent(
    specialist_type="subject_expert",
    session_manager=session_manager,
    agent_id="expert_001",
    specialization="chemistry"
)
```
