import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Trash2, Globe, Terminal } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { McpServerConfig, McpTransport } from '@/types'

const transportConfig: Record<McpTransport, { label: string; className: string; icon: typeof Globe }> = {
  streamable_http: { label: 'HTTP', className: 'bg-cyan-500/20 text-cyan-400', icon: Globe },
  sse: { label: 'SSE', className: 'bg-orange-500/20 text-orange-400', icon: Globe },
  stdio: { label: 'STDIO', className: 'bg-zinc-500/20 text-zinc-400', icon: Terminal },
}

interface McpServerCardProps {
  server: McpServerConfig
  onDelete: (name: string) => void
  isDeleting?: boolean
}

export function McpServerCard({ server, onDelete, isDeleting }: McpServerCardProps) {
  const transport = transportConfig[server.transport]
  const TransportIcon = transport.icon

  return (
    <Card>
      <CardContent className="p-4 flex flex-col gap-3">
        <div className="flex items-start justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <TransportIcon className="h-4 w-4 text-muted-foreground" />
              <span className="font-semibold">{server.name}</span>
            </div>
            <span
              className={cn(
                'mt-1 inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
                transport.className,
              )}
            >
              {transport.label}
            </span>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 text-destructive hover:text-destructive"
            onClick={() => onDelete(server.name)}
            disabled={isDeleting}
            title="Remove server"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>

        {server.url && (
          <p className="text-xs text-muted-foreground font-mono truncate">{server.url}</p>
        )}
        {server.command && (
          <p className="text-xs text-muted-foreground font-mono">
            <span className="text-foreground">{server.command}</span>{' '}
            {server.args.join(' ')}
          </p>
        )}

        {server.headers && Object.keys(server.headers).length > 0 && (
          <div className="flex flex-wrap gap-1">
            {Object.keys(server.headers).map(k => (
              <Badge key={k} variant="outline" className="text-[10px]">{k}: ***</Badge>
            ))}
          </div>
        )}

        <div>
          <p className="text-xs text-muted-foreground mb-1">Available to:</p>
          <div className="flex flex-wrap gap-1">
            {server.specialist_types.length === 0 ? (
              <Badge variant="secondary" className="text-[10px]">ALL agents</Badge>
            ) : (
              server.specialist_types.map(t => (
                <Badge key={t} variant="secondary" className="text-[10px]">{t}</Badge>
              ))
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
