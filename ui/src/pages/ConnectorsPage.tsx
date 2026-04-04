import { useState } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogHeader } from '@/components/ui/dialog'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import {
  Plug,
  Plus,
  Trash2,
  RefreshCw,
  Power,
  ChevronDown,
  ChevronRight,
  Wrench,
  Globe,
  GitBranch,
  MessageSquare,
  Send,
  Mail,
  FileText,
  HardDrive,
  Database,
  Cloud,
  BookOpen,
  ListChecks,
  LayoutList,
  Webhook,
  type LucideIcon,
} from 'lucide-react'
import {
  useConnectors,
  useDeleteConnector,
  useConnectConnector,
  useSyncConnector,
  useConnectorTools,
  useConnectorCatalog,
  useConnectorCatalogCategories,
  useCreateFromCatalog,
} from '@/hooks/useConnectors'
import { connectorsApi } from '@/api/connectors'
import { useToast } from '@/components/ui/toast'
import { cn } from '@/lib/utils'
import type { ConnectorDefinition, ConnectorCatalogEntry } from '@/types'

/* ── Icon map for catalog entries ──────────────────────────────────────── */

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

/* ── Status config ─────────────────────────────────────────────────────── */

const statusConfig: Record<string, { dotClass: string; label: string; variant: 'success' | 'secondary' | 'destructive' | 'warning' }> = {
  connected:    { dotClass: 'bg-green-400',                              label: 'Connected',     variant: 'success' },
  disconnected: { dotClass: 'bg-zinc-400',                               label: 'Not connected', variant: 'secondary' },
  error:        { dotClass: 'bg-red-400',                                label: 'Error',         variant: 'destructive' },
  syncing:      { dotClass: 'bg-yellow-400 animate-pulse',               label: 'Syncing...',    variant: 'warning' },
}

/* ── Type badge colors ─────────────────────────────────────────────────── */

const typeColors: Record<string, string> = {
  openapi:       'bg-cyan-500/20 text-cyan-400',
  repo:          'bg-violet-500/20 text-violet-400',
  database:      'bg-amber-500/20 text-amber-400',
  webhook:       'bg-pink-500/20 text-pink-400',
  oauth_service: 'bg-emerald-500/20 text-emerald-400',
}

/* ── Main page ─────────────────────────────────────────────────────────── */

export function ConnectorsPage() {
  const [tab, setTab] = useState('my-connectors')

  return (
    <div>
      <PageHeader
        title="Connectors"
        description="Connect external APIs, repositories, databases, and services to generate tools automatically"
      />

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="my-connectors">My Connectors</TabsTrigger>
          <TabsTrigger value="catalog">Catalog</TabsTrigger>
        </TabsList>

        <TabsContent value="my-connectors">
          <MyConnectorsTab />
        </TabsContent>
        <TabsContent value="catalog">
          <CatalogTab />
        </TabsContent>
      </Tabs>
    </div>
  )
}

/* ── Tab 1: My Connectors ──────────────────────────────────────────────── */

function MyConnectorsTab() {
  const { data, isLoading } = useConnectors()
  const deleteConnector = useDeleteConnector()
  const connectConnector = useConnectConnector()
  const syncConnector = useSyncConnector()
  const { toast } = useToast()

  const connectors = data?.connectors ?? []

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

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 mt-4">
        {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-52" />)}
      </div>
    )
  }

  if (connectors.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-muted-foreground gap-3">
        <Plug className="h-12 w-12 opacity-20" />
        <p className="text-sm">No connectors configured yet.</p>
        <p className="text-xs">Browse the Catalog tab to add your first connector.</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 mt-4">
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
  )
}

/* ── Connector Card ────────────────────────────────────────────────────── */

