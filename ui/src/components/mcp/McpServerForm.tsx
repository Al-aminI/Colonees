import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Dialog, DialogHeader } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select } from '@/components/ui/select'
import { useState, useEffect } from 'react'

export const mcpServerSchema = z.object({
  name: z.string().regex(/^[a-z0-9_-]+$/, 'Only lowercase letters, numbers, hyphens, underscores').min(2),
  transport: z.enum(['streamable_http', 'sse', 'stdio']),
  url: z.string().optional(),
  headers_json: z.string().optional(),
  command: z.string().optional(),
  args_str: z.string().optional(),
  env_json: z.string().optional(),
  specialist_types_str: z.string().optional(),
})

export type McpServerFormValues = z.infer<typeof mcpServerSchema>

interface McpServerPreset {
  id?: string
  name?: string
  display_name?: string
  description?: string
  transport?: 'streamable_http' | 'sse' | 'stdio'
  url?: string
  command?: string
  args?: string[]
  env_example?: string
  headers_example?: string
}

interface McpServerFormProps {
  open: boolean
  onClose: () => void
  onSubmit: (values: McpServerFormValues) => Promise<void>
  preset?: McpServerPreset | null
}

export function McpServerForm({ open, onClose, onSubmit, preset }: McpServerFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [jsonError, setJsonError] = useState('')

  const { register, handleSubmit, watch, reset, setValue, formState: { errors } } = useForm<McpServerFormValues>({
    resolver: zodResolver(mcpServerSchema),
    defaultValues: { transport: 'streamable_http' },
  })

  const transport = watch('transport')
  const isHttp = transport === 'streamable_http' || transport === 'sse'
  const isStdio = transport === 'stdio'

  useEffect(() => {
    if (!open || !preset) return
    reset({
      name: preset.name ?? '',
      transport: preset.transport ?? 'streamable_http',
      url: preset.url ?? '',
      headers_json: preset.headers_example ?? '',
      command: preset.command ?? '',
      args_str: preset.args?.join(' ') ?? '',
      env_json: preset.env_example ?? '',
      specialist_types_str: '',
    })
  }, [open, preset, reset])

  const handleClose = () => { reset(); setJsonError(''); onClose() }

  const handleFormSubmit = async (values: McpServerFormValues) => {
    if (values.headers_json) {
      try { JSON.parse(values.headers_json) } catch { setJsonError('Invalid JSON in headers'); return }
    }
    if (values.env_json) {
      try { JSON.parse(values.env_json) } catch { setJsonError('Invalid JSON in env'); return }
    }
    setJsonError('')
    setIsSubmitting(true)
    try {
      await onSubmit(values)
      handleClose()
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onClose={handleClose}>
      <DialogHeader
        title={preset?.display_name ? `Register ${preset.display_name} MCP Server` : 'Register MCP Server'}
        onClose={handleClose}
      />
      {preset?.description && (
        <p className="text-sm text-muted-foreground -mt-2 mb-2">{preset.description}</p>
      )}
      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
        <div>
          <Label>Name</Label>
          <Input {...register('name')} placeholder="my_mcp_server" className="mt-1" />
          {errors.name && <p className="mt-1 text-xs text-destructive">{errors.name.message}</p>}
        </div>

        <div>
          <Label>Transport</Label>
          <Select {...register('transport')} className="mt-1 w-full">
            <option value="streamable_http">Streamable HTTP</option>
            <option value="sse">SSE</option>
            <option value="stdio">STDIO</option>
          </Select>
        </div>

        {isHttp && (
          <>
            <div>
              <Label>URL</Label>
              <Input {...register('url')} placeholder="https://mcp.example.com/tools" className="mt-1" />
            </div>
            <div>
              <Label>Headers (JSON)</Label>
              <Textarea
                {...register('headers_json')}
                placeholder='{"Authorization": "Bearer sk-..."}'
                rows={3}
                className="mt-1 font-mono text-xs"
              />
              <p className="mt-1 text-xs text-muted-foreground">Optional. Auth headers — values will be masked in the UI.</p>
            </div>
          </>
        )}

        {isStdio && (
          <>
            <div>
              <Label>Command</Label>
              <Input {...register('command')} placeholder="npx" className="mt-1" />
            </div>
            <div>
              <Label>Args (space-separated)</Label>
              <Input {...register('args_str')} placeholder="-y @anthropic/mcp-server-postgres" className="mt-1" />
            </div>
            <div>
              <Label>Environment Variables (JSON)</Label>
              <Textarea
                {...register('env_json')}
                placeholder='{"API_KEY": "sk-...", "DEBUG": "true"}'
                rows={3}
                className="mt-1 font-mono text-xs"
              />
            </div>
          </>
        )}

        <div>
          <Label>Specialist Types (comma-separated, empty = all)</Label>
          <Input
            {...register('specialist_types_str')}
            placeholder="researcher, analyst"
            className="mt-1"
          />
          <p className="mt-1 text-xs text-muted-foreground">Leave empty to make available to all agent types.</p>
        </div>

        {jsonError && <p className="text-xs text-destructive">{jsonError}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={handleClose}>Cancel</Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Registering…' : 'Register Server'}
          </Button>
        </div>
      </form>
    </Dialog>
  )
}
