import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogHeader } from '@/components/ui/dialog'
import { Separator } from '@/components/ui/separator'
import { Plus, FolderOpen, Trash2, Play, Search, LayoutTemplate, Sparkles, Bot, Server, Database, Upload } from 'lucide-react'
import {
  useWorkspaces,
  useCreateWorkspace,
  useDeleteWorkspace,
  useToggleWorkspace,
} from '@/hooks/useWorkspaces'
import { useColoneesList } from '@/hooks/useColonees'
import { useKnowledgeBases } from '@/hooks/useKnowledgeBases'
import { useTemplates, useTemplateCategories, useApplyTemplate } from '@/hooks/useTemplates'
import { useToast } from '@/components/ui/toast'
import type { WorkspaceDefinition, UseCaseTemplate } from '@/types'

const workspaceFormSchema = z.object({
  name: z.string().regex(/^[a-z0-9_-]+$/, 'Only lowercase letters, numbers, hyphens, underscores').min(2),
  display_name: z.string().min(2),
  description: z.string().min(5),
  icon: z.string().optional(),
  color: z.string().optional(),
  colonee: z.string().optional(),
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

  const applyTemplate = useApplyTemplate()

  const [search, setSearch] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [showTemplates, setShowTemplates] = useState(false)

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

  const handleApplyTemplate = async (templateName: string) => {
    try {
      const result = await applyTemplate.mutateAsync(templateName)
      setShowTemplates(false)
      toast({
        title: 'Template applied',
        description: `Workspace "${result.workspace}" created with ${result.colonees_created.length} colonee(s).`,
        variant: 'success',
      })
      navigate(`/workspaces/${result.workspace}`)
    } catch (err) {
      toast({
        title: 'Failed to apply template',
        description: err instanceof Error ? err.message : 'Unknown error',
        variant: 'error',
      })
    }
  }

  return (
    <div>
      <PageHeader
        title="Workspaces"
        description="Organize your colonees, connectors, and knowledge bases into workspaces"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setShowTemplates(true)}>
              <LayoutTemplate className="h-4 w-4 mr-2" /> From Template
            </Button>
            <Button variant="outline" onClick={async () => {
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
                  // Reload list
                  window.location.reload()
                } catch (err) {
                  toast({ title: 'Import failed', description: err instanceof Error ? err.message : 'Invalid file', variant: 'error' })
                }
              }
              input.click()
            }}>
              <Upload className="h-4 w-4 mr-2" /> Import
            </Button>
            <Button onClick={() => setShowCreate(true)}>
              <Plus className="h-4 w-4 mr-2" /> New Workspace
            </Button>
          </div>
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
              onClick={() => navigate(`/workspaces/${w.name}`)}
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
            colonees: [values.colonee].filter(Boolean) as string[],
            knowledge_bases: values.knowledge_bases,
            enabled: values.enabled,
          })
          toast({ title: 'Workspace created', variant: 'success' })
          navigate(`/workspaces/${values.name}`)
        }}
      />

      <TemplatePickerDialog
        open={showTemplates}
        onClose={() => setShowTemplates(false)}
        onApply={handleApplyTemplate}
        isApplying={applyTemplate.isPending}
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
  onClick,
  isToggling,
}: {
  workspace: WorkspaceDefinition
  onToggle: (name: string, enabled: boolean) => void
  onDelete: (name: string) => void
  onPlayground: () => void
  onClick: () => void
  isToggling: boolean
}) {
  const borderColor = workspace.color || '#6366f1'
  return (
    <Card
      className="flex flex-col cursor-pointer hover:border-primary/40 transition-colors"
      style={{ borderLeftWidth: 4, borderLeftColor: borderColor }}
      onClick={onClick}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2 min-w-0">
            {workspace.icon && <span className="text-lg">{workspace.icon}</span>}
            <CardTitle className="truncate">{workspace.display_name}</CardTitle>
          </div>
          <Switch
            checked={workspace.enabled}
            onCheckedChange={(v) => { onToggle(workspace.name, v) }}
            disabled={isToggling}
            onClick={(e) => e.stopPropagation()}
          />
        </div>
        <p className="text-xs text-muted-foreground font-mono">{workspace.name}</p>
      </CardHeader>
      <CardContent className="flex-1">
        <p className="text-sm text-muted-foreground line-clamp-2">{workspace.description}</p>
        <div className="mt-3 flex flex-wrap gap-1.5">
          <Badge variant="secondary">
            {workspace.colonees[0] || 'No agent'}
          </Badge>
          <Badge variant="secondary">
            {workspace.knowledge_bases.length} KB
          </Badge>
        </div>
      </CardContent>
      <CardFooter className="gap-2" onClick={(e) => e.stopPropagation()}>
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
  const { data: kbData } = useKnowledgeBases()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const colonees = coloneeData?.colonees ?? []
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
      colonee: '',
      knowledge_bases: [],
      enabled: true,
    },
  })

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

        {/* Specialist Agent */}
        {colonees.length > 0 && (
          <section>
            <div>
              <Label>Specialist Agent</Label>
              <Select {...register('colonee')} className="mt-1 w-full">
                <option value="">Select a colonee...</option>
                {colonees.map(c => (
                  <option key={c.name} value={c.name}>{c.display_name}</option>
                ))}
              </Select>
              <p className="text-xs text-muted-foreground mt-1">The specialist agent that will handle all tasks in this workspace</p>
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

/* -- Template Picker Dialog ------------------------------------------------ */

function TemplatePickerDialog({
  open,
  onClose,
  onApply,
  isApplying,
}: {
  open: boolean
  onClose: () => void
  onApply: (name: string) => void
  isApplying: boolean
}) {
  const { data: templatesData, isLoading } = useTemplates()

  const templates = templatesData?.templates ?? []

  return (
    <Dialog open={open} onClose={onClose} className="max-w-2xl">
      <DialogHeader title="Create Workspace from Template" onClose={onClose} />

      {isLoading ? (
        <div className="grid grid-cols-2 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      ) : templates.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground gap-3">
          <LayoutTemplate className="h-10 w-10 opacity-20" />
          <p className="text-sm">No templates available.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3 max-h-[60vh] overflow-y-auto">
          {templates.map((t) => {
            const gradientColor = t.color || '#6366f1'
            return (
              <Card
                key={t.name}
                className="cursor-pointer hover:border-primary/40 transition-colors overflow-hidden"
                onClick={() => onApply(t.name)}
              >
                <div
                  className="h-1.5"
                  style={{
                    background: `linear-gradient(135deg, ${gradientColor}, ${gradientColor}88)`,
                  }}
                />
                <CardContent className="p-3">
                  <div className="flex items-center gap-2 mb-1">
                    {t.icon && <span className="text-base">{t.icon}</span>}
                    <span className="font-semibold text-sm truncate">{t.display_name}</span>
                  </div>
                  <p className="text-xs text-muted-foreground line-clamp-2 mb-2">{t.description}</p>
                  <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Bot className="h-3 w-3" />
                      {t.colonees.length}
                    </span>
                    {t.mcp_server_suggestions.length > 0 && (
                      <span className="flex items-center gap-1">
                        <Server className="h-3 w-3" />
                        {t.mcp_server_suggestions.length}
                      </span>
                    )}
                    {t.recommended_knowledge_bases.length > 0 && (
                      <span className="flex items-center gap-1">
                        <Database className="h-3 w-3" />
                        {t.recommended_knowledge_bases.length}
                      </span>
                    )}
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {isApplying && (
        <div className="flex items-center gap-2 mt-3 text-sm text-muted-foreground">
          <Sparkles className="h-4 w-4 animate-pulse" />
          Applying template...
        </div>
      )}
    </Dialog>
  )
}
