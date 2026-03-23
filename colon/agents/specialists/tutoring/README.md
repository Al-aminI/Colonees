# Domain Expert Specialization

Provides domain reasoning, content design, and end-to-end deliverable creation within the Colonees platform.

## Overview

The Domain Expert specialist handles complex knowledge tasks across any vertical. It analyzes requests, designs structured approaches, and coordinates with tool agents to produce complete deliverables including documents, media, and data outputs.

## Architecture

### Specialist Agent
`TutorSpecialistAgent` — orchestrates domain workflows using file, media, and computation tools.

### Tool Providers

#### FileToolProvider
Handles file I/O for reading source materials and writing output documents.

**Capabilities:** `file_read`, `file_write`, `file_operations`

#### ComputationTools
Executes calculations and code for data processing and analysis.

**Capabilities:** `python_execution`, `calculations`, `mathematical_computation`

#### MediaToolProvider
Generates and processes media assets: images, videos, audio narration.

**Capabilities:** `image_generation`, `video_assembly`, `text_to_speech`, `media_processing`
