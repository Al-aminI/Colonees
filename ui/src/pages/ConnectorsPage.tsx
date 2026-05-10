import { useState } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Dialog, DialogHeader } from '@/components/ui/dialog'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import {
  Plug, Plus, Trash2, RefreshCw, Power, ChevronDown, ChevronRight,
  Wrench, Globe, GitBranch, Send, Mail, FileText, HardDrive,
  Database, Cloud, BookOpen, ListChecks, LayoutList, Webhook,
  Server, Zap, Info, Search, ExternalLink, MessageSquare,
  type LucideIcon,
} from 'lucide-react'
import {
  useConnectors, useDeleteConnector, useConnectConnector,
  useSyncConnector, useCreateFromCatalog,
} from '@/hooks/useConnectors'
import { useMcpServers, useRegisterMcpServer, useRemoveMcpServer } from '@/hooks/useMcpServers'
import { McpServerCard } from '@/components/mcp/McpServerCard'
import { McpServerForm } from '@/components/mcp/McpServerForm'
import { useToast } from '@/components/ui/toast'
import { cn } from '@/lib/utils'
import type { ConnectorDefinition, CreateMcpServerPayload } from '@/types'

/* ── Icon map ──────────────────────────────────────────────────────────── */

const iconMap: Record<string, LucideIcon> = {
  globe: Globe, github: GitBranch, gitlab: GitBranch,
  'message-square': MessageSquare, send: Send, mail: Mail,
  'file-text': FileText, 'hard-drive': HardDrive, database: Database,
  cloud: Cloud, 'book-open': BookOpen, 'list-checks': ListChecks,
  kanban: LayoutList, webhook: Webhook, plug: Plug,
  server: Server, search: Search, zap: Zap, external: ExternalLink,
}

function getIcon(name: string): LucideIcon {
  return iconMap[name] ?? Plug
}

/* ── Status + type configs ─────────────────────────────────────────────── */

const statusConfig: Record<string, { dotClass: string; label: string; variant: 'success' | 'secondary' | 'destructive' | 'warning' }> = {
  connected:    { dotClass: 'bg-green-400', label: 'Connected',     variant: 'success' },
  disconnected: { dotClass: 'bg-zinc-400',  label: 'Not connected', variant: 'secondary' },
  error:        { dotClass: 'bg-red-400',   label: 'Error',        variant: 'destructive' },
  syncing:      { dotClass: 'bg-yellow-400 animate-pulse', label: 'Syncing...', variant: 'warning' },
}

const typeColors: Record<string, string> = {
  openapi:  'bg-cyan-500/20 text-cyan-400',
  repo:     'bg-violet-500/20 text-violet-400',
  webhook:  'bg-pink-500/20 text-pink-400',
}

/* ── MCP Preset Catalog ────────────────────────────────────────────────── */

interface McpPreset {
  id: string
  name: string
  display_name: string
  description: string
  icon: string
  transport: 'streamable_http' | 'sse' | 'stdio'
  url?: string
  command?: string
  args?: string[]
  env_example?: string
  headers_example?: string
  category: string
}

