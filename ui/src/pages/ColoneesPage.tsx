import { useState } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { ColoneeCard } from '@/components/colonees/ColoneeCard'
import { ColoneeForm, type ColoneeFormValues } from '@/components/colonees/ColoneeForm'
import { ColoneeDetailDrawer } from '@/components/colonees/ColoneeDetailDrawer'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Plus, Search } from 'lucide-react'
import {
  useColoneesList,
  useCreateColonee,
  useUpdateColonee,
  useDeleteColonee,
  useToggleColonee,
} from '@/hooks/useColonees'
import { useToast } from '@/components/ui/toast'
import type { ColoneeDefinition } from '@/types'

function formValuesToPayload(values: ColoneeFormValues, existing?: ColoneeDefinition) {
  return {
    name: values.name,
    display_name: values.display_name,
    description: values.description,
    specialist_type: values.name,
    system_prompt: values.system_prompt,
    capabilities: values.capabilities.filter(Boolean),
    built_in_tools: values.built_in_tools,
    mcp_servers: values.mcp_servers,
    tags: values.tags,
    enabled: values.enabled,
    memory: {
      enabled: values.memory_enabled,
      strategy: values.memory_strategy,
      max_size_mb: values.memory_max_size_mb,
    },
    constraints: {
      max_tool_calls: values.constraints_max_tool_calls,
      max_runtime_seconds: values.constraints_max_runtime_seconds,
      forbidden_topics: (values.forbidden_topics ?? existing?.constraints.forbidden_topics ?? []),
      output_format: values.constraints_output_format === 'free' ? null : values.constraints_output_format,
    },
    evaluation: {
      quality_threshold: values.evaluation_quality_threshold,
      require_sources: values.evaluation_require_sources,
      require_structured_output: values.evaluation_require_structured_output,
      custom_criteria: (values.custom_criteria ?? existing?.evaluation.custom_criteria ?? []),
    },
  }
}

export function ColoneesPage() {
  const { data, isLoading } = useColoneesList()
  const createColonee = useCreateColonee()
  const updateColonee = useUpdateColonee()
  const deleteColonee = useDeleteColonee()
  const toggleColonee = useToggleColonee()
  const { toast } = useToast()

  const [search, setSearch] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [editColonee, setEditColonee] = useState<ColoneeDefinition | null>(null)
  const [viewColonee, setViewColonee] = useState<ColoneeDefinition | null>(null)

  const colonees = data?.colonees ?? []
  const filtered = colonees.filter(c =>
    c.display_name.toLowerCase().includes(search.toLowerCase()) ||
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.description.toLowerCase().includes(search.toLowerCase()),
  )

  const handleCreate = async (values: ColoneeFormValues) => {
    await createColonee.mutateAsync(formValuesToPayload(values))
    toast({ title: 'Colonee created', variant: 'success' })
  }

  const handleEdit = async (values: ColoneeFormValues) => {
    if (!editColonee) return
    const payload = formValuesToPayload(values, editColonee)
    await updateColonee.mutateAsync({ name: editColonee.name, payload })
    toast({ title: 'Colonee updated', variant: 'success' })
  }

  const handleDelete = async (name: string) => {
    if (!confirm(`Delete colonee "${name}"?`)) return
    await deleteColonee.mutateAsync(name)
    toast({ title: 'Colonee deleted', variant: 'info' })
  }

  const handleToggle = async (name: string, enabled: boolean) => {
    await toggleColonee.mutateAsync({ name, enabled })
  }

  return (
    <div>
      <PageHeader
        title="Colonees"
        description="Manage your specialist agent definitions"
        actions={
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="h-4 w-4 mr-2" /> New Colonee
          </Button>
        }
      />

      <div className="mb-4 flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search colonees…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8"
          />
        </div>
        <span className="text-sm text-muted-foreground">
          {filtered.length} colonee{filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-48" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map(c => (
            <ColoneeCard
              key={c.name}
              colonee={c}
              onToggle={handleToggle}
              onView={setViewColonee}
              onEdit={setEditColonee}
              onDelete={handleDelete}
              isToggling={toggleColonee.isPending}
            />
          ))}
        </div>
      )}

      <ColoneeForm
        open={showCreate}
        onClose={() => setShowCreate(false)}
        onSubmit={handleCreate}
      />

      {editColonee && (
        <ColoneeForm
          open={!!editColonee}
          onClose={() => setEditColonee(null)}
          onSubmit={handleEdit}
          defaultValues={editColonee}
          isEdit
        />
      )}

      <ColoneeDetailDrawer
        colonee={viewColonee}
        onClose={() => setViewColonee(null)}
      />
    </div>
  )
}
