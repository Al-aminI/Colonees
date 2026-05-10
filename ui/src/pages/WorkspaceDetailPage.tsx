import { useState, useRef, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogHeader } from '@/components/ui/dialog'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import {
  ArrowLeft, Play, Pencil, Trash2, Plus, Bot, Plug, Database,
  Upload, FileText, Search, X, Power, RefreshCw, Wrench,
  ChevronDown, ChevronRight, Globe, GitBranch, MessageSquare,
  Send, Mail, HardDrive, Cloud, BookOpen, ListChecks, LayoutList,
  Webhook, Copy, Download, Upload as UploadIcon, Code, ExternalLink,
  type LucideIcon,
} from 'lucide-react'
import {
  useWorkspace,
  useUpdateWorkspace,
  useDeleteWorkspace,
  useToggleWorkspace,
} from '@/hooks/useWorkspaces'
import {
  useConnectors,
  useDeleteConnector,
  useConnectConnector,
  useSyncConnector,
  useConnectorCatalog,
  useConnectorCatalogCategories,
  useCreateFromCatalog,
  useCreateConnector,
} from '@/hooks/useConnectors'
import {
  useKnowledgeBases,
  useKnowledgeBase,
  useKBFiles,
  useCreateKnowledgeBase,
  useDeleteKnowledgeBase,
  useUploadFile,
  useDeleteKBFile,
  useSearchKB,
} from '@/hooks/useKnowledgeBases'
import { useToast } from '@/components/ui/toast'
import { cn } from '@/lib/utils'
import type {
  ConnectorDefinition,
  ConnectorCatalogEntry,
  KnowledgeBaseDefinition,
  KBSearchResult,
  CreateConnectorPayload,
} from '@/types'

/* ── Connector helpers ────────────────────────────────────────────────── */

const iconMap: Record<string, LucideIcon> = {
  globe: Globe,
  github: GitBranch,
  gitlab: GitBranch,
  'message-square': MessageSquare,
  send: Send,
  mail: Mail,
  'file-text': FileText,
  'hard-drive': HardDrive,
  database: Database,
  cloud: Cloud,
  'book-open': BookOpen,
  'list-checks': ListChecks,
  kanban: LayoutList,
  webhook: Webhook,
  plug: Plug,
}

function getCatalogIcon(icon: string): LucideIcon {
  return iconMap[icon] ?? Plug
}

const statusConfig: Record<string, { dotClass: string; label: string; variant: 'success' | 'secondary' | 'destructive' | 'warning' }> = {
  connected:    { dotClass: 'bg-green-400',                label: 'Connected',     variant: 'success' },
  disconnected: { dotClass: 'bg-zinc-400',                 label: 'Not connected', variant: 'secondary' },
  error:        { dotClass: 'bg-red-400',                  label: 'Error',         variant: 'destructive' },
  syncing:      { dotClass: 'bg-yellow-400 animate-pulse', label: 'Syncing...',    variant: 'warning' },
}

const typeColors: Record<string, string> = {
  openapi:       'bg-cyan-500/20 text-cyan-400',
  repo:          'bg-violet-500/20 text-violet-400',
  database:      'bg-amber-500/20 text-amber-400',
  webhook:       'bg-pink-500/20 text-pink-400',
  oauth_service: 'bg-emerald-500/20 text-emerald-400',
}

/* ── Main Page ────────────────────────────────────────────────────────── */

export function WorkspaceDetailPage() {
  const { name } = useParams<{ name: string }>()
  const navigate = useNavigate()
  const { data: workspace, isLoading } = useWorkspace(name ?? '')
  const deleteWorkspace = useDeleteWorkspace()
  const toggleWorkspace = useToggleWorkspace()
  const { toast } = useToast()

  const [tab, setTab] = useState('overview')

  if (isLoading) {
    return (
      <div>
        <div className="flex items-center gap-3 mb-6">
          <Skeleton className="h-8 w-8" />
          <Skeleton className="h-8 w-64" />
        </div>
        <Skeleton className="h-[400px]" />
      </div>
    )
  }

  if (!workspace) {
    return (
      <div>
        <PageHeader title="Workspace Not Found" />
        <p className="text-sm text-muted-foreground">
          The workspace "{name}" does not exist.
        </p>
        <Button variant="outline" className="mt-4" onClick={() => navigate('/workspaces')}>
          <ArrowLeft className="h-4 w-4 mr-2" /> Back to Workspaces
        </Button>
      </div>
    )
  }

  const handleDelete = async () => {
    if (!confirm(`Delete workspace "${workspace.display_name}"? This cannot be undone.`)) return
    await deleteWorkspace.mutateAsync(workspace.name)
    toast({ title: 'Workspace deleted', variant: 'info' })
    navigate('/workspaces')
  }

  const handleToggle = async (enabled: boolean) => {
    await toggleWorkspace.mutateAsync({ name: workspace.name, enabled })
  }

  const borderColor = workspace.color || '#6366f1'

  return (
    <div>
      {/* Header */}
      <div className="flex items-center gap-3 mb-1">
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => navigate('/workspaces')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex items-center gap-2 min-w-0 flex-1">
          {workspace.icon && <span className="text-xl">{workspace.icon}</span>}
          <div className="min-w-0">
            <h1 className="text-xl font-bold truncate">{workspace.display_name}</h1>
            <p className="text-xs text-muted-foreground font-mono">{workspace.name}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Switch
            checked={workspace.enabled}
            onCheckedChange={handleToggle}
            disabled={toggleWorkspace.isPending}
          />
          <span className="text-xs text-muted-foreground">
            {workspace.enabled ? 'Enabled' : 'Disabled'}
          </span>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={tab} onValueChange={setTab} className="mt-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="connectors">
            Connectors
          </TabsTrigger>
          <TabsTrigger value="knowledge-bases">
            Knowledge Bases
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <OverviewTab workspace={workspace} onDelete={handleDelete} />
        </TabsContent>
        <TabsContent value="connectors">
          <ConnectorsTab workspace={workspace} />
        </TabsContent>
        <TabsContent value="knowledge-bases">
          <KnowledgeBasesTab workspace={workspace} />
        </TabsContent>
      </Tabs>
    </div>
  )
}