const MCP_PRESETS: McpPreset[] = [
  {
    id: 'slack_mcp', name: 'slack', display_name: 'Slack',
    description: 'Read/send messages, manage channels, and interact with your Slack workspace via MCP.',
    icon: 'message-square', transport: 'streamable_http',
    headers_example: '{"Authorization": "Bearer xoxb-your-token"}',
    category: 'communication',
  },
  {
    id: 'telegram_mcp', name: 'telegram', display_name: 'Telegram',
    description: 'Send/receive messages and manage chats via Telegram MCP.',
    icon: 'send', transport: 'stdio',
    command: 'npx',
    args: ['-y', '@anthropic/mcp-server-telegram'],
    env_example: '{"TELEGRAM_BOT_TOKEN": "your-bot-token"}',
    category: 'communication',
  },
  {
    id: 'github_mcp', name: 'github', display_name: 'GitHub',
    description: 'Manage issues, PRs, repos, and code search via GitHub MCP.',
    icon: 'github', transport: 'streamable_http',
    headers_example: '{"Authorization": "Bearer ghp_your-token"}',
    category: 'code',
  },
  {
    id: 'gitlab_mcp', name: 'gitlab', display_name: 'GitLab',
    description: 'Manage merge requests, issues, and repos via GitLab MCP.',
    icon: 'gitlab', transport: 'streamable_http',
    headers_example: '{"Authorization": "Bearer glpat-your-token"}',
    category: 'code',
  },
  {
    id: 'gmail_mcp', name: 'gmail', display_name: 'Gmail',
    description: 'Read, search, and send emails through Gmail MCP.',
    icon: 'mail', transport: 'streamable_http',
    headers_example: '{"Authorization": "Bearer ya29.your-token"}',
    category: 'google',
  },
  {
    id: 'google_docs_mcp', name: 'google_docs', display_name: 'Google Docs',
    description: 'Read and create documents via Google Docs MCP.',
    icon: 'file-text', transport: 'streamable_http',
    headers_example: '{"Authorization": "Bearer ya29.your-token"}',
    category: 'google',
  },
  {
    id: 'google_drive_mcp', name: 'google_drive', display_name: 'Google Drive',
    description: 'List, search, read, and manage files in Google Drive via MCP.',
    icon: 'hard-drive', transport: 'streamable_http',
    headers_example: '{"Authorization": "Bearer ya29.your-token"}',
    category: 'google',
  },
  {
    id: 'notion_mcp', name: 'notion', display_name: 'Notion',
    description: 'Read pages, databases, and manage Notion content via MCP.',
    icon: 'book-open', transport: 'streamable_http',
    headers_example: '{"Authorization": "Bearer ntn_your-token", "Notion-Version": "2022-06-28"}',
    category: 'productivity',
  },
  {
    id: 'linear_mcp', name: 'linear', display_name: 'Linear',
    description: 'Manage issues, projects, and track work in Linear via MCP.',
    icon: 'list-checks', transport: 'streamable_http',
    headers_example: '{"Authorization": "lin_api_your-key"}',
    category: 'productivity',
  },
  {
    id: 'jira_mcp', name: 'jira', display_name: 'Jira',
    description: 'Manage issues, boards, and sprints in Jira via MCP.',
    icon: 'kanban', transport: 'streamable_http',
    headers_example: '{"Authorization": "Basic base64-encoded-credentials"}',
    category: 'productivity',
  },
  {
    id: 'postgres_mcp', name: 'postgres', display_name: 'PostgreSQL',
    description: 'Query tables, describe schema, and analyze data via PostgreSQL MCP.',
    icon: 'database', transport: 'stdio',
    command: 'npx', args: ['-y', '@anthropic/mcp-server-postgres'],
    env_example: '{"DATABASE_URL": "postgresql://user:pass@localhost:5432/db"}',
    category: 'database',
  },
  {
    id: 's3_mcp', name: 's3', display_name: 'AWS S3',
    description: 'List, read, and manage S3 objects via MCP.',
    icon: 'cloud', transport: 'stdio',
    command: 'npx', args: ['-y', '@anthropic/mcp-server-s3'],
    env_example: '{"AWS_ACCESS_KEY_ID": "...", "AWS_SECRET_ACCESS_KEY": "...", "AWS_REGION": "us-east-1"}',
    category: 'storage',
  },
  {
    id: 'filesystem_mcp', name: 'filesystem', display_name: 'Filesystem',
    description: 'Read, write, and manage files on the local filesystem via MCP.',
    icon: 'file-text', transport: 'stdio',
    command: 'npx', args: ['-y', '@anthropic/mcp-server-filesystem', '/path/to/allowed/dir'],
    category: 'utility',
  },
  {
    id: 'brave_search_mcp', name: 'brave_search', display_name: 'Brave Search',
    description: 'Web and local search via Brave Search API MCP.',
    icon: 'search', transport: 'stdio',
    command: 'npx', args: ['-y', '@anthropic/mcp-server-brave-search'],
    env_example: '{"BRAVE_API_KEY": "your-api-key"}',
    category: 'utility',
  },
]

