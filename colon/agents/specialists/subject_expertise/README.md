# Subject Expertise Specialization

Provides deep domain knowledge and expert reasoning within the Colonees platform.

## Overview

The Subject Expertise specialist handles domain-specific knowledge tasks: concept explanation, problem analysis, solution validation, and expert guidance. It coordinates with tool providers for computational and visual support.

## Architecture

### Specialist Agent
`SubjectExpertSpecialistAgent` — orchestrates domain knowledge workflows using media and computation tools.

### Tool Providers

#### ComputationTools
Executes calculations and code for domain demonstrations and problem-solving.

**Capabilities:** `python_execution`, `calculations`, `code_interpreter`, `mathematical_computation`

#### MediaToolProvider
Generates and processes media for concept visualization and explanation.

**Capabilities:** `image_generation`, `video_processing`, `text_to_speech`, `diagram_creation`, `media_processing`

## Domain Expertise

- Domain knowledge provision
- Concept explanation
- Problem analysis
- Solution validation
- Expert guidance
