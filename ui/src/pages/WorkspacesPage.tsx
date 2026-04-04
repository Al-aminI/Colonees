import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogHeader } from '@/components/ui/dialog'
import { Separator } from '@/components/ui/separator'
import { Plus, FolderOpen, Trash2, Play, Search } from 'lucide-react'
import {
  useWorkspaces,
  useCreateWorkspace,
  useDeleteWorkspace,
  useToggleWorkspace,
} from '@/hooks/useWorkspaces'
import { useColoneesList } from '@/hooks/useColonees'
import { useMcpServers } from '@/hooks/useMcpServers'
import { useKnowledgeBases } from '@/hooks/useKnowledgeBases'
import { useToast } from '@/components/ui/toast'
import type { WorkspaceDefinition } from '@/types'

const workspaceFormSchema = z.object({
  name: z.string().regex(/^[a-z0-9_-]+$/, 'Only lowercase letters, numbers, hyphens, underscores').min(2),
  display_name: z.string().min(2),
  description: z.string().min(5),
  icon: z.string().optional(),
  color: z.string().optional(),
  colonees: z.array(z.string()),
  mcp_servers: z.array(z.string()),
  knowledge_bases: z.array(z.string()),
  enabled: z.boolean(),
})

type WorkspaceFormValues = z.infer<typeof workspaceFormSchema>

export function WorkspacesPage() {
  const { data, isLoading } = useWorkspaces()
  const createWorkspace = useCreateWorkspace()
  const deleteWorkspace = useDeleteWorkspace()
  const toggleWorkspace = useToggleWorkspace()
  const { toast } = useToast()
  const navigate = useNavigate()

  const [search, setSearch] = useState('')
  const [showCreate, setShowCreate] = useState(false)

  const workspaces = data?.workspaces ?? []
  const filtered = workspaces.filter(
    w =>
      w.display_name.toLowerCase().includes(search.toLowerCase()) ||
      w.name.toLowerCase().includes(search.toLowerCase()) ||
      w.description.toLowerCase().includes(search.toLowerCase()),
  )

  const handleDelete = async (name: string) => {
    if (!confirm(`Delete workspace "${name}"?`)) return
    await deleteWorkspace.mutateAsync(name)
    toast({ title: 'Workspace deleted', variant: 'info' })
  }

  const handleToggle = async (name: string, enabled: boolean) => {
    await toggleWorkspace.mutateAsync({ name, enabled })
  }

  return (
    <div>
      <PageHeader
        title="Workspaces"
        description="Organize your colonees, MCP servers, and knowledge bases into workspaces"
        actions={
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="h-4 w-4 mr-2" /> New Workspace
          </Button>
        }
      />

      <div className="mb-4 flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search workspaces..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8"
          />
        </div>
        <span className="text-sm text-muted-foreground">
          {filtered.length} workspace{filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-48" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground gap-3">
          <FolderOpen className="h-12 w-12 opacity-20" />
          <p className="text-sm">No workspaces found.</p>
          <Button variant="outline" onClick={() => setShowCreate(true)}>
            Create your first workspace
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((w) => (
            <WorkspaceCard
              key={w.name}
              workspace={w}
              onToggle={handleToggle}
              onDelete={handleDelete}
              onPlayground={() => navigate('/playground')}
              isToggling={toggleWorkspace.isPending}
            />
          ))}
        </div>
      )}

      <CreateWorkspaceDialog
        open={showCreate}
        onClose={() => setShowCreate(false)}
        onCreate={async (values) => {
          await createWorkspace.mutateAsync({
            name: values.name,
            display_name: values.display_name,
            description: values.description,
            icon: values.icon || undefined,
            color: values.color || undefined,
            colonees: values.colonees,
            mcp_servers: values.mcp_servers,
            knowledge_bases: values.knowledge_bases,
            enabled: values.enabled,
          })
          toast({ title: 'Workspace created', variant: 'success' })
        }}
      />
    </div>
  )
}

/* ── Workspace Card ────────────────────────────────────────────────────── */

function WorkspaceCard({
  workspace,
  onToggle,
  onDelete,
  onPlayground,
  isToggling,
}: {
  workspace: WorkspaceDefinition
  onToggle: (name: string, enabled: boolean) => void
  onDelete: (name: string) => void
  onPlayground: () => void
  isToggling: boolean
}) {
  const borderColor = workspace.color || '#6366f1'
  return (
    <Card className="flex flex-col" style={{ borderLeftWidth: 4, borderLeftColor: borderColor }}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2 min-w-0">
            {workspace.icon && <span className="text-lg">{workspace.icon}</span>}
            <CardTitle className="truncate">{workspace.display_name}</CardTitle>
          </div>
          <Switch
            checked={workspace.enabled}
            onCheckedChange={(v) => onToggle(workspace.name, v)}
            disabled={isToggling}
          />
        </div>
        <p className="text-xs text-muted-foreground font-mono">{workspace.name}</p>
      </CardHeader>
      <CardContent className="flex-1">
        <p className="text-sm text-muted-foreground line-clamp-2">{workspace.description}</p>
        <div className="mt-3 flex flex-wrap gap-1.5">
          <Badge variant="secondary">
            {workspace.colonees.length} agent{workspace.colonees.length !== 1 ? 's' : ''}
          </Badge>
          <Badge variant="secondary">
            {workspace.mcp_servers.length} MCP
          </Badge>
          <Badge variant="secondary">
            {workspace.knowledge_bases.length} KB
          </Badge>
        </div>
      </CardContent>
      <CardFooter className="gap-2">
        <Button variant="outline" size="sm" onClick={onPlayground}>
          <Play className="h-3.5 w-3.5 mr-1" /> Playground
        </Button>
        <div className="flex-1" />
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-destructive hover:text-destructive"
          onClick={() => onDelete(workspace.name)}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </CardFooter>
    </Card>
  )
}

