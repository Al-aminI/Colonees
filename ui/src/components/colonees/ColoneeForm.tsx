import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Dialog, DialogHeader } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Separator } from '@/components/ui/separator'
import { useState } from 'react'
import { Plus, X, ChevronDown, ChevronRight } from 'lucide-react'
import type { ColoneeDefinition } from '@/types'
import { useMcpServers } from '@/hooks/useMcpServers'

export const coloneeFormSchema = z.object({
  name: z
    .string()
    .regex(/^[a-z0-9_]+$/, 'Only lowercase letters, numbers, underscores')
    .min(2, 'Min 2 characters'),
  display_name: z.string().min(2, 'Min 2 characters'),
  description: z.string().min(10, 'Min 10 characters — describe what this agent does'),
  specialist_type: z.string().optional(),
  system_prompt: z.string().min(20, 'Min 20 characters'),
  capabilities: z.array(z.string()).min(1, 'Add at least one capability'),
  built_in_tools: z.array(z.enum(['file', 'computation', 'research', 'media'])),
  mcp_servers: z.array(z.string()),
  tags: z.array(z.string()),
  enabled: z.boolean(),
  memory_enabled: z.boolean(),
  memory_strategy: z.enum(['basic', 'semantic', 'episodic']),
  memory_max_size_mb: z.number().min(1).max(4096),
  constraints_max_tool_calls: z.number().min(1).max(1000),
  constraints_max_runtime_seconds: z.number().min(10).max(3600),
  constraints_output_format: z.enum(['free', 'json', 'markdown']),
  forbidden_topics: z.array(z.string()),
  evaluation_quality_threshold: z.number().min(0).max(1),
  evaluation_require_sources: z.boolean(),
  evaluation_require_structured_output: z.boolean(),
  custom_criteria: z.array(z.string()),
})

export type ColoneeFormValues = z.infer<typeof coloneeFormSchema>

interface ColoneeFormProps {
  open: boolean
  onClose: () => void
  onSubmit: (values: ColoneeFormValues) => Promise<void>
  defaultValues?: ColoneeDefinition
  isEdit?: boolean
}

const BUILT_IN_TOOLS = ['file', 'computation', 'research', 'media'] as const

function SectionHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-3">
      <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">{title}</h3>
      {subtitle && <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>}
    </div>
  )
}

function CollapsibleSection({
  title,
  defaultOpen = false,
  children,
}: {
  title: string
  defaultOpen?: boolean
  children: React.ReactNode
}) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div>
      <button
        type="button"
        className="flex items-center gap-2 w-full text-left py-1"
        onClick={() => setOpen((o) => !o)}
      >
        {open ? (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
        )}
        <span className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          {title}
        </span>
      </button>
      {open && <div className="mt-3 space-y-3">{children}</div>}
    </div>
  )
}

function Req() {
  return <span className="text-destructive ml-0.5">*</span>
}

