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
import { Plus, X } from 'lucide-react'
import type { ColoneeDefinition } from '@/types'
import { useMcpServers } from '@/hooks/useMcpServers'

export const coloneeFormSchema = z.object({
  name: z.string().regex(/^[a-z0-9_]+$/, 'Only lowercase letters, numbers, underscores').min(2),
  display_name: z.string().min(2),
  description: z.string().min(10),
  specialist_type: z.enum(['researcher', 'domain_expert', 'analyst', 'executor', 'media_producer']),
  system_prompt: z.string().min(20),
  capabilities: z.array(z.string()).min(1),
  built_in_tools: z.array(z.enum(['file', 'computation', 'research', 'media'])),
  mcp_servers: z.array(z.string()),
  tags: z.array(z.string()),
  enabled: z.boolean(),
  memory_enabled: z.boolean(),
  memory_strategy: z.enum(['basic', 'semantic', 'episodic']),
  memory_max_size_mb: z.number().min(1).max(4096),
  constraints_max_tool_calls: z.number().min(1).max(1000),
  constraints_max_runtime_seconds: z.number().min(10).max(3600),
  evaluation_quality_threshold: z.number().min(0).max(1),
  evaluation_require_sources: z.boolean(),
  evaluation_require_structured_output: z.boolean(),
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
          memory_strategy: defaultValues.memory.strategy,
          memory_max_size_mb: defaultValues.memory.max_size_mb,
          constraints_max_tool_calls: defaultValues.constraints.max_tool_calls,
          constraints_max_runtime_seconds: defaultValues.constraints.max_runtime_seconds,
          evaluation_quality_threshold: defaultValues.evaluation.quality_threshold,
          evaluation_require_sources: defaultValues.evaluation.require_sources,
          evaluation_require_structured_output: defaultValues.evaluation.require_structured_output,
        }
      : {
          specialist_type: 'researcher',
          capabilities: [''],
          built_in_tools: [],
          mcp_servers: [],
          tags: [],
          enabled: true,
          memory_enabled: true,
          memory_strategy: 'basic',
          memory_max_size_mb: 64,
          constraints_max_tool_calls: 50,
          constraints_max_runtime_seconds: 300,
          evaluation_quality_threshold: 0.7,
          evaluation_require_sources: false,
          evaluation_require_structured_output: false,
        },
  })

  const capabilities = watch('capabilities') ?? []
  const builtInTools = watch('built_in_tools') ?? []
  const selectedMcp = watch('mcp_servers') ?? []
  const tags = watch('tags') ?? []

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
    <Dialog open={open} onClose={handleClose} className="max-w-2xl">
      <DialogHeader title={isEdit ? 'Edit Colonee' : 'Create Colonee'} onClose={handleClose} />

      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-5">
        {/* Identity */}
        <section>
          <h3 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wide">Identity</h3>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Name (slug)</Label>
              <Input
                {...register('name')}
                placeholder="my_agent"
                disabled={isEdit}
                className="mt-1"
              />
              {errors.name && <p className="mt-1 text-xs text-destructive">{errors.name.message}</p>}
            </div>
            <div>
              <Label>Display Name</Label>
              <Input {...register('display_name')} placeholder="My Agent" className="mt-1" />
              {errors.display_name && <p className="mt-1 text-xs text-destructive">{errors.display_name.message}</p>}
            </div>
          </div>
          <div className="mt-3">
            <Label>Specialist Type</Label>
            <Select {...register('specialist_type')} className="mt-1 w-full">
              <option value="researcher">Researcher</option>
              <option value="domain_expert">Domain Expert</option>
              <option value="analyst">Analyst</option>
              <option value="executor">Executor</option>
              <option value="media_producer">Media Producer</option>
            </Select>
          </div>
          <div className="mt-3">
            <Label>Description</Label>
            <Textarea {...register('description')} placeholder="What does this agent do?" className="mt-1" rows={2} />
            {errors.description && <p className="mt-1 text-xs text-destructive">{errors.description.message}</p>}
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

        {/* System Prompt */}
        <section>
          <h3 className="text-sm font-semibold mb-1 text-muted-foreground uppercase tracking-wide">System Prompt</h3>
          <p className="text-xs text-muted-foreground mb-2">Use {'{specialization}'} as a placeholder for the agent's specialization.</p>
          <Textarea {...register('system_prompt')} rows={5} placeholder="You are a {specialization} specialist..." />
          {errors.system_prompt && <p className="mt-1 text-xs text-destructive">{errors.system_prompt.message}</p>}
        </section>

        <Separator />

        {/* Capabilities */}
        <section>
          <h3 className="text-sm font-semibold mb-2 text-muted-foreground uppercase tracking-wide">Capabilities</h3>
          <div className="space-y-2">
            {capabilities.map((_, i) => (
              <div key={i} className="flex gap-2">
                <Input
                  value={capabilities[i]}
                  onChange={(e) => {
                    const next = [...capabilities]
                    next[i] = e.target.value
                    setValue('capabilities', next)
                  }}
                  placeholder="e.g. web_research"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => setValue('capabilities', capabilities.filter((_, j) => j !== i))}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ))}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setValue('capabilities', [...capabilities, ''])}
            >
              <Plus className="h-3.5 w-3.5 mr-1" /> Add Capability
            </Button>
          </div>
        </section>

        <Separator />

        {/* Tools */}
        <section>
          <h3 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wide">Built-in Tools</h3>
          <div className="grid grid-cols-2 gap-2">
            {BUILT_IN_TOOLS.map(tool => (
              <label key={tool} className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  checked={builtInTools.includes(tool)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setValue('built_in_tools', [...builtInTools, tool])
                    } else {
                      setValue('built_in_tools', builtInTools.filter(t => t !== tool))
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
                {mcpServers.map(s => (
                  <label key={s.name} className="flex items-center gap-2 text-sm cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedMcp.includes(s.name)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setValue('mcp_servers', [...selectedMcp, s.name])
                        } else {
                          setValue('mcp_servers', selectedMcp.filter(n => n !== s.name))
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
        </section>

        <Separator />

        {/* Memory */}
        <section>
          <h3 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wide">Memory</h3>
          <div className="grid grid-cols-3 gap-3 items-end">
            <div className="flex items-center gap-2 mt-1">
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
        </section>

        <Separator />

        {/* Constraints */}
        <section>
          <h3 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wide">Constraints</h3>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Max Tool Calls</Label>
              <Input
                type="number"
                {...register('constraints_max_tool_calls', { valueAsNumber: true })}
                className="mt-1"
              />
            </div>
            <div>
              <Label>Max Runtime (seconds)</Label>
              <Input
                type="number"
                {...register('constraints_max_runtime_seconds', { valueAsNumber: true })}
                className="mt-1"
              />
            </div>
          </div>
        </section>

        <Separator />

        {/* Evaluation */}
        <section>
          <h3 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wide">Evaluation</h3>
          <div className="grid grid-cols-3 gap-3 items-end">
            <div>
              <Label>Quality Threshold (0–1)</Label>
              <Input
                type="number"
                step="0.1"
                min="0"
                max="1"
                {...register('evaluation_quality_threshold', { valueAsNumber: true })}
                className="mt-1"
              />
            </div>
            <div className="flex items-center gap-2 mt-1">
              <Switch
                checked={watch('evaluation_require_sources')}
                onCheckedChange={(v) => setValue('evaluation_require_sources', v)}
              />
              <Label>Require Sources</Label>
            </div>
            <div className="flex items-center gap-2 mt-1">
              <Switch
                checked={watch('evaluation_require_structured_output')}
                onCheckedChange={(v) => setValue('evaluation_require_structured_output', v)}
              />
              <Label>Structured Output</Label>
            </div>
          </div>
        </section>

        {/* Tags */}
        <section>
          <h3 className="text-sm font-semibold mb-2 text-muted-foreground uppercase tracking-wide">Tags</h3>
          <div className="flex flex-wrap gap-2 mb-2">
            {tags.map((tag, i) => (
              <span key={i} className="flex items-center gap-1 rounded-full bg-muted px-2.5 py-1 text-xs">
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
            placeholder="Add tag and press Enter"
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

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={handleClose}>Cancel</Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Saving…' : isEdit ? 'Update Colonee' : 'Create Colonee'}
          </Button>
        </div>
      </form>
    </Dialog>
  )
}
