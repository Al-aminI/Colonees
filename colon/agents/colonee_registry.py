"""
Colonee Registry
Stores and manages Colonee definitions — the blueprints for specialist agents.

A Colonee is a fully-described specialist: role, system prompt, tools,
memory config, constraints, evaluation criteria, and enabled state.

Built-in colonees ship as defaults. User-defined colonees are created via
the API and stored here. Both are instantiated the same way — no special
Python classes needed for user-defined specialists.
"""

import json
import logging
import os
from copy import deepcopy
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class MemoryConfig:
    enabled: bool = False
    strategy: str = "basic"          # basic | semantic | episodic
    max_size_mb: int = 512

@dataclass
class ConstraintsConfig:
    max_tool_calls: int = 30
    max_runtime_seconds: int = 600   # 10 min
    forbidden_topics: List[str] = field(default_factory=list)
    output_format: Optional[str] = None   # e.g. "json", "markdown", None = free

@dataclass
class EvaluationConfig:
    quality_threshold: float = 0.7   # 0–1, used by future eval layer
    require_sources: bool = False
    require_structured_output: bool = False
    custom_criteria: List[str] = field(default_factory=list)

@dataclass
class ColoneeDefinition:
    # Identity
    name: str                        # unique slug, e.g. "researcher"
    display_name: str
    description: str
    specialist_type: str             # maps to _specialist_type on the agent class

    # Behaviour
    system_prompt: str               # supports {specialization} placeholder
    capabilities: List[str]          # capability strings registered in AgentDirectory
    built_in_tools: List[str]        # subset of: file, computation, research, media
    mcp_servers: List[str]           # server names from MCPManager

    # Config
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    constraints: ConstraintsConfig = field(default_factory=ConstraintsConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)

    # Metadata
    enabled: bool = True
    builtin: bool = False            # True = ships with platform, cannot be deleted
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    created_by: str = "system"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ColoneeDefinition":
        d = deepcopy(d)
        d["memory"] = MemoryConfig(**d.get("memory", {}))
        d["constraints"] = ConstraintsConfig(**d.get("constraints", {}))
        d["evaluation"] = EvaluationConfig(**d.get("evaluation", {}))
        return cls(**d)


# ---------------------------------------------------------------------------
# Built-in definitions
# ---------------------------------------------------------------------------