/* ── Tab 1: Overview ──────────────────────────────────────────────────── */

function OverviewTab({
  workspace,
  onDelete,
}: {
  workspace: import('@/types').WorkspaceDefinition
  onDelete: () => void
}) {
  const navigate = useNavigate()
  const updateWorkspace = useUpdateWorkspace()
  const { toast } = useToast()
  const [showEdit, setShowEdit] = useState(false)

  const [editDisplayName, setEditDisplayName] = useState(workspace.display_name)
  const [editDescription, setEditDescription] = useState(workspace.description)
  const [editIcon, setEditIcon] = useState(workspace.icon)
  const [editColor, setEditColor] = useState(workspace.color)

  const handleSaveEdit = async () => {
    await updateWorkspace.mutateAsync({
      name: workspace.name,
      payload: {
        display_name: editDisplayName,
        description: editDescription,
        icon: editIcon || undefined,
        color: editColor || undefined,
      },
    })
    toast({ title: 'Workspace updated', variant: 'success' })
    setShowEdit(false)
  }

  const borderColor = workspace.color || '#6366f1'

  return (
    <div className="mt-4 space-y-6">
      <Card style={{ borderLeftWidth: 4, borderLeftColor: borderColor }}>
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-muted-foreground">{workspace.description}</p>
              <div className="flex flex-wrap gap-2 mt-4">
                <Badge variant="secondary">
                  <Bot className="h-3 w-3 mr-1" />
                  {workspace.colonees.length} colonee{workspace.colonees.length !== 1 ? 's' : ''}
                </Badge>
                <Badge variant="secondary">
                  <Database className="h-3 w-3 mr-1" />
                  {workspace.knowledge_bases.length} knowledge base{workspace.knowledge_bases.length !== 1 ? 's' : ''}
                </Badge>
                <Badge variant={workspace.enabled ? 'success' : 'secondary'}>
                  {workspace.enabled ? 'Enabled' : 'Disabled'}
                </Badge>
              </div>
              {/* Agent */}
              {workspace.colonees.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-sm font-semibold mb-2">Specialist Agent</h3>
                  <Badge variant="info">{workspace.colonees[0]}</Badge>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex gap-3">
        <Button onClick={() => navigate(`/playground`)}>
          <Play className="h-4 w-4 mr-2" /> Use in Playground
        </Button>
        <Button variant="outline" onClick={() => {
          setEditDisplayName(workspace.display_name)
          setEditDescription(workspace.description)
          setEditIcon(workspace.icon)
          setEditColor(workspace.color)
          setShowEdit(true)
        }}>
          <Pencil className="h-4 w-4 mr-2" /> Edit Workspace
        </Button>
        <Button variant="destructive" onClick={onDelete}>
          <Trash2 className="h-4 w-4 mr-2" /> Delete
        </Button>
      </div>

      {/* API Endpoint */}
      <Card className="border-blue-500/30 bg-blue-500/5">
        <CardContent className="p-5 space-y-3">
          <div className="flex items-center gap-2">
            <Code className="h-4 w-4 text-blue-400" />
            <h3 className="text-sm font-semibold">Workspace API Endpoint</h3>
          </div>
          <p className="text-xs text-muted-foreground">
            Invoke this workspace from any external application. The workspace acts as a
            standalone agent API — POST a goal and get results.
          </p>
          <div className="rounded-md bg-background border border-border p-3 font-mono text-xs">
            <div className="flex items-center justify-between mb-1">
              <span className="text-muted-foreground">POST</span>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={() => {
                  navigator.clipboard.writeText(
                    `curl -X POST "${window.location.origin}/api/workspaces/${workspace.name}/invoke" \\\n  -H "Content-Type: application/json" \\\n  -H "X-API-Key: your-api-key" \\\n  -d '{"goal": "Your task here"}'`
                  )
                  toast({ title: 'Copied', variant: 'success' })
                }}
              >
                <Copy className="h-3 w-3" />
              </Button>
            </div>
            <code className="text-blue-400">
              /workspaces/{workspace.name}/invoke
            </code>
          </div>
          <p className="text-[11px] text-muted-foreground">
            Set <code className="rounded bg-muted px-1">COLONEES_API_KEY</code> in your environment
            and pass it as <code className="rounded bg-muted px-1">X-API-Key</code> header or
            <code className="rounded bg-muted px-1"> Bearer</code> token.
          </p>
        </CardContent>
      </Card>

      {/* Export / Import */}
      <div className="flex gap-3">
        <Button variant="outline" size="sm" onClick={async () => {
          try {
            const { workspacesApi } = await import('@/api/workspaces')
            const data = await workspacesApi.export(workspace.name)
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url; a.download = `${workspace.name}.colonees.json`; a.click()
            URL.revokeObjectURL(url)
            toast({ title: 'Workspace exported', variant: 'success' })
          } catch (err) {
            toast({ title: 'Export failed', description: err instanceof Error ? err.message : 'Unknown error', variant: 'error' })
          }
        }}>
          <Download className="h-3.5 w-3.5 mr-1" /> Export
        </Button>
        <Button variant="outline" size="sm" onClick={() => {
          const input = document.createElement('input')
          input.type = 'file'; input.accept = '.json'
          input.onchange = async (e) => {
            const file = (e.target as HTMLInputElement).files?.[0]
            if (!file) return
            try {
              const text = await file.text()
              const data = JSON.parse(text)
              const { workspacesApi } = await import('@/api/workspaces')
              await workspacesApi.import(data)
              toast({ title: 'Workspace imported', variant: 'success' })
              window.location.reload()
            } catch (err) {
              toast({ title: 'Import failed', description: err instanceof Error ? err.message : 'Invalid file', variant: 'error' })
            }
          }
          input.click()
        }}>
          <UploadIcon className="h-3.5 w-3.5 mr-1" /> Import
        </Button>
      </div>

      {/* Edit Dialog */}
      <Dialog open={showEdit} onClose={() => setShowEdit(false)}>
        <DialogHeader title="Edit Workspace" onClose={() => setShowEdit(false)} />
        <div className="space-y-4">
          <div>
            <Label>Display Name</Label>
            <Input
              value={editDisplayName}
              onChange={(e) => setEditDisplayName(e.target.value)}
              className="mt-1"
            />
          </div>
          <div>
            <Label>Description</Label>
            <Textarea
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
              className="mt-1"
              rows={3}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Icon (emoji)</Label>
              <Input
                value={editIcon}
                onChange={(e) => setEditIcon(e.target.value)}
                placeholder="e.g. :rocket:"
                className="mt-1"
              />
            </div>
            <div>
              <Label>Color (hex)</Label>
              <Input
                value={editColor}
                onChange={(e) => setEditColor(e.target.value)}
                placeholder="#6366f1"
                className="mt-1"
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setShowEdit(false)}>Cancel</Button>
            <Button onClick={handleSaveEdit} disabled={updateWorkspace.isPending}>
              {updateWorkspace.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  )
}

/* ── Tab 2: Connectors ────────────────────────────────────────────────── */

function ConnectorsTab({
  workspace,
}: {
  workspace: import('@/types').WorkspaceDefinition
}) {
  const { data: connectorData, isLoading } = useConnectors()
  const deleteConnector = useDeleteConnector()
  const connectConnector = useConnectConnector()
  const syncConnector = useSyncConnector()
  const updateWorkspace = useUpdateWorkspace()
  const { toast } = useToast()

  const [showCatalog, setShowCatalog] = useState(false)
  const [showCustom, setShowCustom] = useState(false)

  const allConnectors = connectorData?.connectors ?? []
  const workspaceConnectors = allConnectors.filter(c =>
    c.workspaces.includes(workspace.name),
  )

  const handleDelete = async (name: string) => {
    if (!confirm(`Delete connector "${name}"?`)) return
    await deleteConnector.mutateAsync(name)
    toast({ title: 'Connector deleted', variant: 'info' })
  }

  const handleConnect = async (name: string) => {
    try {
      await connectConnector.mutateAsync(name)
      toast({ title: 'Connector activated', variant: 'success' })
    } catch (err) {
      toast({
        title: 'Failed to connect',
        description: err instanceof Error ? err.message : 'Unknown error',
        variant: 'error',
      })
    }
  }

  const handleSync = async (name: string) => {
    try {
      await syncConnector.mutateAsync(name)
      toast({ title: 'Sync started', variant: 'success' })
    } catch (err) {
      toast({
        title: 'Failed to sync',
        description: err instanceof Error ? err.message : 'Unknown error',
        variant: 'error',
      })
    }
  }

  return (
    <div className="mt-4">
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm text-muted-foreground">
          {workspaceConnectors.length} connector{workspaceConnectors.length !== 1 ? 's' : ''} in this workspace
        </span>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => setShowCatalog(true)}>
            <Plus className="h-3.5 w-3.5 mr-1" /> From Catalog
          </Button>
          <Button size="sm" onClick={() => setShowCustom(true)}>
            <Plus className="h-3.5 w-3.5 mr-1" /> Custom
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-52" />)}
        </div>
      ) : workspaceConnectors.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground gap-3">
          <Plug className="h-10 w-10 opacity-20" />
          <p className="text-sm">No connectors in this workspace yet.</p>
          <p className="text-xs">Add one from the catalog or create a custom connector.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {workspaceConnectors.map(c => (
            <ConnectorCardInline
              key={c.name}
              connector={c}
              onDelete={handleDelete}
              onConnect={handleConnect}
              onSync={handleSync}
              isDeleting={deleteConnector.isPending}
            />
          ))}
        </div>
      )}

      {/* Catalog Dialog */}
      {showCatalog && (
        <CatalogPickerDialog
          open={showCatalog}
          onClose={() => setShowCatalog(false)}
          workspaceName={workspace.name}
        />
      )}

      {/* Custom Connector Dialog */}
      <CustomConnectorDialog
        open={showCustom}
        onClose={() => setShowCustom(false)}
        workspaceName={workspace.name}
      />
    </div>
  )
}