function ConnectorCard({
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
        {/* Header */}
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
            title="Delete connector"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>

        {/* Status + type */}
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-1.5">
            <span className={cn('h-2 w-2 rounded-full shrink-0', status.dotClass)} />
            <Badge variant={status.variant} className="text-[10px] px-1.5 py-0">
              {status.label}
            </Badge>
          </div>
          <span className={cn('inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium', typeColor)}>
            {connector.type}
          </span>
        </div>

        {/* Error message */}
        {connector.status === 'error' && connector.status_message && (
          <p className="text-xs text-destructive bg-destructive/10 rounded px-2 py-1">
            {connector.status_message}
          </p>
        )}

        {/* Description */}
        {connector.description && (
          <p className="text-xs text-muted-foreground line-clamp-2">{connector.description}</p>
        )}

        {/* Tools count */}
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Wrench className="h-3.5 w-3.5" />
          <span>{connector.tools_generated.length} tool{connector.tools_generated.length !== 1 ? 's' : ''} generated</span>
        </div>

        {/* Workspaces */}
        {connector.workspaces.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {connector.workspaces.map((ws) => (
              <Badge key={ws} variant="secondary" className="text-[10px]">{ws}</Badge>
            ))}
          </div>
        )}

        {/* Last synced */}
        {connector.last_synced_at && (
          <p className="text-[10px] text-muted-foreground">
            Last synced: {new Date(connector.last_synced_at).toLocaleString()}
          </p>
        )}

        {/* Actions */}
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

        {/* Expandable tools list */}
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

/* ── Tab 2: Catalog ────────────────────────────────────────────────────── */

function CatalogTab() {
  const [category, setCategory] = useState('all')
  const { data: catData, isLoading: catLoading } = useConnectorCatalogCategories()
  const { data: catalogData, isLoading: catalogLoading } = useConnectorCatalog()
  const { toast } = useToast()

  const [selectedEntry, setSelectedEntry] = useState<ConnectorCatalogEntry | null>(null)

  const categories = catData?.categories ?? []
  const allEntries = catalogData?.catalog ?? []
  const entries = category === 'all'
    ? allEntries
    : allEntries.filter((e) => e.category === category)

  const isLoading = catLoading || catalogLoading

  return (
    <div className="mt-4">
      {/* Category filter tabs */}
      <Tabs value={category} onValueChange={setCategory} className="mb-4">
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          {catLoading
            ? Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-7 w-20 rounded-md" />
              ))
            : categories.map((cat) => (
                <TabsTrigger key={cat.name} value={cat.name}>
                  {cat.display_name}
                  <span className="ml-1.5 text-xs opacity-60">{cat.count}</span>
                </TabsTrigger>
              ))}
        </TabsList>
      </Tabs>

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-44" />
          ))}
        </div>
      ) : entries.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground gap-3">
          <Plug className="h-12 w-12 opacity-20" />
          <p className="text-sm">No connectors found in this category.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {entries.map((entry) => (
            <CatalogCard
              key={entry.id}
              entry={entry}
              onAdd={() => setSelectedEntry(entry)}
            />
          ))}
        </div>
      )}

      {/* Add from catalog dialog */}
      {selectedEntry && (
        <CatalogFormDialog
          entry={selectedEntry}
          open={!!selectedEntry}
          onClose={() => setSelectedEntry(null)}
        />
      )}
    </div>
  )
}

/* ── Catalog Card ──────────────────────────────────────────────────────── */

function CatalogCard({
  entry,
  onAdd,
}: {
  entry: ConnectorCatalogEntry
  onAdd: () => void
}) {
  const Icon = getCatalogIcon(entry.icon)
  const typeColor = typeColors[entry.type] ?? 'bg-zinc-500/20 text-zinc-400'

  return (
    <Card className="flex flex-col hover:border-primary/40 transition-colors">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent">
            <Icon className="h-5 w-5 text-foreground" />
          </div>
          <div className="min-w-0 flex-1">
            <CardTitle className="truncate text-base">{entry.display_name}</CardTitle>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1">
        <p className="text-sm text-muted-foreground line-clamp-2">{entry.description}</p>
        <div className="flex items-center gap-2 mt-3">
          <Badge variant="outline" className="text-[10px]">{entry.category}</Badge>
          <span className={cn('inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium', typeColor)}>
            {entry.type}
          </span>
        </div>
      </CardContent>
      <CardFooter className="pt-0">
        <Button size="sm" onClick={onAdd} className="w-full">
          <Plus className="h-3.5 w-3.5 mr-1" /> Add
        </Button>
      </CardFooter>
    </Card>
  )
}

/* ── Dynamic form dialog from catalog schema ───────────────────────────── */

