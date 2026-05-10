from typing import Any, Dict, List


class ConnectorCatalog:
    """
    Catalog of connector configurations for services that don't have
    MCP (Model Context Protocol) servers available.

    These are legacy integration methods:
      - openapi:  Parse any OpenAPI/Swagger spec to auto-generate REST tools.
      - repo:     Clone a git repo and provide code search/read tools.
      - webhook:  Simple outbound HTTP webhook.

    For all popular services (Slack, GitHub, Gmail, Notion, PostgreSQL, etc.),
    use the MCP Servers tab — MCP provides purpose-built, type-safe tools.
    """

    @staticmethod
    def get_catalog() -> List[Dict[str, Any]]:
        return [
            # -- Generic OpenAPI --
            {
                "id": "openapi_custom",
                "display_name": "Custom API (OpenAPI/Swagger)",
                "description": "Connect any REST API by providing its OpenAPI/Swagger spec URL. Tools are auto-generated for each endpoint. Use for legacy APIs that don't have an MCP server.",
                "category": "api",
                "type": "openapi",
                "provider": "custom",
                "icon": "globe",
                "config_schema": {
                    "spec_url": {"type": "string", "label": "Swagger/OpenAPI Spec URL", "required": True, "placeholder": "https://api.example.com/openapi.json"},
                    "base_url": {"type": "string", "label": "Base URL (override)", "required": False, "placeholder": "https://api.example.com/v1"},
                    "auth_type": {"type": "select", "label": "Auth Type", "options": ["none", "bearer", "api_key", "basic"], "required": False},
                },
                "credential_schema": {
                    "api_key_or_token": {"type": "password", "label": "API Key / Bearer Token", "required": False},
                },
            },
            # -- Code Repositories --
            {
                "id": "github_repo",
                "display_name": "GitHub Repository",
                "description": "Clone a GitHub repository and give agents code search, file read, and structure exploration tools.",
                "category": "code",
                "type": "repo",
                "provider": "github",
                "icon": "github",
                "config_schema": {
                    "repo_url": {"type": "string", "label": "Repository URL", "required": True, "placeholder": "https://github.com/owner/repo"},
                    "branch": {"type": "string", "label": "Branch", "required": False, "default": "main"},
                },
                "credential_schema": {
                    "access_token": {"type": "password", "label": "GitHub Access Token", "required": False, "help": "Required for private repos"},
                },
            },
            {
                "id": "gitlab_repo",
                "display_name": "GitLab Repository",
                "description": "Clone a GitLab repository for code search and understanding.",
                "category": "code",
                "type": "repo",
                "provider": "gitlab",
                "icon": "gitlab",
                "config_schema": {
                    "repo_url": {"type": "string", "label": "Repository URL", "required": True},
                    "branch": {"type": "string", "label": "Branch", "required": False, "default": "main"},
                },
                "credential_schema": {
                    "access_token": {"type": "password", "label": "GitLab Access Token", "required": False},
                },
            },
            # -- Webhook --
            {
                "id": "webhook_custom",
                "display_name": "Custom Webhook",
                "description": "Connect any webhook endpoint. Agents can send data to external services via HTTP.",
                "category": "integration",
                "type": "webhook",
                "provider": "custom",
                "icon": "webhook",
                "config_schema": {
                    "url": {"type": "string", "label": "Webhook URL", "required": True, "placeholder": "https://hooks.example.com/trigger"},
                    "method": {"type": "select", "label": "HTTP Method", "options": ["POST", "PUT", "PATCH"], "required": False, "default": "POST"},
                },
                "credential_schema": {
                    "auth_header": {"type": "password", "label": "Authorization Header Value", "required": False},
                },
            },
        ]

    @staticmethod
    def get_categories() -> List[Dict[str, str]]:
        catalog = ConnectorCatalog.get_catalog()
        cats = {}
        for entry in catalog:
            cat = entry['category']
            if cat not in cats:
                cats[cat] = {"name": cat, "display_name": cat.replace('_', ' ').title(), "count": 0}
            cats[cat]["count"] += 1
        return list(cats.values())

    @staticmethod
    def get_by_id(catalog_id: str) -> Dict[str, Any] | None:
        for entry in ConnectorCatalog.get_catalog():
            if entry['id'] == catalog_id:
                return entry
        return None

    @staticmethod
    def get_by_category(category: str) -> List[Dict[str, Any]]:
        return [e for e in ConnectorCatalog.get_catalog() if e['category'] == category]