/* ── Inline Connector Card ────────────────────────────────────────────── */

function ConnectorCardInline({
  connector,
  onDelete,
  onConnect,
  onSync,
  isDeleting,
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
  const ProviderIcon = getCatalogIcon(connector.provider)

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
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 text-destructive hover:text-destructive shrink-0"
            onClick={() => onDelete(connector.name)}
            disabled={isDeleting}
          >
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
          <p className="text-xs text-destructive bg-destructive/10 rounded px-2 py-1">
            {connector.status_message}
          </p>
        )}

        {connector.description && (
          <p className="text-xs text-muted-foreground line-clamp-2">{connector.description}</p>
        )}

        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Wrench className="h-3.5 w-3.5" />
          <span>{connector.tools_generated.length} tool{connector.tools_generated.length !== 1 ? 's' : ''} generated</span>
        </div>

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
            <button
              onClick={() => setExpanded(!expanded)}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
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

/* ── Catalog Picker Dialog ────────────────────────────────────────────── */

interface SchemaField {
  key: string
  type: string
  label: string
  description?: string
  required?: boolean
  default?: string
  options?: string[]
}

function parseSchemaFields(schema: Record<string, any>): SchemaField[] {
  if (!schema || typeof schema !== 'object') return []
  const properties = schema.properties ?? schema
  const required: string[] = schema.required ?? []
  return Object.entries(properties).map(([key, def]: [string, any]) => ({
    key,
    type: def.type ?? 'string',
    label: def.title ?? def.label ?? key,
    description: def.description,
    required: required.includes(key) || def.required === true,
    default: def.default ?? '',
    options: def.enum ?? def.options,
  }))
}

