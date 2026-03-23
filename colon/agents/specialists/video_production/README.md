# Video Production Specialization

Orchestrates the complete video production workflow within the Colonees platform — from concept to final rendered MP4.

## Architecture

### Specialist Agent
`VideoProductionSpecialistAgent` — drives the full pipeline using the `MediaToolProvider`.

### Tool Provider

#### MediaToolProvider
Handles all media operations: script generation, image generation, TTS, resizing, and video assembly.

**Capabilities:** `script_generation`, `image_generation`, `text_to_speech`, `image_processing`, `video_assembly`, `local_storage`

## Workflow

1. `create_production` — initialise local storage
2. `write_script` — generate scene-by-scene JSON script
3. `sanitize_image_prompt` → `generate_image` — generate scene visuals (parallel)
4. `resize_image` — crop/resize to 1280x720 (parallel)
5. `text_to_speech` — synthesise narration audio (parallel)
6. `list_artifacts` — verify asset counts before assembly
7. `assemble_video` — concatenate scenes into final MP4

## Domain Expertise

- Video creation and planning
- Creative direction
- Production orchestration
- Asset coordination
