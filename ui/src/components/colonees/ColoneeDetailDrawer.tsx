import { Dialog, DialogHeader } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { SpecialistTypeBadge } from './SpecialistTypeBadge'
import { formatRelativeTime } from '@/lib/utils'
import type { ColoneeDefinition } from '@/types'

interface ColoneeDetailDrawerProps {
  colonee: ColoneeDefinition | null
  onClose: () => void
}

export function ColoneeDetailDrawer({ colonee, onClose }: ColoneeDetailDrawerProps) {
  if (!colonee) return null

  return (
    <Dialog open={!!colonee} onClose={onClose} className="max-w-2xl">
      <DialogHeader title={colonee.display_name} onClose={onClose} />

      <div className="space-y-4 text-sm">
        <div className="flex flex-wrap gap-2">
          <SpecialistTypeBadge type={colonee.specialist_type} />
          {colonee.builtin && <Badge variant="outline">Built-in</Badge>}
          <Badge variant={colonee.enabled ? 'success' : 'secondary'}>
            {colonee.enabled ? 'Enabled' : 'Disabled'}
          </Badge>
          {colonee.tags.map(t => (
            <Badge key={t} variant="outline">{t}</Badge>
          ))}
        </div>

        <p className="text-muted-foreground">{colonee.description}</p>

        <div>
          <h3 className="font-semibold mb-1">System Prompt</h3>
          <pre className="rounded-md bg-muted p-3 text-xs overflow-x-auto whitespace-pre-wrap">{colonee.system_prompt}</pre>
        </div>

        {colonee.capabilities.length > 0 && (
          <div>
            <h3 className="font-semibold mb-1">Capabilities</h3>
            <div className="flex flex-wrap gap-1">
              {colonee.capabilities.map(c => (
                <Badge key={c} variant="secondary">{c}</Badge>
              ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <h3 className="font-semibold mb-1">Memory</h3>
            <dl className="space-y-1 text-xs text-muted-foreground">
              <div className="flex justify-between"><dt>Enabled</dt><dd>{String(colonee.memory.enabled)}</dd></div>
              <div className="flex justify-between"><dt>Strategy</dt><dd>{colonee.memory.strategy}</dd></div>
              <div className="flex justify-between"><dt>Max Size</dt><dd>{colonee.memory.max_size_mb} MB</dd></div>
            </dl>
          </div>
          <div>
            <h3 className="font-semibold mb-1">Constraints</h3>
            <dl className="space-y-1 text-xs text-muted-foreground">
              <div className="flex justify-between"><dt>Max Tool Calls</dt><dd>{colonee.constraints.max_tool_calls}</dd></div>
              <div className="flex justify-between"><dt>Max Runtime</dt><dd>{colonee.constraints.max_runtime_seconds}s</dd></div>
            </dl>
          </div>
        </div>

        {(colonee.built_in_tools.length > 0 || colonee.mcp_servers.length > 0) && (
          <div>
            <h3 className="font-semibold mb-1">Tools</h3>
            <div className="flex flex-wrap gap-1">
              {colonee.built_in_tools.map(t => (
                <Badge key={t} variant="info">{t}</Badge>
              ))}
              {colonee.mcp_servers.map(s => (
                <Badge key={s} variant="outline">MCP: {s}</Badge>
              ))}
            </div>
          </div>
        )}

        <p className="text-xs text-muted-foreground">
          Created {formatRelativeTime(colonee.created_at)} · Updated {formatRelativeTime(colonee.updated_at)}
        </p>
      </div>
    </Dialog>
  )
}
