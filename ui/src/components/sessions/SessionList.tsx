import { MessageSquare, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface SessionListProps {
  sessions: string[]
  selected: string | null
  onSelect: (id: string) => void
  onDelete: (id: string) => void
}

export function SessionList({ sessions, selected, onSelect, onDelete }: SessionListProps) {
  if (sessions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-40 text-muted-foreground text-sm gap-2">
        <MessageSquare className="h-8 w-8 opacity-30" />
        <p>No sessions yet. Use the Playground to start one.</p>
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {sessions.map((id) => (
        <div
          key={id}
          className={cn(
            'flex items-center gap-2 rounded-md px-3 py-2 text-sm cursor-pointer hover:bg-accent group',
            selected === id && 'bg-primary/10 text-primary',
          )}
          onClick={() => onSelect(id)}
        >
          <MessageSquare className="h-3.5 w-3.5 shrink-0 opacity-60" />
          <span className="flex-1 truncate font-mono text-xs">{id}</span>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 opacity-0 group-hover:opacity-100"
            onClick={(e) => { e.stopPropagation(); onDelete(id) }}
            title="Delete session"
          >
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>
      ))}
    </div>
  )
}