/* ── Create Dialog ─────────────────────────────────────────────────────── */

function CreateWorkspaceDialog({
  open,
  onClose,
  onCreate,
}: {
  open: boolean
  onClose: () => void
  onCreate: (values: WorkspaceFormValues) => Promise<void>
}) {
  const { data: coloneeData } = useColoneesList()
  const { data: mcpData } = useMcpServers()
  const { data: kbData } = useKnowledgeBases()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const colonees = coloneeData?.colonees ?? []
  const mcpServers = mcpData?.servers ?? []
  const knowledgeBases = kbData?.knowledge_bases ?? []

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
    reset,
  } = useForm<WorkspaceFormValues>({
    resolver: zodResolver(workspaceFormSchema),
    defaultValues: {
      colonees: [],
      mcp_servers: [],
      knowledge_bases: [],
      enabled: true,
    },
  })

  const selectedColonees = watch('colonees') ?? []
  const selectedMcp = watch('mcp_servers') ?? []
  const selectedKB = watch('knowledge_bases') ?? []

  const handleClose = () => {
    reset()
    onClose()
  }

  const onSubmit = async (values: WorkspaceFormValues) => {
    setIsSubmitting(true)
    try {
      await onCreate(values)
      handleClose()
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onClose={handleClose} className="max-w-2xl">
      <DialogHeader title="Create Workspace" onClose={handleClose} />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {/* Identity */}
        <section>
          <h3 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wide">
            Identity
          </h3>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Name (slug)</Label>
              <Input {...register('name')} placeholder="my-workspace" className="mt-1" />
              {errors.name && (
                <p className="mt-1 text-xs text-destructive">{errors.name.message}</p>
              )}
            </div>
            <div>
              <Label>Display Name</Label>
              <Input {...register('display_name')} placeholder="My Workspace" className="mt-1" />
              {errors.display_name && (
                <p className="mt-1 text-xs text-destructive">{errors.display_name.message}</p>
              )}
            </div>
          </div>
          <div className="mt-3">
            <Label>Description</Label>
            <Textarea
              {...register('description')}
              placeholder="What is this workspace for?"
              className="mt-1"
              rows={2}
            />
            {errors.description && (
              <p className="mt-1 text-xs text-destructive">{errors.description.message}</p>
            )}
          </div>
          <div className="grid grid-cols-2 gap-3 mt-3">
            <div>
              <Label>Icon (emoji)</Label>
              <Input {...register('icon')} placeholder="e.g. 🚀" className="mt-1" />
            </div>
            <div>
              <Label>Color (hex)</Label>
              <Input {...register('color')} placeholder="#6366f1" className="mt-1" />
            </div>
          </div>
          <div className="mt-3 flex items-center gap-3">
            <Label>Enabled</Label>
            <Switch
              checked={watch('enabled')}
              onCheckedChange={(v) => setValue('enabled', v)}
            />
          </div>
        </section>

        <Separator />

        {/* Colonees */}
        {colonees.length > 0 && (
          <section>
            <h3 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wide">
              Colonees
            </h3>
            <div className="grid grid-cols-2 gap-2">
              {colonees.map((c) => (
                <label key={c.name} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedColonees.includes(c.name)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setValue('colonees', [...selectedColonees, c.name])
                      } else {
                        setValue(
                          'colonees',
                          selectedColonees.filter((n) => n !== c.name),
                        )
                      }
                    }}
                    className="rounded"
                  />
                  <span>{c.display_name}</span>
                </label>
              ))}
            </div>
          </section>
        )}

        {/* MCP Servers */}
        {mcpServers.length > 0 && (
          <section>
            <h3 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wide">
              MCP Servers
            </h3>
            <div className="grid grid-cols-2 gap-2">
              {mcpServers.map((s) => (
                <label key={s.name} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedMcp.includes(s.name)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setValue('mcp_servers', [...selectedMcp, s.name])
                      } else {
                        setValue(
                          'mcp_servers',
                          selectedMcp.filter((n) => n !== s.name),
                        )
                      }
                    }}
                    className="rounded"
                  />
                  <span>{s.name}</span>
                </label>
              ))}
            </div>
          </section>
        )}

        {/* Knowledge Bases */}
        {knowledgeBases.length > 0 && (
          <section>
            <h3 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wide">
              Knowledge Bases
            </h3>
            <div className="grid grid-cols-2 gap-2">
              {knowledgeBases.map((kb) => (
                <label key={kb.name} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedKB.includes(kb.name)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setValue('knowledge_bases', [...selectedKB, kb.name])
                      } else {
                        setValue(
                          'knowledge_bases',
                          selectedKB.filter((n) => n !== kb.name),
                        )
                      }
                    }}
                    className="rounded"
                  />
                  <span>{kb.display_name}</span>
                </label>
              ))}
            </div>
          </section>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Creating...' : 'Create Workspace'}
          </Button>
        </div>
      </form>
    </Dialog>
  )
}
