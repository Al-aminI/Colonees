import { cn, formatResult } from '@/lib/utils'
import type { HistoryTurn } from '@/types'

interface MessageBubbleProps {
  turn: HistoryTurn
}

export function MessageBubble({ turn }: MessageBubbleProps) {
  const isUser = turn.role === 'user'
  const isError = turn.role === 'error'

  return (
    <div className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={cn(
          'max-w-[80%] rounded-lg px-4 py-2.5 text-sm',
          isUser && 'bg-primary text-primary-foreground',
          !isUser && !isError && 'bg-card border border-border',
          isError && 'bg-destructive/10 border border-destructive/30 text-destructive',
        )}
      >
        {turn.role !== 'user' && (
          <p className="text-[10px] font-medium uppercase tracking-wide mb-1 opacity-60">
            {turn.role}
          </p>
        )}
        {typeof turn.content === 'string' && !turn.content.startsWith('{') && !turn.content.startsWith('[') ? (
          <p className="whitespace-pre-wrap">{turn.content}</p>
        ) : (
          <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
            {formatResult(turn.content)}
          </pre>
        )}
      </div>
    </div>
  )
}