function getPresetCategories(): { name: string; display_name: string; count: number }[] {
  const cats: Record<string, { name: string; display_name: string; count: number }> = {}
  MCP_PRESETS.forEach((p) => {
    if (!cats[p.category]) {
      cats[p.category] = { name: p.category, display_name: p.category.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase()), count: 0 }
    }
    cats[p.category].count++
  })
  return Object.values(cats)
}

/* ── Main page ─────────────────────────────────────────────────────────── */

export function ConnectorsPage() {
  const [tab, setTab] = useState('mcp')

  return (
    <div>
      <PageHeader
        title="Connectors"
        description="Connect external tools and services to your agent swarm"
      />

      <div className="mb-4 rounded-md border border-blue-500/30 bg-blue-500/5 p-3 flex items-start gap-3">
        <Info className="h-4 w-4 text-blue-400 shrink-0 mt-0.5" />
        <div className="text-sm">
          <p className="font-medium text-blue-300">MCP servers are the recommended integration method.</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            Model Context Protocol (MCP) servers provide purpose-built, type-safe tools with rich descriptions.
            The "Legacy Connectors" tab is for OpenAPI, Git repos, and webhooks — use only when an MCP server
            isn't available for your service.
          </p>
        </div>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="mcp">
            <Server className="h-3.5 w-3.5 mr-1.5" /> MCP Servers
          </TabsTrigger>
          <TabsTrigger value="legacy">
            <Plug className="h-3.5 w-3.5 mr-1.5" /> Legacy Connectors
          </TabsTrigger>
        </TabsList>

        <TabsContent value="mcp">
          <McpServersTab />
        </TabsContent>
        <TabsContent value="legacy">
          <LegacyConnectorsTab />
        </TabsContent>
      </Tabs>
    </div>
  )
}

/* ── Tab: MCP Servers ──────────────────────────────────────────────────── */

