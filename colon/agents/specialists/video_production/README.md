# Video Production Specialization

A modular, state-of-the-art video production system for GALOS that orchestrates the complete workflow from concept to final rendering.

## Architecture

This module follows best practices for modular agent design:

```
video_production/
├── __init__.py              # Public API exports
├── models.py                # Data models and validation
├── specialist.py            # VideoProductionSpecialistAgent (orchestrator)
├── tools/                   # Tool agents (execution only)
│   ├── __init__.py
│   ├── script_agent.py      # Script generation
│   ├── audio_agent.py       # Audio synthesis (TTS + music)
│   ├── visual_agent.py      # Visual asset generation
│   └── assembly_agent.py    # Video assembly (FFmpeg)
└── README.md                # This file
```

## Components

### Data Models (`models.py`)

Core data structures with validation:

- **VideoStructure**: Complete video plan with scenes and metadata
- **Scene**: Individual scene with description, narration, timing
- **AudioCue**: Audio timing and content within scenes
- **VideoStyle**: Style configuration (colors, fonts, pacing)
- **VideoAsset**: Generated assets (images, audio, video)
- **ProductionState**: Production progress tracking
- **Enums**: AssetType, AssetStatus, ProductionStage

### Specialist Agent (`specialist.py`)

**VideoProductionSpecialistAgent** - Orchestrates the complete video production workflow:

- **Responsibilities**: Planning, coordination, creative decisions, quality validation
- **Does NOT**: Execute tools directly (delegates to tool agents)
- **Key Methods**:
  - `create_video()`: Main production pipeline
  - `plan_video_structure()`: Scene planning algorithm
  - `generate_assets_parallel()`: Parallel asset generation with concurrency control
  - `_get_or_create_tool_agent()`: Tool agent caching

### Tool Agents (`tools/`)

Each tool agent handles specific technical operations:

#### ScriptToolAgent (`script_agent.py`)
- Generates video scripts with scene breakdowns
- Validates timing and scene completeness
- Supports script refinement based on feedback

#### AudioToolAgent (`audio_agent.py`)
- Text-to-speech narration generation
- Background music generation
- Audio mixing and synchronization

#### VisualToolAgent (`visual_agent.py`)
- Scene image generation
- Animation creation (zoom, pan, fade, ken_burns)
- Transition effects (fade, dissolve, wipe, slide)
- Text overlay rendering

#### VideoAssemblyToolAgent (`assembly_agent.py`)
- Video assembly from components
- FFmpeg-based rendering
- Effects and post-processing
- Multi-format export (mp4, mov, webm)

## Usage

### Import from Module

```python
from galos.agents.video_production import (
    # Models
    VideoStructure,
    Scene,
    VideoStyle,
    VideoAsset,
    ProductionState,
    
    # Specialist
    VideoProductionSpecialistAgent,
    
    # Tool Agents
    ScriptToolAgent,
    AudioToolAgent,
    VisualToolAgent,
    VideoAssemblyToolAgent,
)
```

### Create Video Production Specialist

```python
from galos.agents.video_production import VideoProductionSpecialistAgent, VideoStyle

# Initialize specialist
specialist = VideoProductionSpecialistAgent(
    session_manager=session_manager,
    agent_id="video_prod_001",
    specialization="corporate_training",
    agent_manager=agent_manager,
    agent_directory=agent_directory
)

# Define video style
style = VideoStyle(
    style_name='professional_modern',
    visual_style='minimalist',
    color_palette=['#2C3E50', '#3498DB', '#ECF0F1'],
    font_family='Roboto',
    animation_intensity=0.6,
    transition_style='smooth',
    music_genre='ambient',
    narration_voice='professional_female',
    pacing='moderate'
)

# Create video
result = await specialist.create_video(
    topic='Introduction to Supply Chain Management',
    style=style,
    duration=120,  # 2 minutes
    target_audience='professionals',
    requirements={}
)
```