interface SchemaField {
  key: string
  type: string        // "string" | "password" | "select" | "number" | "hidden"
  label: string
  description?: string
  required?: boolean
  default?: string
  options?: string[]   // for "select" type
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

function CatalogFormDialog({
  entry,
  open,
  onClose,
}: {
  entry: ConnectorCatalogEntry
  open: boolean
  onClose: () => void
}) {
  const createFromCatalog = useCreateFromCatalog()
  const connectConnector = useConnectConnector()
  const { toast } = useToast()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const configFields = parseSchemaFields(entry.config_schema)
  const credentialFields = parseSchemaFields(entry.credential_schema)
  const visibleConfigFields = configFields.filter((f) => f.type !== 'hidden')
  const visibleCredFields = credentialFields.filter((f) => f.type !== 'hidden')
  const hasFields = visibleConfigFields.length > 0 || visibleCredFields.length > 0

  // Build initial values from defaults
  const buildInitial = () => {
    const vals: Record<string, string> = {}
    ;[...configFields, ...credentialFields].forEach((f) => {
      if (f.default) vals[f.key] = String(f.default)
    })
    return vals
  }

  const [values, setValues] = useState<Record<string, string>>(buildInitial)

  const setValue = (key: string, value: string) => {
    setValues((prev) => ({ ...prev, [key]: value }))
  }

  const handleClose = () => {
    setValues(buildInitial())
    onClose()
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    try {
      // Collect config and credential values from the form
      const configVals: Record<string, string> = {}
      const credVals: Record<string, string> = {}
      configFields.forEach((f) => {
        if (values[f.key]) configVals[f.key] = values[f.key]
      })
      credentialFields.forEach((f) => {
        if (values[f.key]) credVals[f.key] = values[f.key]
      })

      // Build a unique name from the catalog entry
      const connectorName = values['_name'] || entry.id.replace(/[^a-z0-9_]/g, '_')

      // Create connector from catalog with full payload
      const connector = await createFromCatalog.mutateAsync({
        catalogId: entry.id,
        payload: {
          name: connectorName,
          display_name: entry.display_name,
          description: entry.description,
          type: entry.type,
          provider: entry.provider,
          config: configVals,
          credentials: credVals,
        },
      })

      // Connect the connector
      await connectConnector.mutateAsync(connector.name)
      toast({ title: `${entry.display_name} connected`, variant: 'success' })
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

  const Icon = getCatalogIcon(entry.icon)

  return (
    <Dialog open={open} onClose={handleClose} className="max-w-lg">
      <DialogHeader
        title={`Add ${entry.display_name}`}
        onClose={handleClose}
      />

      <div className="flex items-center gap-3 mb-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent">
          <Icon className="h-5 w-5 text-foreground" />
        </div>
        <div>
          <p className="text-sm text-muted-foreground">{entry.description}</p>
          <div className="flex gap-2 mt-1">
            <Badge variant="outline" className="text-[10px]">{entry.category}</Badge>
            <Badge variant="outline" className="text-[10px]">{entry.type}</Badge>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Connector name */}
        <div>
          <Label>Connector Name</Label>
          <Input
            value={values['_name'] ?? entry.id}
            onChange={(e) => setValue('_name', e.target.value.replace(/[^a-z0-9_]/g, '_'))}
            placeholder={entry.id}
            className="mt-1"
          />
          <p className="text-[10px] text-muted-foreground mt-1">Lowercase letters, numbers, underscores only</p>
        </div>

        {/* Config fields */}
        {visibleConfigFields.length > 0 && (
          <div className="space-y-3">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Configuration</p>
            {visibleConfigFields.map((field) => (
              <DynamicField
                key={field.key}
                field={field}
                value={values[field.key] ?? ''}
                onChange={(v) => setValue(field.key, v)}
              />
            ))}
          </div>
        )}

        {/* Credential fields */}
        {visibleCredFields.length > 0 && (
          <div className="space-y-3">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Credentials</p>
            {visibleCredFields.map((field) => (
              <DynamicField
                key={field.key}
                field={field}
                value={values[field.key] ?? ''}
                onChange={(v) => setValue(field.key, v)}
              />
            ))}
          </div>
        )}

        {!hasFields && (
          <p className="text-sm text-muted-foreground">
            No additional configuration required. Click below to create and connect.
          </p>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            <Power className="h-3.5 w-3.5 mr-1" />
            {isSubmitting ? 'Creating...' : 'Create & Connect'}
          </Button>
        </div>
      </form>
    </Dialog>
  )
}

/* ── Dynamic field renderer ────────────────────────────────────────────── */

function DynamicField({
  field,
  value,
  onChange,
}: {
  field: SchemaField
  value: string
  onChange: (value: string) => void
}) {
  return (
    <div>
      <Label>
        {field.label}
        {field.required && <span className="text-destructive ml-0.5">*</span>}
      </Label>
      {field.type === 'select' && field.options ? (
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          required={field.required}
          className="flex h-9 w-full appearance-none rounded-md border border-input bg-transparent px-3 py-1 pr-8 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring mt-1"
        >
          <option value="">Select...</option>
          {field.options.map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      ) : (
        <Input
          type={field.type === 'password' ? 'password' : field.type === 'number' ? 'number' : 'text'}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.description ?? field.label}
          required={field.required}
          className="mt-1"
        />
      )}
      {field.description && field.type !== 'password' && (
        <p className="mt-1 text-xs text-muted-foreground">{field.description}</p>
      )}
    </div>
  )
}