export function ColoneeForm({ open, onClose, onSubmit, defaultValues, isEdit }: ColoneeFormProps) {
  const { data: mcpData } = useMcpServers()
  const mcpServers = mcpData?.servers ?? []
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
    reset,
  } = useForm<ColoneeFormValues>({
    resolver: zodResolver(coloneeFormSchema),
    defaultValues: defaultValues
      ? {
          name: defaultValues.name,
          display_name: defaultValues.display_name,
          description: defaultValues.description,
          specialist_type: defaultValues.specialist_type,
          system_prompt: defaultValues.system_prompt,
          capabilities: defaultValues.capabilities,
          built_in_tools: defaultValues.built_in_tools,
          mcp_servers: defaultValues.mcp_servers,
          tags: defaultValues.tags,
          enabled: defaultValues.enabled,
          memory_enabled: defaultValues.memory.enabled,
          memory_strategy: defaultValues.memory.strategy as ColoneeFormValues['memory_strategy'],
          memory_max_size_mb: defaultValues.memory.max_size_mb,
          constraints_max_tool_calls: defaultValues.constraints.max_tool_calls,
          constraints_max_runtime_seconds: defaultValues.constraints.max_runtime_seconds,
          constraints_output_format: (defaultValues.constraints.output_format as ColoneeFormValues['constraints_output_format']) || 'free',
          forbidden_topics: defaultValues.constraints.forbidden_topics ?? [],
          evaluation_quality_threshold: defaultValues.evaluation.quality_threshold,
          evaluation_require_sources: defaultValues.evaluation.require_sources,
          evaluation_require_structured_output: defaultValues.evaluation.require_structured_output,
          custom_criteria: defaultValues.evaluation.custom_criteria ?? [],
        }
      : {
          name: '',
          display_name: '',
          description: '',
          system_prompt: '',
          capabilities: [],
          built_in_tools: [],
          mcp_servers: [],
          tags: [],
          enabled: true,
          memory_enabled: true,
          memory_strategy: 'basic',
          memory_max_size_mb: 64,
          constraints_max_tool_calls: 50,
          constraints_max_runtime_seconds: 300,
          constraints_output_format: 'free',
          forbidden_topics: [],
          evaluation_quality_threshold: 0.7,
          evaluation_require_sources: false,
          evaluation_require_structured_output: false,
          custom_criteria: [],
        },
  })

  const capabilities = watch('capabilities') ?? []
  const builtInTools = watch('built_in_tools') ?? []
  const selectedMcp = watch('mcp_servers') ?? []
  const tags = watch('tags') ?? []
  const watchedSystemPrompt = watch('system_prompt')

  const handleClose = () => {
    reset()
    onClose()
  }

  const handleFormSubmit = async (values: ColoneeFormValues) => {
    setIsSubmitting(true)
    try {
      await onSubmit(values)
      handleClose()
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onClose={handleClose} className="max-w-2xl max-h-[90vh] overflow-y-auto">
      <DialogHeader title={isEdit ? 'Edit Colonee' : 'Create Colonee'} onClose={handleClose} />

      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
        {/* ── Identity ─────────────────────────────────────────────────── */}
        <section>
          <SectionHeader
            title="Identity"
            subtitle="Name your agent and define its role"
          />

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label><Req /> Name (slug)</Label>
              <Input
                {...register('name')}
                placeholder="my_research_agent"
                disabled={isEdit}
                className="mt-1 font-mono text-sm"
              />
              {errors.name && <p className="mt-1 text-xs text-destructive">{errors.name.message}</p>}
              <p className="mt-0.5 text-[11px] text-muted-foreground">
                Unique identifier — lowercase, no spaces
              </p>
            </div>
            <div>
              <Label><Req /> Display Name</Label>
              <Input {...register('display_name')} placeholder="My Research Agent" className="mt-1" />
              {errors.display_name && <p className="mt-1 text-xs text-destructive">{errors.display_name.message}</p>}
            </div>
          </div>

          <div className="mt-3">
            <Label><Req /> Description</Label>
            <Textarea
              {...register('description')}
              placeholder="Describe what this agent does, its domain, and its intended use case..."
              className="mt-1"
              rows={3}
            />
            {errors.description && (
              <p className="mt-1 text-xs text-destructive">{errors.description.message}</p>
            )}
          </div>

          <div className="mt-3 flex items-center gap-3">
            <Switch
              checked={watch('enabled')}
              onCheckedChange={(v) => setValue('enabled', v)}
            />
            <Label>Enabled — agent can be spawned by the superagent</Label>
          </div>
        </section>

        <Separator />

        {/* ── Behavior ─────────────────────────────────────────────────── */}
        <section>
          <SectionHeader
            title="Behavior"
            subtitle="Instructions that define how this agent thinks and acts"
          />

          <div>
            <Label><Req /> System Prompt</Label>
            <p className="text-xs text-muted-foreground mt-0.5">
              Use <code className="rounded bg-muted px-1 text-[11px]">{'{specialization}'}</code> as a
              placeholder — it will be replaced with the agent's specialization at runtime.
            </p>
            <Textarea
              {...register('system_prompt')}
              rows={6}
              placeholder="You are a {specialization} specialist. Your role is to..."
              className="mt-1"
            />
            {errors.system_prompt && (
              <p className="mt-1 text-xs text-destructive">{errors.system_prompt.message}</p>
            )}
          </div>

          {watchedSystemPrompt && watchedSystemPrompt.includes('{specialization}') && (
            <div className="mt-2 rounded-md border border-border bg-muted/30 p-3">
              <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wide mb-1">
                Preview
              </p>
              <pre className="text-xs whitespace-pre-wrap text-foreground/80">
                {watchedSystemPrompt.replace(
                  /\{specialization\}/g,
                  watch('display_name') || 'your domain',
                )}
              </pre>
            </div>
          )}

          <div className="mt-4">
            <Label><Req /> Capabilities</Label>
            <p className="text-xs text-muted-foreground mt-0.5 mb-2">
              Free-form tags that describe what this agent can do (e.g. "web_research", "data_analysis").
              These are used by the superagent to match goals to the right specialist.
            </p>
            <div className="space-y-2">
              {capabilities.length === 0 && (
                <p className="text-xs text-muted-foreground italic py-1">
                  No capabilities added yet. Add at least one.
                </p>
              )}
              {capabilities.map((_, i) => (
                <div key={i} className="flex gap-2">
                  <Input
                    value={capabilities[i]}
                    onChange={(e) => {
                      const next = [...capabilities]
                      next[i] = e.target.value
                      setValue('capabilities', next, { shouldValidate: true })
                    }}
                    placeholder="e.g. web_research"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() =>
                      setValue(
                        'capabilities',
                        capabilities.filter((_, j) => j !== i),
                        { shouldValidate: true },
                      )
                    }
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
            {errors.capabilities && (
              <p className="mt-1 text-xs text-destructive">{errors.capabilities.message}</p>
            )}
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="mt-2"
              onClick={() => setValue('capabilities', [...capabilities, ''], { shouldValidate: true })}
            >
              <Plus className="h-3.5 w-3.5 mr-1" /> Add Capability
            </Button>
          </div>
        </section>

        <Separator />

        {/* ── Tools ────────────────────────────────────────────────────── */}
        <section>
          <SectionHeader
            title="Tools"
            subtitle="Which built-in tool sets and external MCP servers this agent can use"
          />

          <div className="grid grid-cols-2 gap-2">
            {BUILT_IN_TOOLS.map((tool) => (
              <label key={tool} className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  checked={builtInTools.includes(tool)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setValue('built_in_tools', [...builtInTools, tool])
                    } else {
                      setValue('built_in_tools', builtInTools.filter((t) => t !== tool))
                    }
                  }}
                  className="rounded"
                />
                <span className="capitalize">{tool}</span>
              </label>
            ))}
          </div>

          {mcpServers.length > 0 && (
            <div className="mt-3">
              <Label className="mb-2 block">MCP Servers</Label>
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
                          setValue('mcp_servers', selectedMcp.filter((n) => n !== s.name))
                        }
                      }}
                      className="rounded"
                    />
                    <span>{s.name}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {mcpServers.length === 0 && (
            <p className="mt-2 text-xs text-muted-foreground italic">
              No MCP servers registered. Register one in{' '}
              <span className="font-medium">Connectors → MCP Servers</span>.
            </p>
          )}
        </section>

        <Separator />

        {/* ── Tags ─────────────────────────────────────────────────────── */}
        <section>
          <SectionHeader
            title="Tags"
            subtitle="Label your agent for filtering and discovery"
          />

          <div className="flex flex-wrap gap-2 mb-2">
            {tags.length === 0 && (
              <p className="text-xs text-muted-foreground italic py-1">No tags yet.</p>
            )}
            {tags.map((tag, i) => (
              <span
                key={i}
                className="flex items-center gap-1 rounded-full bg-muted px-2.5 py-1 text-xs"
              >
                {tag}
                <button
                  type="button"
                  onClick={() => setValue('tags', tags.filter((_, j) => j !== i))}
                  className="opacity-60 hover:opacity-100"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
          </div>
          <Input
            placeholder="Type a tag and press Enter"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                const val = (e.target as HTMLInputElement).value.trim()
                if (val && !tags.includes(val)) {
                  setValue('tags', [...tags, val])
                  ;(e.target as HTMLInputElement).value = ''
                }
              }
            }}
          />
        </section>

        <Separator />

        {/* ── Advanced ─────────────────────────────────────────────────── */}
        <section>
          <CollapsibleSection title="Advanced Configuration">
            {/* Memory */}
            <div>
              <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Memory
              </Label>
              <div className="grid grid-cols-3 gap-3 mt-2 items-end">
                <div className="flex items-center gap-2">
                  <Switch
                    checked={watch('memory_enabled')}
                    onCheckedChange={(v) => setValue('memory_enabled', v)}
                  />
                  <Label>Enable Memory</Label>
                </div>
                <div>
                  <Label>Strategy</Label>
                  <Select {...register('memory_strategy')} className="mt-1 w-full">
                    <option value="basic">Basic</option>
                    <option value="semantic">Semantic</option>
                    <option value="episodic">Episodic</option>
                  </Select>
                </div>
                <div>
                  <Label>Max Size (MB)</Label>
                  <Input
                    type="number"
                    {...register('memory_max_size_mb', { valueAsNumber: true })}
                    className="mt-1"
                  />
                </div>
              </div>
            </div>

            <Separator />

            {/* Constraints */}
            <div>
              <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Constraints
              </Label>
              <div className="grid grid-cols-3 gap-3 mt-2">
                <div>
                  <Label>Max Tool Calls</Label>
                  <Input
                    type="number"
                    {...register('constraints_max_tool_calls', { valueAsNumber: true })}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label>Max Runtime (s)</Label>
                  <Input
                    type="number"
                    {...register('constraints_max_runtime_seconds', { valueAsNumber: true })}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label>Output Format</Label>
                  <Select {...register('constraints_output_format')} className="mt-1 w-full">
                    <option value="free">Free form</option>
                    <option value="json">JSON</option>
                    <option value="markdown">Markdown</option>
                  </Select>
                </div>
              </div>

              <div className="mt-3">
                <Label>Forbidden Topics</Label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {(watch('forbidden_topics') ?? []).length === 0 && (
                    <p className="text-xs text-muted-foreground italic py-1">None</p>
                  )}
                  {(watch('forbidden_topics') ?? []).map((topic, i) => (
                    <span
                      key={i}
                      className="flex items-center gap-1 rounded-full bg-destructive/10 px-2.5 py-1 text-xs text-destructive"
                    >
                      {topic}
                      <button
                        type="button"
                        onClick={() => {
                          const next = [...(watch('forbidden_topics') ?? [])]
                          next.splice(i, 1)
                          setValue('forbidden_topics', next)
                        }}
                        className="opacity-60 hover:opacity-100"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
                <Input
                  placeholder="Add topic and press Enter"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      const val = (e.target as HTMLInputElement).value.trim()
                      const current = watch('forbidden_topics') ?? []
                      if (val && !current.includes(val)) {
                        setValue('forbidden_topics', [...current, val])
                        ;(e.target as HTMLInputElement).value = ''
                      }
                    }
                  }}
                />
              </div>
            </div>

            <Separator />

            {/* Evaluation */}
            <div>
              <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Evaluation
              </Label>
              <div className="grid grid-cols-3 gap-3 mt-2 items-end">
                <div>
                  <Label>Quality Threshold</Label>
                  <Input
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    {...register('evaluation_quality_threshold', { valueAsNumber: true })}
                    className="mt-1"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <Switch
                    checked={watch('evaluation_require_sources')}
                    onCheckedChange={(v) => setValue('evaluation_require_sources', v)}
                  />
                  <Label>Require Sources</Label>
                </div>
                <div className="flex items-center gap-2">
                  <Switch
                    checked={watch('evaluation_require_structured_output')}
                    onCheckedChange={(v) => setValue('evaluation_require_structured_output', v)}
                  />
                  <Label>Require Structured Output</Label>
                </div>
              </div>

              <div className="mt-3">
                <Label>Custom Criteria</Label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {(watch('custom_criteria') ?? []).length === 0 && (
                    <p className="text-xs text-muted-foreground italic py-1">None</p>
                  )}
                  {(watch('custom_criteria') ?? []).map((criterion, i) => (
                    <span
                      key={i}
                      className="flex items-center gap-1 rounded-full bg-muted px-2.5 py-1 text-xs"
                    >
                      {criterion}
                      <button
                        type="button"
                        onClick={() => {
                          const next = [...(watch('custom_criteria') ?? [])]
                          next.splice(i, 1)
                          setValue('custom_criteria', next)
                        }}
                        className="opacity-60 hover:opacity-100"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
                <Input
                  placeholder="Add criterion and press Enter"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      const val = (e.target as HTMLInputElement).value.trim()
                      const current = watch('custom_criteria') ?? []
                      if (val && !current.includes(val)) {
                        setValue('custom_criteria', [...current, val])
                        ;(e.target as HTMLInputElement).value = ''
                      }
                    }
                  }}
                />
              </div>
            </div>
          </CollapsibleSection>
        </section>

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Saving…' : isEdit ? 'Update Colonee' : 'Create Colonee'}
          </Button>
        </div>
      </form>
    </Dialog>
  )
}
