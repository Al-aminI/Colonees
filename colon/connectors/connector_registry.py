import os
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

@dataclass
class ConnectorDefinition:
    name: str                           # slug: "myapp_api"
    display_name: str                   # "MyApp API"
    description: str
    type: str                           # "openapi", "repo", "database", "webhook", "oauth_service"
    provider: str                       # "custom", "github", "gmail", "slack", "postgres", etc.
    config: Dict[str, Any] = field(default_factory=dict)
    # For openapi: {spec_url, base_url, auth_type, auth_header_name}
    # For repo: {repo_url, branch, include_patterns, exclude_patterns}
    # For database: {db_type, host, port, database, ssl}
    # For webhook: {url, method, headers}
    # For oauth_service: {provider, scopes, token_url, auth_url}
    credentials: Dict[str, str] = field(default_factory=dict)
    # Stored masked in responses. Keys depend on type:
    # openapi: {api_key, bearer_token}
    # repo: {access_token}
    # database: {password, connection_string}
    # oauth_service: {client_id, client_secret, access_token, refresh_token}
    status: str = "disconnected"        # "connected", "disconnected", "error", "syncing"
    status_message: str = ""
    tools_generated: List[str] = field(default_factory=list)  # names of auto-generated tools
    workspaces: List[str] = field(default_factory=list)       # scoped to these workspaces
    specialist_types: List[str] = field(default_factory=list)  # scoped to these agent types (empty = all)
    enabled: bool = True
    created_at: str = ""
    updated_at: str = ""
    last_synced_at: str = ""
    sync_stats: Dict[str, Any] = field(default_factory=dict)
    # For repos: {files_indexed, total_size_bytes, last_commit}
    # For openapi: {endpoints_found, methods_mapped}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'type': self.type,
            'provider': self.provider,
            'config': self.config,
            'credentials': self.credentials,
            'status': self.status,
            'status_message': self.status_message,
            'tools_generated': self.tools_generated,
            'workspaces': self.workspaces,
            'specialist_types': self.specialist_types,
            'enabled': self.enabled,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_synced_at': self.last_synced_at,
            'sync_stats': self.sync_stats,
        }

    def to_safe_dict(self) -> Dict[str, Any]:
        """Returns dict with credentials masked."""
        d = self.to_dict()
        d['credentials'] = {k: '***' for k in self.credentials}
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConnectorDefinition':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class ConnectorManager:
    """Manages connector definitions and persistence."""

    def __init__(self, storage_dir: str):
        self._connectors: Dict[str, ConnectorDefinition] = {}
        self._storage_path = os.path.join(storage_dir, 'connectors.json')
        self._connectors_data_dir = os.path.join(storage_dir, 'connector_data')
        os.makedirs(self._connectors_data_dir, exist_ok=True)
        self._load()

    def _load(self):
        if os.path.exists(self._storage_path):
            try:
                with open(self._storage_path) as f:
                    data = json.load(f)
                for item in data:
                    defn = ConnectorDefinition.from_dict(item)
                    self._connectors[defn.name] = defn
                logger.info(f"Loaded {len(self._connectors)} connectors")
            except Exception as e:
                logger.error(f"Failed to load connectors: {e}")

    def _save(self):
        try:
            with open(self._storage_path, 'w') as f:
                json.dump([c.to_dict() for c in self._connectors.values()], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save connectors: {e}")

    def create(self, name: str, display_name: str, description: str, type: str,
               provider: str = "custom", config: Dict = None, credentials: Dict = None,
               workspaces: List[str] = None, specialist_types: List[str] = None) -> ConnectorDefinition:
        if name in self._connectors:
            raise ValueError(f"Connector '{name}' already exists")
        now = datetime.now(timezone.utc).isoformat()
        defn = ConnectorDefinition(
            name=name,
            display_name=display_name,
            description=description,
            type=type,
            provider=provider,
            config=config or {},
            credentials=credentials or {},
            workspaces=workspaces or [],
            specialist_types=specialist_types or [],
            created_at=now,
            updated_at=now,
        )
        self._connectors[name] = defn
        self._save()
        return defn

    def get(self, name: str) -> Optional[ConnectorDefinition]:
        return self._connectors.get(name)

    def list(self, type_filter: str = None, workspace: str = None) -> List[ConnectorDefinition]:
        result = list(self._connectors.values())
        if type_filter:
            result = [c for c in result if c.type == type_filter]
        if workspace:
            result = [c for c in result if not c.workspaces or workspace in c.workspaces]
        return result

    def update(self, name: str, **kwargs) -> ConnectorDefinition:
        defn = self._connectors.get(name)
        if not defn:
            raise ValueError(f"Connector '{name}' not found")
        protected = {'name', 'created_at'}
        for key, val in kwargs.items():
            if key in protected:
                continue
            if hasattr(defn, key):
                setattr(defn, key, val)
        defn.updated_at = datetime.now(timezone.utc).isoformat()
        self._save()
        return defn

    def delete(self, name: str):
        if name not in self._connectors:
            raise ValueError(f"Connector '{name}' not found")
        del self._connectors[name]
        self._save()

    def update_status(self, name: str, status: str, message: str = "",
                      tools: List[str] = None, sync_stats: Dict = None):
        defn = self._connectors.get(name)
        if not defn:
            return
        defn.status = status
        defn.status_message = message
        if tools is not None:
            defn.tools_generated = tools
        if sync_stats is not None:
            defn.sync_stats = sync_stats
        defn.updated_at = datetime.now(timezone.utc).isoformat()
        if status == "connected":
            defn.last_synced_at = defn.updated_at
        self._save()

    def get_connector_data_dir(self, name: str) -> str:
        """Returns the data directory for a connector (for storing cloned repos, cached specs, etc.)"""
        d = os.path.join(self._connectors_data_dir, name)
        os.makedirs(d, exist_ok=True)
        return d

    def get_connectors_for_workspace(self, workspace: str) -> List[ConnectorDefinition]:
        """Get all enabled connectors scoped to a workspace."""
        return [c for c in self._connectors.values()
                if c.enabled and (not c.workspaces or workspace in c.workspaces)]

    def get_connectors_for_specialist(self, specialist_type: str) -> List[ConnectorDefinition]:
        """Get all enabled connectors scoped to a specialist type."""
        return [c for c in self._connectors.values()
                if c.enabled and (not c.specialist_types or specialist_type in c.specialist_types)]
