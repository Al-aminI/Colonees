// ── System ─────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string
  service: string
}

export interface PlatformMetrics {
  total_sessions_created: number
  total_agents_spawned: number
  total_requests_handled: number
  platform_start_time: string | null
}

export interface PlatformStatus {
  platform_initialized: boolean
  active_sessions: number
  metrics: PlatformMetrics
  resource_stats: Record<string, unknown>
  memory_stats: Record<string, unknown>
  config_summary: {
    max_concurrent_users: number
    max_active_sessions: number
    environment: string
  }
}

// ── Colonees ───────────────────────────────────────────────────────────────

export type SpecialistType = string

export type BuiltInTool = 'file' | 'computation' | 'research' | 'media'

export interface MemoryConfig {
  enabled: boolean
  strategy: 'basic' | 'semantic' | 'episodic'
  max_size_mb: number
}

export interface ConstraintsConfig {
  max_tool_calls: number
  max_runtime_seconds: number
  forbidden_topics: string[]
  output_format: string | null
}

export interface EvaluationConfig {
  quality_threshold: number
  require_sources: boolean
  require_structured_output: boolean
  custom_criteria: string[]
}

export interface ColoneeDefinition {
  name: string
  display_name: string
  description: string
  specialist_type: SpecialistType
  system_prompt: string
  capabilities: string[]
  built_in_tools: BuiltInTool[]
  mcp_servers: string[]
  memory: MemoryConfig
  constraints: ConstraintsConfig
  evaluation: EvaluationConfig
  enabled: boolean
  builtin: boolean
  tags: string[]
  created_at: string
  updated_at: string
  created_by?: string
}

export type CreateColoneePayload = Omit<ColoneeDefinition, 'created_at' | 'updated_at' | 'builtin'>

export type UpdateColoneePayload = Partial<
  Omit<ColoneeDefinition, 'name' | 'builtin' | 'created_at' | 'updated_at'>
>

// ── MCP Servers ────────────────────────────────────────────────────────────

export type McpTransport = 'streamable_http' | 'sse' | 'stdio'

export interface McpServerConfig {
  name: string
  transport: McpTransport
  url: string | null
  command: string | null
  args: string[]
  headers: Record<string, string> | null
  env: Record<string, string> | null
  specialist_types: string[]
}

export interface CreateMcpServerPayload {
  name: string
  transport: McpTransport
  url?: string
  headers?: Record<string, string>
  command?: string
  args?: string[]
  env?: Record<string, string>
  specialist_types?: string[]
}

// ── Sessions / History ─────────────────────────────────────────────────────

export interface HistoryTurn {
  role: 'user' | 'assistant' | 'error' | 'tool'
  content: string
  timestamp?: string
  metadata?: Record<string, unknown>
}

export interface SessionHistory {
  session_id: string
  history: HistoryTurn[]
  count: number
}

// ── Invoke ────────────────────────────────────────────────────────────────

export interface InvokePayload {
  goal: string
  session_id?: string
  user_id?: string
  context?: Record<string, unknown>
  colonees?: string[]
  workspace?: string
}

export interface InvokeResponse {
  status: string
  result: unknown
  session_id?: string
}

// ── Workspaces ──────────────────────────────────────────────────────────────

export interface WorkspaceDefinition {
  name: string
  display_name: string
  description: string
  colonees: string[]
  knowledge_bases: string[]
  icon: string
  color: string
  created_at: string
  updated_at: string
  created_by: string
  enabled: boolean
}

export interface CreateWorkspacePayload {
  name: string
  display_name: string
  description: string
  colonees?: string[]
  knowledge_bases?: string[]
  icon?: string
  color?: string
  enabled?: boolean
}

export type UpdateWorkspacePayload = Partial<Omit<WorkspaceDefinition, 'name' | 'created_at' | 'created_by'>>

// ── Knowledge Bases ─────────────────────────────────────────────────────────

export type KnowledgeBaseType = 'files' | 'database' | 'api'

export interface KnowledgeBaseDefinition {
  name: string
  display_name: string
  description: string
  type: KnowledgeBaseType
  file_paths: string[]
  config: Record<string, unknown>
  specialist_types: string[]
  workspaces: string[]
  enabled: boolean
  created_at: string
  updated_at: string
  stats: {
    total_files: number
    total_chunks: number
    total_size_bytes: number
  }
}

export interface CreateKnowledgeBasePayload {
  name: string
  display_name: string
  description: string
  type?: KnowledgeBaseType
  specialist_types?: string[]
  workspaces?: string[]
  enabled?: boolean
}

export interface KBFileInfo {
  name: string
  size: number
  uploaded_at: string
}

export interface KBSearchResult {
  content: string
  source: string
  score: number
}

// ── Templates ───────────────────────────────────────────────────────────────

export interface McpServerSuggestion {
  name: string
  description: string
  transport: string
}

export interface UseCaseTemplate {
  name: string
  display_name: string
  description: string
  category: string
  icon: string
  color: string
  colonees: Record<string, unknown>[]
  mcp_server_suggestions: McpServerSuggestion[]
  workspace_config: Record<string, unknown>
  recommended_knowledge_bases: string[]
  tags: string[]
}

export interface TemplateCategory {
  name: string
  display_name: string
  icon: string
  count: number
}

export interface TemplateApplyResult {
  status: string
  workspace: string
  colonees_created: string[]
  colonees_skipped: string[]
  knowledge_bases_created: string[]
}

// ── Connectors ──────────────────────────────────────────────────────────────

export interface ConnectorDefinition {
  name: string
  display_name: string
  description: string
  type: string       // "openapi", "repo", "database", "webhook", "oauth_service"
  provider: string   // "custom", "github", "gmail", "slack", etc.
  config: Record<string, any>
  credentials: Record<string, string>   // values are "***" in responses
  status: string     // "connected", "disconnected", "error", "syncing"
  status_message: string
  tools_generated: string[]
  workspaces: string[]
  specialist_types: string[]
  enabled: boolean
  created_at: string
  updated_at: string
  last_synced_at: string
  sync_stats: Record<string, any>
}

export interface CreateConnectorPayload {
  name: string
  display_name: string
  description: string
  type: string
  provider?: string
  config?: Record<string, any>
  credentials?: Record<string, string>
  workspaces?: string[]
  specialist_types?: string[]
}

export interface ConnectorCatalogEntry {
  id: string
  display_name: string
  description: string
  category: string
  type: string
  provider: string
  icon: string
  config_schema: Record<string, any>
  credential_schema: Record<string, any>
}

export interface ConnectorCatalogCategory {
  name: string
  display_name: string
  count: number
}
