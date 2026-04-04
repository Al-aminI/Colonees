"""
Workspace Manager
Groups colonees, MCP servers, and knowledge bases into logical workspaces
for specific use cases.

A workspace is a named grouping that lets users organise their agent swarm
by domain or project — e.g. "Customer Support", "Legal Research", etc.
When a workspace is referenced in an /invoke call, its colonee list is used
as the default allowlist for the superagent.
"""

import json
import logging
import os
import threading
from copy import deepcopy
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class WorkspaceDefinition:
    """A workspace groups colonees + MCP servers + knowledge bases for a use case."""

    name: str                                        # slug: "customer_support"
    display_name: str                                # "Customer Support"
    description: str

    colonees: List[str] = field(default_factory=list)        # colonee names
    mcp_servers: List[str] = field(default_factory=list)     # MCP server names
    knowledge_bases: List[str] = field(default_factory=list) # knowledge base names

    icon: str = ""                                   # emoji or icon name
    color: str = "#3b82f6"                           # hex color for UI

    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    created_by: str = "system"
    enabled: bool = True

    # -- serialisation -------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "WorkspaceDefinition":
        d = deepcopy(d)
        return cls(**d)


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------

class WorkspaceManager:
    """
    In-memory registry of workspace definitions with JSON file persistence.

    Thread-safe: all mutating operations acquire a lock before touching
    internal state or writing to disk.
    """

    def __init__(self, storage_dir: str):
        self._workspaces: Dict[str, WorkspaceDefinition] = {}
        self._storage_path = Path(os.path.join(storage_dir, "workspaces.json"))
        self._lock = threading.Lock()
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load workspace definitions from disk."""
        if not self._storage_path.exists():
            logger.info("No workspace file at %s — starting empty", self._storage_path)
            return
        try:
            data = json.loads(self._storage_path.read_text())
            for raw in data:
                defn = WorkspaceDefinition.from_dict(raw)
                self._workspaces[defn.name] = defn
            logger.info(
                "Loaded %d workspaces from %s", len(self._workspaces), self._storage_path
            )
        except Exception as e:
            logger.warning("Failed to load workspaces: %s", e)

    def _save(self) -> None:
        """Persist all workspace definitions to disk."""
        try:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = [ws.to_dict() for ws in self._workspaces.values()]
            self._storage_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.warning("Failed to save workspaces: %s", e)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(self, defn: WorkspaceDefinition) -> WorkspaceDefinition:
        """Create a new workspace. Raises ValueError if the name is taken."""
        with self._lock:
            if defn.name in self._workspaces:
                raise ValueError(f"Workspace '{defn.name}' already exists.")
            now = datetime.now(timezone.utc).isoformat()
            defn.created_at = now
            defn.updated_at = now
            self._workspaces[defn.name] = defn
            self._save()
            logger.info("Workspace created: '%s'", defn.name)
            return defn

    def get(self, name: str) -> Optional[WorkspaceDefinition]:
        """Return a workspace by name, or None if not found."""
        return self._workspaces.get(name)

    def list(self, enabled_only: bool = False) -> List[WorkspaceDefinition]:
        """Return all workspaces, optionally filtered to enabled ones only."""
        result = list(self._workspaces.values())
        if enabled_only:
            result = [ws for ws in result if ws.enabled]
        return result

    def update(self, name: str, updates: Dict[str, Any]) -> WorkspaceDefinition:
        """
        Apply partial updates to an existing workspace.
        Raises KeyError if the workspace does not exist.
        Protected fields (name, created_at, created_by) are silently dropped.
        """
        with self._lock:
            defn = self._workspaces.get(name)
            if not defn:
                raise KeyError(f"Workspace '{name}' not found.")

            # Prevent overwriting identity fields
            for protected in ("name", "created_at", "created_by"):
                updates.pop(protected, None)

            updates["updated_at"] = datetime.now(timezone.utc).isoformat()

            for k, v in updates.items():
                if hasattr(defn, k):
                    setattr(defn, k, v)

            self._save()
            logger.info("Workspace updated: '%s'", name)
            return defn

    def delete(self, name: str) -> bool:
        """Delete a workspace. Raises KeyError if not found."""
        with self._lock:
            if name not in self._workspaces:
                raise KeyError(f"Workspace '{name}' not found.")
            del self._workspaces[name]
            self._save()
            logger.info("Workspace deleted: '%s'", name)
            return True

    def enable(self, name: str) -> WorkspaceDefinition:
        """Enable a workspace."""
        return self.update(name, {"enabled": True})

    def disable(self, name: str) -> WorkspaceDefinition:
        """Disable a workspace."""
        return self.update(name, {"enabled": False})

    # ------------------------------------------------------------------
    # Convenience accessors
    # ------------------------------------------------------------------

    def get_workspace_colonees(self, name: str) -> List[str]:
        """Return the list of colonee names for a workspace. Raises KeyError if not found."""
        defn = self._workspaces.get(name)
        if not defn:
            raise KeyError(f"Workspace '{name}' not found.")
        return list(defn.colonees)

    def get_workspace_mcp_servers(self, name: str) -> List[str]:
        """Return the list of MCP server names for a workspace. Raises KeyError if not found."""
        defn = self._workspaces.get(name)
        if not defn:
            raise KeyError(f"Workspace '{name}' not found.")
        return list(defn.mcp_servers)
