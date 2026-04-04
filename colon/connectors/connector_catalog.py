from typing import Any, Dict, List


class ConnectorCatalog:
    """
    Catalog of pre-built connector configurations for popular services.
    Users pick a catalog entry, fill in credentials, and connect.
    """

    @staticmethod
    def get_catalog() -> List[Dict[str, Any]]:
        return [
            # -- API Connectors --
            {
                "id": "openapi_custom",
                "display_name": "Custom API (OpenAPI/Swagger)",
                "description": "Connect any REST API by providing its OpenAPI/Swagger spec URL. Tools are auto-generated for each endpoint.",
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
                "description": "Connect a GitHub repository. Agents can search code, read files, and understand the project structure.",
                "category": "code",
                "type": "repo",
                "provider": "github",
                "icon": "github",
                "config_schema": {
                    "repo_url": {"type": "string", "label": "Repository URL", "required": True, "placeholder": "https://github.com/owner/repo"},
                    "branch": {"type": "string", "label": "Branch", "required": False, "default": "main"},
                },
                "credential_schema": {
                    "access_token": {"type": "password", "label": "GitHub Personal Access Token", "required": False, "help": "Required for private repos"},
                },
            },
            {
                "id": "gitlab_repo",
                "display_name": "GitLab Repository",
                "description": "Connect a GitLab repository for code search and understanding.",
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
            # -- Communication --
            {
                "id": "slack_api",
                "display_name": "Slack",
                "description": "Connect to Slack to read/send messages, manage channels, and interact with your workspace.",
                "category": "communication",
                "type": "openapi",
                "provider": "slack",
                "icon": "message-square",
                "config_schema": {
                    "spec_url": {"type": "hidden", "default": "https://raw.githubusercontent.com/slackapi/slack-api-specs/master/web-api/slack_web_openapi_v2.json"},
                    "base_url": {"type": "hidden", "default": "https://slack.com/api"},
                    "auth_type": {"type": "hidden", "default": "bearer"},
                },
                "credential_schema": {
                    "api_key_or_token": {"type": "password", "label": "Slack Bot Token", "required": True, "placeholder": "xoxb-..."},
                },
            },
            {
                "id": "telegram_bot",
                "display_name": "Telegram Bot",
                "description": "Connect a Telegram bot to send/receive messages and manage chats.",
                "category": "communication",
                "type": "openapi",
                "provider": "telegram",
                "icon": "send",
                "config_schema": {
                    "base_url": {"type": "computed", "template": "https://api.telegram.org/bot{bot_token}"},
                    "auth_type": {"type": "hidden", "default": "none"},
                },
                "credential_schema": {
                    "bot_token": {"type": "password", "label": "Bot Token", "required": True, "placeholder": "123456:ABC-DEF..."},
                },
            },
            # -- Google Services --
            {
                "id": "gmail_api",
                "display_name": "Gmail",
                "description": "Connect Gmail to read, search, and send emails through your agents.",
                "category": "google",
                "type": "openapi",
                "provider": "gmail",
                "icon": "mail",
                "config_schema": {
                    "spec_url": {"type": "hidden", "default": "https://gmail.googleapis.com/$discovery/rest?version=v1"},
                    "base_url": {"type": "hidden", "default": "https://gmail.googleapis.com/gmail/v1"},
                    "auth_type": {"type": "hidden", "default": "bearer"},
                },
                "credential_schema": {
                    "api_key_or_token": {"type": "password", "label": "OAuth Access Token", "required": True},
                },
            },
            {
                "id": "google_docs_api",
                "display_name": "Google Docs",
                "description": "Connect Google Docs to read and create documents.",
                "category": "google",
                "type": "openapi",
                "provider": "google_docs",
                "icon": "file-text",
                "config_schema": {
                    "base_url": {"type": "hidden", "default": "https://docs.googleapis.com/v1"},
                    "auth_type": {"type": "hidden", "default": "bearer"},
                },
                "credential_schema": {
                    "api_key_or_token": {"type": "password", "label": "OAuth Access Token", "required": True},
                },
            },
            {
                "id": "google_drive_api",
                "display_name": "Google Drive",
                "description": "Connect Google Drive to list, search, read, and manage files.",
                "category": "google",
                "type": "openapi",
                "provider": "google_drive",
                "icon": "hard-drive",
                "config_schema": {
                    "base_url": {"type": "hidden", "default": "https://www.googleapis.com/drive/v3"},
                    "auth_type": {"type": "hidden", "default": "bearer"},
                },
                "credential_schema": {
                    "api_key_or_token": {"type": "password", "label": "OAuth Access Token", "required": True},
                },
            },
            # -- Databases --
            {
                "id": "postgres_db",
                "display_name": "PostgreSQL",
                "description": "Connect a PostgreSQL database. Agents can query tables, describe schema, and analyze data.",
                "category": "database",
                "type": "database",
                "provider": "postgres",
                "icon": "database",
                "config_schema": {
                    "host": {"type": "string", "label": "Host", "required": True, "placeholder": "localhost"},
                    "port": {"type": "number", "label": "Port", "required": False, "default": 5432},
                    "database": {"type": "string", "label": "Database Name", "required": True},
                    "username": {"type": "string", "label": "Username", "required": True},
                },
                "credential_schema": {
                    "password": {"type": "password", "label": "Password", "required": True},
                },
            },
            # -- Cloud Storage --
            {
                "id": "s3_bucket",
                "display_name": "AWS S3 Bucket",
                "description": "Connect an S3 bucket to list, read, and search files.",
                "category": "storage",
                "type": "webhook",
                "provider": "s3",
                "icon": "cloud",
                "config_schema": {
                    "bucket": {"type": "string", "label": "Bucket Name", "required": True},
                    "region": {"type": "string", "label": "AWS Region", "required": True, "default": "us-east-1"},
                    "prefix": {"type": "string", "label": "Key Prefix", "required": False},
                },
                "credential_schema": {
                    "aws_access_key_id": {"type": "password", "label": "AWS Access Key ID", "required": True},
                    "aws_secret_access_key": {"type": "password", "label": "AWS Secret Access Key", "required": True},
                },
            },
            # -- Project Management --
            {
                "id": "notion_api",
                "display_name": "Notion",
                "description": "Connect Notion to read pages, databases, and manage content.",
                "category": "productivity",
                "type": "openapi",
                "provider": "notion",
                "icon": "book-open",
                "config_schema": {
                    "base_url": {"type": "hidden", "default": "https://api.notion.com/v1"},
                    "auth_type": {"type": "hidden", "default": "bearer"},
                },
                "credential_schema": {
                    "api_key_or_token": {"type": "password", "label": "Notion Integration Token", "required": True, "placeholder": "ntn_..."},
                },
            },
            {
                "id": "linear_api",
                "display_name": "Linear",
                "description": "Connect Linear to manage issues, projects, and track work.",
                "category": "productivity",
                "type": "openapi",
                "provider": "linear",
                "icon": "list-checks",
                "config_schema": {
                    "base_url": {"type": "hidden", "default": "https://api.linear.app"},
                    "auth_type": {"type": "hidden", "default": "bearer"},
                },
                "credential_schema": {
                    "api_key_or_token": {"type": "password", "label": "Linear API Key", "required": True},
                },
            },
            {
                "id": "jira_api",
                "display_name": "Jira",
                "description": "Connect Jira to manage issues, boards, and sprints.",
                "category": "productivity",
                "type": "openapi",
                "provider": "jira",
                "icon": "kanban",
                "config_schema": {
                    "base_url": {"type": "string", "label": "Jira Instance URL", "required": True, "placeholder": "https://yourcompany.atlassian.net"},
                    "auth_type": {"type": "hidden", "default": "basic"},
                },
                "credential_schema": {
                    "api_key_or_token": {"type": "password", "label": "API Token (email:token base64)", "required": True},
                },
            },
            # -- Webhooks --
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