function McpServersTab() {
  const { data, isLoading } = useMcpServers()
  const registerServer = useRegisterMcpServer()
  const removeServer = useRemoveMcpServer()
  const { toast } = useToast()
  const [showForm, setShowForm] = useState(false)
  const [showPresets, setShowPresets] = useState(false)
  const [presetCategory, setPresetCategory] = useState('all')
  const [selectedPreset, setSelectedPreset] = useState<McpPreset | null>(null)

  const servers = data?.servers ?? []

  const handleRegister = async (values: {
    name: string; transport: string; url?: string; headers_json?: string;
    command?: string; args_str?: string; env_json?: string; specialist_types_str?: string
  }) => {
    const payload: CreateMcpServerPayload = {
      name: values.name,
      transport: values.transport as CreateMcpServerPayload['transport'],
    }
    if (values.url) payload.url = values.url
    if (values.command) payload.command = values.command
    if (values.args_str) payload.args = values.args_str.split(/\s+/).filter(Boolean)
    if (values.headers_json) {
      try { payload.headers = JSON.parse(values.headers_json) } catch {}
    }
    if (values.env_json) {
      try { payload.env = JSON.parse(values.env_json) } catch {}
    }
    if (values.specialist_types_str) {
      payload.specialist_types = values.specialist_types_str.split(',').map((s) => s.trim()).filter(Boolean)
    }
    await registerServer.mutateAsync(payload)
    toast({ title: 'MCP server registered', variant: 'success' })
  }

  const handleDelete = async (name: string) => {
    if (!confirm(`Remove MCP server "${name}"?`)) return
    await removeServer.mutateAsync(name)
    toast({ title: 'Server removed', variant: 'info' })
  }

  const filteredPresets = presetCategory === 'all'
    ? MCP_PRESETS
    : MCP_PRESETS.filter((p) => p.category === presetCategory)

  return (
    <div className="mt-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Button onClick={() => setShowForm(true)}>
            <Plus className="h-4 w-4 mr-2" /> Register MCP Server
          </Button>
          <Button variant="outline" onClick={() => setShowPresets((p) => !p)}>
            <Zap className="h-4 w-4 mr-2" />
            {showPresets ? 'Hide' : 'Browse'} Presets ({MCP_PRESETS.length})
          </Button>
        </div>
      </div>

      {showPresets && (
        <Card className="mb-6">
          <CardContent className="p-4">
            <p className="text-sm font-medium mb-3">MCP Server Presets</p>
            <div className="flex flex-wrap gap-1.5 mb-3">
              <Badge
                variant={presetCategory === 'all' ? 'default' : 'outline'}
                className="cursor-pointer text-[11px]"
                onClick={() => setPresetCategory('all')}
              >
                All ({MCP_PRESETS.length})
              </Badge>
              {getPresetCategories().map((cat) => (
                <Badge
                  key={cat.name}
                  variant={presetCategory === cat.name ? 'default' : 'outline'}
                  className="cursor-pointer text-[11px]"
                  onClick={() => setPresetCategory(cat.name)}
                >
                  {cat.display_name} ({cat.count})
                </Badge>
              ))}
            </div>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {filteredPresets.map((preset) => {
                const Icon = getIcon(preset.icon)
                return (
                  <button
                    key={preset.id}
                    className="flex items-start gap-3 rounded-md border border-border p-3 text-left hover:bg-accent transition-colors"
                    onClick={() => { setSelectedPreset(preset); setShowForm(true) }}
                  >
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-accent">
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium">{preset.display_name}</p>
                      <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">{preset.description}</p>
                      <Badge variant="outline" className="mt-1.5 text-[10px]">{preset.transport}</Badge>
                    </div>
                  </button>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-40" />)}
        </div>
      ) : servers.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground gap-3">
          <Server className="h-12 w-12 opacity-20" />
          <p className="text-sm">No MCP servers registered yet.</p>
          <p className="text-xs">Browse the preset catalog or register a custom MCP server.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {servers.map((s) => (
            <McpServerCard key={s.name} server={s} onDelete={handleDelete} isDeleting={removeServer.isPending} />
          ))}
        </div>
      )}

      <McpServerForm
        open={showForm}
        onClose={() => { setShowForm(false); setSelectedPreset(null) }}
        onSubmit={handleRegister}
        preset={selectedPreset}
      />
    </div>
  )
}

/* ── Tab: Legacy Connectors (OpenAPI, Repo, Webhook) ───────────────────── */

/* ── Quick Create Dialog ───────────────────────────────────────────────── */

interface FieldDef {
  key: string
  label: string
  type: 'text' | 'password' | 'select'
  placeholder?: string
  required?: boolean
  options?: string[]
  default?: string
}

const LEGACY_CONNECTOR_TYPES: {
  id: string
  label: string
  desc: string
  icon: LucideIcon
  quickFields: FieldDef[]
  quickCreds: FieldDef[]
  authTypeField?: { key: string; default: string }
}[] = [
  {
    id: 'openapi_custom', label: 'Add OpenAPI Connector',
    desc: 'Auto-generate tools from any OpenAPI/Swagger spec. For legacy REST APIs without an MCP server.',
    icon: Globe,
    quickFields: [
      { key: 'spec_url', label: 'Spec URL', type: 'text', placeholder: 'https://api.example.com/openapi.json', required: true },
      { key: 'base_url', label: 'Base URL (optional)', type: 'text', placeholder: 'https://api.example.com/v1' },
    ],
    quickCreds: [
      { key: 'api_key_or_token', label: 'API Key / Bearer Token', type: 'password', placeholder: 'sk-...' },
    ],
    authTypeField: { key: 'auth_type', default: 'bearer' },
  },
  {
    id: 'github_repo', label: 'Add Repo Connector',
    desc: 'Clone a Git repo and give agents code search, file read, and structure exploration tools.',
    icon: GitBranch,
    quickFields: [
      { key: 'repo_url', label: 'Repository URL', type: 'text', placeholder: 'https://github.com/owner/repo', required: true },
      { key: 'branch', label: 'Branch', type: 'text', placeholder: 'main' },
    ],
    quickCreds: [
      { key: 'access_token', label: 'Access Token (for private repos)', type: 'password', placeholder: '' },
    ],
  },
  {
    id: 'webhook_custom', label: 'Add Webhook Connector',
    desc: 'Connect a webhook endpoint. Agents can send data to external services via HTTP.',
    icon: Webhook,
    quickFields: [
      { key: 'url', label: 'Webhook URL', type: 'text', placeholder: 'https://hooks.example.com/trigger', required: true },
      { key: 'method', label: 'HTTP Method', type: 'select', options: ['POST', 'PUT', 'PATCH'], default: 'POST' },
    ],
    quickCreds: [
      { key: 'auth_header', label: 'Authorization Header Value', type: 'password', placeholder: '' },
    ],
  },
]

function LegacyConnectorsTab() {
  const { data, isLoading } = useConnectors()
  const deleteConnector = useDeleteConnector()
  const connectConnector = useConnectConnector()
  const syncConnector = useSyncConnector()
  const createFromCatalog = useCreateFromCatalog()
  const { toast } = useToast()
  const [showCreate, setShowCreate] = useState<string | null>(null)

  const connectors = data?.connectors ?? []

  const handleDelete = async (name: string) => {
    if (!confirm(`Delete connector "${name}"?`)) return
    await deleteConnector.mutateAsync(name)
    toast({ title: 'Connector deleted', variant: 'info' })
  }

  const handleConnect = async (name: string) => {
    try {
      await connectConnector.mutateAsync(name)
      toast({ title: 'Connected', variant: 'success' })
    } catch (err) {
      toast({ title: 'Failed to connect', description: err instanceof Error ? err.message : 'Unknown error', variant: 'error' })
    }
  }

  const handleSync = async (name: string) => {
    try {
      await syncConnector.mutateAsync(name)
      toast({ title: 'Sync started', variant: 'success' })
    } catch (err) {
      toast({ title: 'Failed to sync', description: err instanceof Error ? err.message : 'Unknown error', variant: 'error' })
    }
  }

  return (
    <div className="mt-4">
      <div className="mb-4 rounded-md border border-amber-500/20 bg-amber-500/5 p-3 flex items-start gap-3">
        <Info className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
        <div className="text-sm">
          <p className="font-medium text-amber-300">Legacy integration methods.</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            OpenAPI, repo, and webhook connectors are kept for services without MCP server support.
            Prefer the MCP Servers tab for all popular services.
          </p>
        </div>
      </div>

      {/* Quick-add buttons */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 mb-6">
        {LEGACY_CONNECTOR_TYPES.map((type) => {
          const Icon = type.icon
          return (
            <button
              key={type.id}
              className="flex flex-col items-center gap-2 rounded-lg border border-border p-4 text-center hover:bg-accent transition-colors"
              onClick={() => setShowCreate(type.id)}
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-accent">
                <Icon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-medium">{type.label}</p>
                <p className="text-xs text-muted-foreground mt-1">{type.desc}</p>
              </div>
            </button>
          )
        })}
      </div>

      {/* Existing connectors */}
      {connectors.length > 0 && (
        <>
          <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-3">
            Configured ({connectors.length})
          </p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {connectors.map((c) => (
              <ConnectorCard
                key={c.name}
                connector={c}
                onDelete={handleDelete}
                onConnect={handleConnect}
                onSync={handleSync}
                isDeleting={deleteConnector.isPending}
              />
            ))}
          </div>
        </>
      )}

      {isLoading && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-52" />)}
        </div>
      )}

      {!isLoading && connectors.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground gap-3">
          <Plug className="h-10 w-10 opacity-20" />
          <p className="text-sm">No legacy connectors configured.</p>
        </div>
      )}

      {/* Create dialog */}
      {showCreate && (
        <QuickCreateDialog
          typeId={showCreate}
          open={!!showCreate}
          onClose={() => setShowCreate(null)}
          createFromCatalog={createFromCatalog}
          connectConnector={connectConnector}
        />
      )}
    </div>
  )
}

/* ── Legacy Connector Card ─────────────────────────────────────────────── */

function ConnectorCard({
  connector, onDelete, onConnect, onSync, isDeleting,
}: {
  connector: ConnectorDefinition
  onDelete: (name: string) => void
  onConnect: (name: string) => void
  onSync: (name: string) => void
  isDeleting?: boolean
}) {
  const [expanded, setExpanded] = useState(false)
  const status = statusConfig[connector.status] ?? statusConfig.disconnected
  const typeColor = typeColors[connector.type] ?? 'bg-zinc-500/20 text-zinc-400'
  const ProviderIcon = getIcon(connector.provider)

  return (
    <Card>
      <CardContent className="p-4 flex flex-col gap-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <ProviderIcon className="h-4 w-4 text-muted-foreground shrink-0" />
              <span className="font-semibold truncate">{connector.display_name}</span>
            </div>
            <p className="text-xs text-muted-foreground font-mono mt-0.5 truncate">{connector.name}</p>
          </div>
          <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive shrink-0"
            onClick={() => onDelete(connector.name)} disabled={isDeleting}>
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-1.5">
            <span className={cn('h-2 w-2 rounded-full shrink-0', status.dotClass)} />
            <Badge variant={status.variant} className="text-[10px] px-1.5 py-0">{status.label}</Badge>
          </div>
          <span className={cn('inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium', typeColor)}>
            {connector.type}
          </span>
        </div>

        {connector.status === 'error' && connector.status_message && (
          <p className="text-xs text-destructive bg-destructive/10 rounded px-2 py-1">{connector.status_message}</p>
        )}

        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Wrench className="h-3.5 w-3.5" />
          <span>{connector.tools_generated.length} tool{connector.tools_generated.length !== 1 ? 's' : ''}</span>
        </div>

        {connector.workspaces.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {connector.workspaces.map((ws) => <Badge key={ws} variant="secondary" className="text-[10px]">{ws}</Badge>)}
          </div>
        )}

        {connector.last_synced_at && (
          <p className="text-[10px] text-muted-foreground">Last synced: {new Date(connector.last_synced_at).toLocaleString()}</p>
        )}

        <div className="flex items-center gap-2 pt-1">
          {connector.status === 'connected' ? (
            <Button size="sm" variant="outline" onClick={() => onSync(connector.name)}>
              <RefreshCw className="h-3.5 w-3.5 mr-1" /> Sync
            </Button>
          ) : (
            <Button size="sm" onClick={() => onConnect(connector.name)}>
              <Power className="h-3.5 w-3.5 mr-1" /> Connect
            </Button>
          )}
        </div>

        {connector.status === 'connected' && connector.tools_generated.length > 0 && (
          <div>
            <button onClick={() => setExpanded(!expanded)}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors">
              {expanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
              {expanded ? 'Hide' : 'Show'} tools
            </button>
            {expanded && (
              <div className="mt-2 space-y-1 max-h-40 overflow-y-auto">
                {connector.tools_generated.map((tool) => (
                  <div key={tool} className="flex items-center gap-2 rounded px-2 py-1 text-xs bg-accent/50">
                    <Wrench className="h-3 w-3 text-muted-foreground shrink-0" />
                    <span className="font-mono truncate">{tool}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

/* ── Quick Create Dialog ───────────────────────────────────────────────── */

function QuickCreateDialog({
  typeId, open, onClose, createFromCatalog, connectConnector,
}: {
  typeId: string
  open: boolean
  onClose: () => void
  createFromCatalog: ReturnType<typeof useCreateFromCatalog>
  connectConnector: ReturnType<typeof useConnectConnector>
}) {
  const { toast } = useToast()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const typeDef = LEGACY_CONNECTOR_TYPES.find((t) => t.id === typeId)
  if (!typeDef) return null

  const [name, setName] = useState('')
  const [fieldValues, setFieldValues] = useState<Record<string, string>>(() => {
    const vals: Record<string, string> = {}
    typeDef.quickFields.forEach((f) => {
      if (f.default) vals[f.key] = f.default
    })
    if (typeDef.authTypeField) vals[typeDef.authTypeField.key] = typeDef.authTypeField.default
    return vals
  })
  const [credValues, setCredValues] = useState<Record<string, string>>({})

  const handleClose = () => {
    setName('')
    setFieldValues({})
    setCredValues({})
    onClose()
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) {
      toast({ title: 'Name is required', variant: 'error' })
      return
    }
    setIsSubmitting(true)
    try {
      const config: Record<string, string> = { ...fieldValues }
      if (typeDef.authTypeField) {
        config['auth_type'] = config['auth_type'] || typeDef.authTypeField.default
      }
      const connector = await createFromCatalog.mutateAsync({
        catalogId: typeDef.id,
        payload: {
          name: name.replace(/[^a-z0-9_]/g, '_'),
          display_name: typeDef.label.replace('Add ', ''),
          description: typeDef.desc,
          type: typeDef.id === 'openapi_custom' ? 'openapi' : typeDef.id === 'github_repo' ? 'repo' : 'webhook',
          provider: typeDef.id === 'openapi_custom' ? 'custom' : typeDef.id === 'github_repo' ? 'github' : 'custom',
          config,
          credentials: credValues,
        },
      })
      await connectConnector.mutateAsync(connector.name)
      toast({ title: 'Connected', variant: 'success' })
      handleClose()
    } catch (err) {
      toast({ title: 'Failed', description: err instanceof Error ? err.message : 'Unknown error', variant: 'error' })
    } finally {
      setIsSubmitting(false)
    }
  }

  const Icon = typeDef.icon

  return (
    <Dialog open={open} onClose={handleClose} className="max-w-md">
      <DialogHeader title={typeDef.label} onClose={handleClose} />
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label>Connector Name</Label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value.replace(/[^a-z0-9_]/g, '_'))}
            placeholder="my_connector"
            className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring mt-1"
            autoFocus
          />
        </div>

        {typeDef.quickFields.map((f) => (
          <div key={f.key}>
            <Label>{f.label}</Label>
            {f.type === 'select' && f.options ? (
              <select
                value={fieldValues[f.key] ?? ''}
                onChange={(e) => setFieldValues((p) => ({ ...p, [f.key]: e.target.value }))}
                className="flex h-9 w-full appearance-none rounded-md border border-input bg-transparent px-3 py-1 pr-8 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring mt-1"
              >
                {f.options.map((o) => <option key={o} value={o}>{o}</option>)}
              </select>
            ) : (
              <input
                type={f.type}
                value={fieldValues[f.key] ?? ''}
                onChange={(e) => setFieldValues((p) => ({ ...p, [f.key]: e.target.value }))}
                placeholder={f.placeholder}
                required={f.required}
                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring mt-1"
              />
            )}
          </div>
        ))}

        {typeDef.quickCreds.map((f) => (
          <div key={f.key}>
            <Label>{f.label}</Label>
            <input
              type="password"
              value={credValues[f.key] ?? ''}
              onChange={(e) => setCredValues((p) => ({ ...p, [f.key]: e.target.value }))}
              placeholder={f.placeholder}
              className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring mt-1"
            />
          </div>
        ))}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={handleClose}>Cancel</Button>
          <Button type="submit" disabled={isSubmitting}>
            <Power className="h-3.5 w-3.5 mr-1" />
            {isSubmitting ? 'Creating...' : 'Create & Connect'}
          </Button>
        </div>
      </form>
    </Dialog>
  )
}