_BUILTIN_COLONEES: List[Dict[str, Any]] = [
    {
        "name": "researcher",
        "display_name": "Researcher",
        "description": "Gathers, validates, and synthesises information from any source.",
        "specialist_type": "researcher",
        "system_prompt": (
            "You are a Research Specialist for {specialization}. "
            "Gather information using your tools, cross-reference sources, "
            "and synthesise findings into well-supported, cited research output. "
            "Always produce actual findings with source URLs — never just descriptions."
        ),
        "capabilities": [
            "research_strategy_design", "information_synthesis",
            "source_validation", "research_methodology", "data_analysis",
        ],
        "built_in_tools": ["research", "computation"],
        "mcp_servers": [],
        "builtin": True,
        "tags": ["research", "information"],
    },
    {
        "name": "domain_expert",
        "display_name": "Domain Expert",
        "description": "Provides deep domain knowledge, explanations, and problem-solving.",
        "specialist_type": "domain_expert",
        "system_prompt": (
            "You are a {specialization} Subject Expert. "
            "Provide accurate domain knowledge, analyse complex problems, "
            "validate information, and create supporting materials. "
            "Produce actual explanations with supporting materials — not just descriptions."
        ),
        "capabilities": [
            "domain_knowledge_provision", "concept_explanation",
            "problem_analysis", "solution_validation", "expert_guidance",
        ],
        "built_in_tools": ["media", "computation", "research"],
        "mcp_servers": [],
        "builtin": True,
        "tags": ["knowledge", "expertise"],
    },
    {
        "name": "analyst",
        "display_name": "Analyst",
        "description": "Analyses data, designs evaluations, and produces structured reports.",
        "specialist_type": "analyst",
        "system_prompt": (
            "You are an Analyst Specialist for {specialization}. "
            "Design evaluations, analyse data, and produce structured, actionable reports. "
            "Always deliver actual output files with URLs — not just descriptions."
        ),
        "capabilities": [
            "analysis_design", "data_analysis", "evaluation",
            "reporting", "structured_output",
        ],
        "built_in_tools": ["file", "media", "computation"],
        "mcp_servers": [],
        "builtin": True,
        "tags": ["analysis", "reporting"],
    },
    {
        "name": "executor",
        "display_name": "Executor",
        "description": "Executes tasks: file operations, computation, and structured delivery.",
        "specialist_type": "executor",
        "system_prompt": (
            "You are a Domain Expert Specialist for {specialization}. "
            "Analyse requests, design deliverables, and create all necessary materials "
            "using your tools. Produce actual materials — not descriptions."
        ),
        "capabilities": [
            "domain_knowledge_provision", "concept_explanation",
            "problem_analysis", "solution_validation", "expert_guidance",
        ],
        "built_in_tools": ["file", "media", "computation"],
        "mcp_servers": [],
        "builtin": True,
        "tags": ["execution", "file", "computation"],
    },
    {
        "name": "media_producer",
        "display_name": "Media Producer",
        "description": "Produces professional media: images, audio, and video.",
        "specialist_type": "media_producer",
        "system_prompt": (
            "You are a Media Production Agent for {specialization}. "
            "Produce professional videos end-to-end: script, images, narration, assembly. "
            "Always return the actual local_path of the final video file."
        ),
        "capabilities": [
            "video_creation", "video_planning", "creative_direction",
            "production_orchestration", "asset_coordination",
        ],
        "built_in_tools": ["media"],
        "mcp_servers": [],
        "builtin": True,
        "tags": ["media", "video", "audio", "image"],
    },
]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class ColoneeRegistry:
    """
    In-memory registry of Colonee definitions with optional JSON persistence.

    Built-in colonees are loaded at startup and cannot be deleted.
    User-defined colonees can be created, updated, enabled/disabled, and deleted.

    Persistence: if COLONEES_REGISTRY_PATH is set (or defaults to
    colonees_files/colonee_registry.json), definitions are saved to disk
    and reloaded on startup.
    """

    def __init__(self, persist_path: Optional[str] = None):
        self._colonees: Dict[str, ColoneeDefinition] = {}
        self._persist_path = Path(
            persist_path
            or os.getenv("COLONEES_REGISTRY_PATH", "colonees_files/colonee_registry.json")
        )
        self._load_builtins()
        self._load_persisted()

    # ------------------------------------------------------------------
    # Startup
    # ------------------------------------------------------------------

    def _load_builtins(self) -> None:
        for raw in _BUILTIN_COLONEES:
            defn = ColoneeDefinition.from_dict(raw)
            self._colonees[defn.name] = defn
        logger.info("Loaded %d built-in colonees", len(_BUILTIN_COLONEES))

    def _load_persisted(self) -> None:
        if not self._persist_path.exists():
            return
        try:
            data = json.loads(self._persist_path.read_text())
            loaded = 0
            for raw in data:
                if raw.get("builtin"):
                    continue  # never overwrite builtins from disk
                defn = ColoneeDefinition.from_dict(raw)
                self._colonees[defn.name] = defn
                loaded += 1
            logger.info("Loaded %d user-defined colonees from %s", loaded, self._persist_path)
        except Exception as e:
            logger.warning("Failed to load persisted colonees: %s", e)

    def _persist(self) -> None:
        try:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            data = [c.to_dict() for c in self._colonees.values() if not c.builtin]
            self._persist_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.warning("Failed to persist colonees: %s", e)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(self, defn: ColoneeDefinition) -> ColoneeDefinition:
        if defn.name in self._colonees:
            raise ValueError(f"Colonee '{defn.name}' already exists.")
        defn.builtin = False
        defn.created_at = datetime.utcnow().isoformat()
        defn.updated_at = defn.created_at
        self._colonees[defn.name] = defn
        self._persist()
        logger.info("Colonee created: '%s'", defn.name)
        return defn

    def get(self, name: str) -> Optional[ColoneeDefinition]:
        return self._colonees.get(name)

    def list(
        self,
        enabled_only: bool = False,
        tags: Optional[List[str]] = None,
    ) -> List[ColoneeDefinition]:
        result = list(self._colonees.values())
        if enabled_only:
            result = [c for c in result if c.enabled]
        if tags:
            result = [c for c in result if any(t in c.tags for t in tags)]
        return result

    def update(self, name: str, updates: Dict[str, Any]) -> ColoneeDefinition:
        defn = self._colonees.get(name)
        if not defn:
            raise KeyError(f"Colonee '{name}' not found.")
        # Prevent overwriting identity / builtin flag
        for protected in ("name", "builtin", "created_at", "created_by"):
            updates.pop(protected, None)
        updates["updated_at"] = datetime.utcnow().isoformat()
        # Nested dataclass updates
        for key in ("memory", "constraints", "evaluation"):
            if key in updates and isinstance(updates[key], dict):
                current = asdict(getattr(defn, key))
                current.update(updates.pop(key))
                cls = {"memory": MemoryConfig, "constraints": ConstraintsConfig, "evaluation": EvaluationConfig}[key]
                setattr(defn, key, cls(**current))
        for k, v in updates.items():
            if hasattr(defn, k):
                setattr(defn, k, v)
        self._persist()
        logger.info("Colonee updated: '%s'", name)
        return defn

    def delete(self, name: str) -> bool:
        defn = self._colonees.get(name)
        if not defn:
            raise KeyError(f"Colonee '{name}' not found.")
        if defn.builtin:
            raise PermissionError(f"Built-in colonee '{name}' cannot be deleted.")
        del self._colonees[name]
        self._persist()
        logger.info("Colonee deleted: '%s'", name)
        return True

    def enable(self, name: str) -> ColoneeDefinition:
        return self.update(name, {"enabled": True})

    def disable(self, name: str) -> ColoneeDefinition:
        return self.update(name, {"enabled": False})