### Direct Tool Agent Usage

```python
from galos.agents.video_production.tools import ScriptToolAgent

# Create script agent
script_agent = ScriptToolAgent(session_manager, "script_001")

# Generate script
script = await script_agent.generate_script(
    topic="Python Programming Basics",
    duration=60,
    style="professional",
    scene_count=6,
    target_audience="developers"
)
```

## Production Pipeline

The VideoProductionSpecialistAgent orchestrates a 6-stage pipeline:

1. **Planning (15%)**: Calculate scene count, durations, structure
2. **Script Generation (30%)**: Generate scene descriptions and narration
3. **Audio Generation (55%)**: Create narration and background music in parallel
4. **Visual Generation (80%)**: Generate scene images in parallel
5. **Assembly (95%)**: Combine all assets into final video
6. **Validation (100%)**: Quality checks and completion

## Key Features

- **Parallel Processing**: Concurrent asset generation with semaphore control (max 5)
- **Error Handling**: Retry logic with exponential backoff (max 3 retries)
- **Progress Tracking**: Real-time production state updates (0-100%)
- **Tool Agent Caching**: Reuse agents within session for performance
- **Validation**: Scene sequence, duration consistency, asset completeness
- **Mock Integration**: Ready for production API integration (TTS, image gen, FFmpeg)

## Integration

### Agent Manager

The module integrates with GALOS Agent Manager through factories:

```python
# Tool agents registered in ToolAgentFactory
tool_types = ['script', 'audio', 'visual', 'video_assembly']

# Specialist registered in SpecialistAgentFactory
specialist_types = ['video_production']
```

### Agent Directory

VideoProductionSpecialistAgent registers with Agent Directory:

- **Capabilities**: video_creation, video_planning, video_production_orchestration
- **Status Updates**: Heartbeat, load tracking, availability
- **Discovery**: Capability-based agent selection

### Supervisor

Supervisor recognizes video production requests through keyword detection:

```python
# Keywords: 'video', 'create video', 'generate video', 'video about'
# Returns capabilities: ['video_creation', 'script_generation', 'audio_generation', ...]
```

## Testing

Tests are organized by component:

- `tests/test_video_models.py` - Data model validation
- `tests/test_script_tool_agent.py` - Script generation
- `tests/test_audio_tool_agent.py` - Audio synthesis
- `tests/test_visual_tool_agent.py` - Visual generation
- `tests/test_video_assembly_tool_agent.py` - Video assembly
- `tests/test_video_production_specialist_agent.py` - Orchestration
- `tests/test_video_production_properties.py` - Property-based tests

## External Services

The module is designed for integration with:

- **TTS**: Google Gemini TTS
- **Image Generation**: DALL-E 3, Stable Diffusion, Midjourney
- **Music Generation**: Soundraw, AIVA, Mubert
- **Video Rendering**: FFmpeg

Currently uses mock implementations for development.

## Performance

- **Target Latency**: <2 minutes for 2-minute video
- **Concurrency**: Max 5 parallel asset generations
- **Retry Strategy**: Exponential backoff (1s, 2s, 4s)
- **Agent Spawn**: <200ms with caching
- **Throughput**: 30 videos/hour at peak load

## Best Practices

1. **Separation of Concerns**: Specialist reasons, tools execute
2. **Direct Invocation**: No message passing overhead
3. **Caching**: Reuse tool agents within session
4. **Parallel Execution**: Maximize throughput with asyncio
5. **Error Recovery**: Graceful degradation with retries
6. **Progress Tracking**: Real-time state updates
7. **Validation**: Multiple validation layers (input, timing, output)

## Future Enhancements

- Real API integrations (TTS, image generation, music)
- Advanced caching strategies (Redis, content-based)
- Progressive rendering (stream partial results)
- Quality assessment (automated video quality checks)
- Style templates (pre-configured visual styles)
- Multi-language support (narration in multiple languages)