function CatalogPickerDialog({
  open,
  onClose,
  workspaceName,
}: {
  open: boolean
  onClose: () => void
  workspaceName: string
}) {
  const { data: catalogData, isLoading } = useConnectorCatalog()
  const createFromCatalog = useCreateFromCatalog()
  const connectConnector = useConnectConnector()
  const { toast } = useToast()

  const [selectedEntry, setSelectedEntry] = useState<ConnectorCatalogEntry | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formValues, setFormValues] = useState<Record<string, string>>({})

  const catalog = catalogData?.catalog ?? []

  const handleSelectEntry = (entry: ConnectorCatalogEntry) => {
    setSelectedEntry(entry)
    // Build initial values from defaults
    const vals: Record<string, string> = {}
    const configFields = parseSchemaFields(entry.config_schema)
    const credFields = parseSchemaFields(entry.credential_schema)
    ;[...configFields, ...credFields].forEach((f) => {
      if (f.default) vals[f.key] = String(f.default)
    })
    setFormValues(vals)
  }

  const handleSubmitCatalog = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedEntry) return
    setIsSubmitting(true)
    try {
      const configFields = parseSchemaFields(selectedEntry.config_schema)
      const credFields = parseSchemaFields(selectedEntry.credential_schema)
      const configVals: Record<string, string> = {}
      const credVals: Record<string, string> = {}
      configFields.forEach((f) => { if (formValues[f.key]) configVals[f.key] = formValues[f.key] })
      credFields.forEach((f) => { if (formValues[f.key]) credVals[f.key] = formValues[f.key] })

      const connectorName = formValues['_name'] || selectedEntry.id.replace(/[^a-z0-9_]/g, '_')

      const connector = await createFromCatalog.mutateAsync({
        catalogId: selectedEntry.id,
        payload: {
          name: connectorName,
          display_name: selectedEntry.display_name,
          description: selectedEntry.description,
          type: selectedEntry.type,
          provider: selectedEntry.provider,
          config: configVals,
          credentials: credVals,
          workspaces: [workspaceName],
        },
      })

      await connectConnector.mutateAsync(connector.name)
      toast({ title: `${selectedEntry.display_name} connected`, variant: 'success' })
      setSelectedEntry(null)
      onClose()
    } catch (err) {
      toast({
        title: 'Failed to create connector',
        description: err instanceof Error ? err.message : 'Unknown error',
        variant: 'error',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  // If an entry is selected, show form
  if (selectedEntry) {
    const configFields = parseSchemaFields(selectedEntry.config_schema).filter(f => f.type !== 'hidden')
    const credFields = parseSchemaFields(selectedEntry.credential_schema).filter(f => f.type !== 'hidden')
    const Icon = getCatalogIcon(selectedEntry.icon)

    return (
      <Dialog open={open} onClose={() => { setSelectedEntry(null); onClose() }} className="max-w-lg">
        <DialogHeader
          title={`Add ${selectedEntry.display_name}`}
          onClose={() => { setSelectedEntry(null); onClose() }}
        />
        <div className="flex items-center gap-3 mb-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent">
            <Icon className="h-5 w-5 text-foreground" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">{selectedEntry.description}</p>
            <div className="flex gap-2 mt-1">
              <Badge variant="outline" className="text-[10px]">{selectedEntry.category}</Badge>
              <Badge variant="outline" className="text-[10px]">{selectedEntry.type}</Badge>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmitCatalog} className="space-y-4">
          <div>
            <Label>Connector Name</Label>
            <Input
              value={formValues['_name'] ?? selectedEntry.id}
              onChange={(e) => setFormValues(prev => ({ ...prev, _name: e.target.value.replace(/[^a-z0-9_]/g, '_') }))}
              placeholder={selectedEntry.id}
              className="mt-1"
            />
          </div>

          {configFields.length > 0 && (
            <div className="space-y-3">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Configuration</p>
              {configFields.map((field) => (
                <div key={field.key}>
                  <Label>
                    {field.label}
                    {field.required && <span className="text-destructive ml-0.5">*</span>}
                  </Label>
                  <Input
                    type={field.type === 'password' ? 'password' : 'text'}
                    value={formValues[field.key] ?? ''}
                    onChange={(e) => setFormValues(prev => ({ ...prev, [field.key]: e.target.value }))}
                    placeholder={field.description ?? field.label}
                    required={field.required}
                    className="mt-1"
                  />
                </div>
              ))}
            </div>
          )}

          {credFields.length > 0 && (
            <div className="space-y-3">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Credentials</p>
              {credFields.map((field) => (
                <div key={field.key}>
                  <Label>
                    {field.label}
                    {field.required && <span className="text-destructive ml-0.5">*</span>}
                  </Label>
                  <Input
                    type={field.type === 'password' ? 'password' : 'text'}
                    value={formValues[field.key] ?? ''}
                    onChange={(e) => setFormValues(prev => ({ ...prev, [field.key]: e.target.value }))}
                    placeholder={field.description ?? field.label}
                    required={field.required}
                    className="mt-1"
                  />
                </div>
              ))}
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setSelectedEntry(null)}>Back</Button>
            <Button type="submit" disabled={isSubmitting}>
              <Power className="h-3.5 w-3.5 mr-1" />
              {isSubmitting ? 'Creating...' : 'Create & Connect'}
            </Button>
          </div>
        </form>
      </Dialog>
    )
  }

  return (
    <Dialog open={open} onClose={onClose} className="max-w-2xl">
      <DialogHeader title="Add Connector from Catalog" onClose={onClose} />

      {isLoading ? (
        <div className="grid grid-cols-2 gap-3">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-32" />)}
        </div>
      ) : catalog.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground gap-3">
          <Plug className="h-10 w-10 opacity-20" />
          <p className="text-sm">No connectors available in catalog.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3 max-h-[60vh] overflow-y-auto">
          {catalog.map((entry) => {
            const Icon = getCatalogIcon(entry.icon)
            const typeColor = typeColors[entry.type] ?? 'bg-zinc-500/20 text-zinc-400'
            return (
              <Card
                key={entry.id}
                className="cursor-pointer hover:border-primary/40 transition-colors"
                onClick={() => handleSelectEntry(entry)}
              >
                <CardContent className="p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-md bg-accent">
                      <Icon className="h-4 w-4 text-foreground" />
                    </div>
                    <span className="font-semibold text-sm truncate">{entry.display_name}</span>
                  </div>
                  <p className="text-xs text-muted-foreground line-clamp-2 mb-2">{entry.description}</p>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-[10px]">{entry.category}</Badge>
                    <span className={cn('inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium', typeColor)}>
                      {entry.type}
                    </span>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </Dialog>
  )
}

/* ── Custom Connector Dialog ──────────────────────────────────────────── */

function CustomConnectorDialog({
  open,
  onClose,
  workspaceName,
}: {
  open: boolean
  onClose: () => void
  workspaceName: string
}) {
  const createConnector = useCreateConnector()
  const connectConnector = useConnectConnector()
  const { toast } = useToast()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const [name, setName] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [description, setDescription] = useState('')
  const [type, setType] = useState('openapi')
  const [provider, setProvider] = useState('custom')

  const handleClose = () => {
    setName('')
    setDisplayName('')
    setDescription('')
    setType('openapi')
    setProvider('custom')
    onClose()
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    try {
      const connector = await createConnector.mutateAsync({
        name,
        display_name: displayName,
        description,
        type,
        provider,
        workspaces: [workspaceName],
      })
      toast({ title: 'Connector created', variant: 'success' })
      handleClose()
    } catch (err) {
      toast({
        title: 'Failed to create connector',
        description: err instanceof Error ? err.message : 'Unknown error',
        variant: 'error',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onClose={handleClose}>
      <DialogHeader title="Create Custom Connector" onClose={handleClose} />
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label>Name (slug)</Label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value.replace(/[^a-z0-9_]/g, '_'))}
            placeholder="my_connector"
            className="mt-1"
            required
          />
        </div>
        <div>
          <Label>Display Name</Label>
          <Input
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="My Connector"
            className="mt-1"
            required
          />
        </div>
        <div>
          <Label>Description</Label>
          <Textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What does this connector do?"
            className="mt-1"
            rows={2}
            required
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Label>Type</Label>
            <Select value={type} onChange={(e) => setType(e.target.value)} className="mt-1 w-full">
              <option value="openapi">OpenAPI</option>
              <option value="repo">Repository</option>
              <option value="database">Database</option>
              <option value="webhook">Webhook</option>
              <option value="oauth_service">OAuth Service</option>
            </Select>
          </div>
          <div>
            <Label>Provider</Label>
            <Input
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              placeholder="custom"
              className="mt-1"
            />
          </div>
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={handleClose}>Cancel</Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Creating...' : 'Create Connector'}
          </Button>
        </div>
      </form>
    </Dialog>
  )
}

/* ── Tab 4: Knowledge Bases ───────────────────────────────────────────── */

function KnowledgeBasesTab({
  workspace,
}: {
  workspace: import('@/types').WorkspaceDefinition
}) {
  const { data: kbData, isLoading } = useKnowledgeBases()
  const createKB = useCreateKnowledgeBase()
  const deleteKB = useDeleteKnowledgeBase()
  const updateWorkspace = useUpdateWorkspace()
  const { toast } = useToast()

  const [showCreate, setShowCreate] = useState(false)
  const [expandedKB, setExpandedKB] = useState<string | null>(null)
  const [showAddExisting, setShowAddExisting] = useState(false)

  const allKBs = kbData?.knowledge_bases ?? []
  const workspaceKBs = allKBs.filter(kb =>
    workspace.knowledge_bases.includes(kb.name) || kb.workspaces.includes(workspace.name),
  )
  const availableKBs = allKBs.filter(kb =>
    !workspace.knowledge_bases.includes(kb.name) && !kb.workspaces.includes(workspace.name),
  )

  const handleCreate = async (values: { name: string; display_name: string; description: string; type: string }) => {
    await createKB.mutateAsync({
      name: values.name,
      display_name: values.display_name,
      description: values.description,
      type: values.type as 'files' | 'database' | 'api',
      workspaces: [workspace.name],
    })
    // Also add to workspace list
    await updateWorkspace.mutateAsync({
      name: workspace.name,
      payload: { knowledge_bases: [...workspace.knowledge_bases, values.name] },
    })
    toast({ title: 'Knowledge base created', variant: 'success' })
  }

  const handleDelete = async (kbName: string) => {
    if (!confirm(`Delete knowledge base "${kbName}"?`)) return
    await deleteKB.mutateAsync(kbName)
    await updateWorkspace.mutateAsync({
      name: workspace.name,
      payload: { knowledge_bases: workspace.knowledge_bases.filter(n => n !== kbName) },
    })
    if (expandedKB === kbName) setExpandedKB(null)
    toast({ title: 'Knowledge base deleted', variant: 'info' })
  }

  const handleAddToWorkspace = async (kbName: string) => {
    await updateWorkspace.mutateAsync({
      name: workspace.name,
      payload: { knowledge_bases: [...workspace.knowledge_bases, kbName] },
    })
    toast({ title: 'Knowledge base added to workspace', variant: 'success' })
  }

  const handleRemoveFromWorkspace = async (kbName: string) => {
    await updateWorkspace.mutateAsync({
      name: workspace.name,
      payload: { knowledge_bases: workspace.knowledge_bases.filter(n => n !== kbName) },
    })
    toast({ title: 'Knowledge base removed from workspace', variant: 'info' })
  }

  return (
    <div className="mt-4">
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm text-muted-foreground">
          {workspaceKBs.length} knowledge base{workspaceKBs.length !== 1 ? 's' : ''} in this workspace
        </span>
        <div className="flex gap-2">
          {availableKBs.length > 0 && (
            <Button variant="outline" size="sm" onClick={() => setShowAddExisting(true)}>
              <Plus className="h-3.5 w-3.5 mr-1" /> Add Existing
            </Button>
          )}
          <Button size="sm" onClick={() => setShowCreate(true)}>
            <Plus className="h-3.5 w-3.5 mr-1" /> New Knowledge Base
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-32" />)}
        </div>
      ) : workspaceKBs.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground gap-3">
          <Database className="h-10 w-10 opacity-20" />
          <p className="text-sm">No knowledge bases in this workspace yet.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {workspaceKBs.map(kb => (
            <div key={kb.name}>
              <Card
                className={cn(
                  'cursor-pointer transition-colors',
                  expandedKB === kb.name ? 'border-primary/40' : 'hover:border-primary/20',
                )}
                onClick={() => setExpandedKB(expandedKB === kb.name ? null : kb.name)}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 min-w-0">
                      <Database className="h-4 w-4 text-muted-foreground shrink-0" />
                      <div className="min-w-0">
                        <p className="font-semibold truncate">{kb.display_name}</p>
                        <p className="text-xs text-muted-foreground font-mono">{kb.name}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                      <Badge variant="info" className="text-[10px]">{kb.type}</Badge>
                      <Badge variant="secondary" className="text-[10px]">
                        {kb.stats.total_files} file{kb.stats.total_files !== 1 ? 's' : ''}
                      </Badge>
                      <Badge variant="secondary" className="text-[10px]">
                        {(kb.stats.total_size_bytes / 1024).toFixed(1)} KB
                      </Badge>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={() => handleRemoveFromWorkspace(kb.name)}
                        title="Remove from workspace"
                      >
                        <X className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-destructive hover:text-destructive"
                        onClick={() => handleDelete(kb.name)}
                        title="Delete knowledge base"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1 line-clamp-1">{kb.description}</p>
                </CardContent>
              </Card>

              {/* Expanded KB Detail */}
              {expandedKB === kb.name && (
                <Card className="mt-1 border-t-0 rounded-t-none">
                  <KBExpandedPanel kbName={kb.name} />
                </Card>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Create KB Dialog */}
      <CreateKBDialog
        open={showCreate}
        onClose={() => setShowCreate(false)}
        onCreate={handleCreate}
      />

      {/* Add Existing KB Dialog */}
      <Dialog open={showAddExisting} onClose={() => setShowAddExisting(false)}>
        <DialogHeader title="Add Existing Knowledge Base" onClose={() => setShowAddExisting(false)} />
        <div className="space-y-2 max-h-[50vh] overflow-y-auto">
          {availableKBs.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">
              All knowledge bases are already in this workspace.
            </p>
          ) : (
            availableKBs.map(kb => (
              <div
                key={kb.name}
                className="flex items-center justify-between rounded-md border px-3 py-2"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate">{kb.display_name}</p>
                  <p className="text-xs text-muted-foreground">
                    {kb.type} - {kb.stats.total_files} file{kb.stats.total_files !== 1 ? 's' : ''}
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    handleAddToWorkspace(kb.name)
                    setShowAddExisting(false)
                  }}
                >
                  <Plus className="h-3.5 w-3.5 mr-1" /> Add
                </Button>
              </div>
            ))
          )}
        </div>
      </Dialog>
    </div>
  )
}

/* ── KB Expanded Panel (files, upload, search) ────────────────────────── */

function KBExpandedPanel({ kbName }: { kbName: string }) {
  const { data: kb } = useKnowledgeBase(kbName)
  const { data: filesData, isLoading: filesLoading } = useKBFiles(kbName)
  const uploadFile = useUploadFile()
  const deleteFile = useDeleteKBFile()
  const searchKB = useSearchKB()
  const { toast } = useToast()

  const fileInputRef = useRef<HTMLInputElement>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<KBSearchResult[]>([])
  const [isDragging, setIsDragging] = useState(false)

  const files = filesData?.files ?? []

  const handleUpload = useCallback(
    async (fileList: FileList | null) => {
      if (!fileList) return
      for (let i = 0; i < fileList.length; i++) {
        try {
          await uploadFile.mutateAsync({ kbName, file: fileList[i] })
          toast({ title: `Uploaded ${fileList[i].name}`, variant: 'success' })
        } catch (err) {
          toast({
            title: `Failed to upload ${fileList[i].name}`,
            description: err instanceof Error ? err.message : 'Unknown error',
            variant: 'error',
          })
        }
      }
    },
    [kbName, uploadFile, toast],
  )

  const handleDeleteFile = async (filename: string) => {
    if (!confirm(`Delete file "${filename}"?`)) return
    await deleteFile.mutateAsync({ kbName, filename })
    toast({ title: 'File deleted', variant: 'info' })
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    const result = await searchKB.mutateAsync({ name: kbName, query: searchQuery })
    setSearchResults(result.results)
  }

  return (
    <CardContent className="p-4 space-y-4" onClick={(e) => e.stopPropagation()}>
      {/* File Upload */}
      <div>
        <h4 className="text-xs font-semibold mb-2 text-muted-foreground uppercase tracking-wide">Files</h4>
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) => handleUpload(e.target.files)}
          className="hidden"
          multiple
        />
        <div
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(e) => { e.preventDefault(); setIsDragging(false); handleUpload(e.dataTransfer.files) }}
          className={cn(
            'border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors',
            isDragging ? 'border-primary bg-primary/5' : 'border-border hover:border-muted-foreground',
          )}
        >
          <Upload className="h-6 w-6 mx-auto mb-1 text-muted-foreground" />
          <p className="text-xs text-muted-foreground">Drop files here or click to upload</p>
          {uploadFile.isPending && <p className="text-xs text-primary mt-1">Uploading...</p>}
        </div>

        {filesLoading ? (
          <Skeleton className="h-20 mt-2" />
        ) : files.length === 0 ? (
          <p className="text-xs text-muted-foreground mt-2">No files uploaded yet.</p>
        ) : (
          <div className="space-y-1 mt-2">
            {files.map((f) => (
              <div key={f.name} className="flex items-center gap-3 rounded-md px-3 py-1.5 text-sm hover:bg-accent">
                <FileText className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                <span className="flex-1 truncate text-xs">{f.name}</span>
                <span className="text-[10px] text-muted-foreground shrink-0">{(f.size / 1024).toFixed(1)} KB</span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 shrink-0 text-destructive hover:text-destructive"
                  onClick={() => handleDeleteFile(f.name)}
                  disabled={deleteFile.isPending}
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>

      <Separator />

      {/* Search */}
      <div>
        <h4 className="text-xs font-semibold mb-2 text-muted-foreground uppercase tracking-wide">Search</h4>
        <div className="flex gap-2">
          <Input
            placeholder="Search knowledge base..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="flex-1 h-8 text-xs"
          />
          <Button size="sm" onClick={handleSearch} disabled={searchKB.isPending || !searchQuery.trim()}>
            <Search className="h-3.5 w-3.5 mr-1" />
            {searchKB.isPending ? '...' : 'Search'}
          </Button>
        </div>

        {searchResults.length > 0 && (
          <div className="space-y-2 mt-3">
            {searchResults.map((result, i) => (
              <div key={i} className="rounded-md border p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] text-muted-foreground font-mono truncate">{result.source}</span>
                  <Badge variant="outline" className="text-[10px] shrink-0">
                    {(result.score * 100).toFixed(0)}% match
                  </Badge>
                </div>
                <p className="text-xs whitespace-pre-wrap">{result.content}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </CardContent>
  )
}

/* ── Create KB Dialog (simplified) ────────────────────────────────────── */

function CreateKBDialog({
  open,
  onClose,
  onCreate,
}: {
  open: boolean
  onClose: () => void
  onCreate: (values: { name: string; display_name: string; description: string; type: string }) => Promise<void>
}) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [name, setName] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [description, setDescription] = useState('')
  const [type, setType] = useState('files')

  const handleClose = () => {
    setName('')
    setDisplayName('')
    setDescription('')
    setType('files')
    onClose()
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    try {
      await onCreate({ name, display_name: displayName, description, type })
      handleClose()
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onClose={handleClose}>
      <DialogHeader title="Create Knowledge Base" onClose={handleClose} />
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label>Name (slug)</Label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value.replace(/[^a-z0-9_-]/g, ''))}
            placeholder="my-knowledge-base"
            className="mt-1"
            required
          />
        </div>
        <div>
          <Label>Display Name</Label>
          <Input
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="My Knowledge Base"
            className="mt-1"
            required
          />
        </div>
        <div>
          <Label>Description</Label>
          <Textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What kind of knowledge does this contain?"
            className="mt-1"
            rows={2}
            required
          />
        </div>
        <div>
          <Label>Type</Label>
          <Select value={type} onChange={(e) => setType(e.target.value)} className="mt-1 w-full">
            <option value="files">Files</option>
            <option value="database">Database</option>
            <option value="api">API</option>
          </Select>
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={handleClose}>Cancel</Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Creating...' : 'Create Knowledge Base'}
          </Button>
        </div>
      </form>
    </Dialog>
  )
}
