import { cn } from '@/lib/utils'
import { Bot, User } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { HistoryTurn } from '@/types'

interface MessageBubbleProps {
  turn: HistoryTurn
}

export function MessageBubble({ turn }: MessageBubbleProps) {
  const isUser = turn.role === 'user'
  const isError = turn.role === 'error'

  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
      <div
        className={cn(
          'flex h-7 w-7 shrink-0 items-center justify-center rounded-full',
          isUser && 'bg-primary text-primary-foreground',
          isError && 'bg-destructive/20 text-destructive',
          !isUser && !isError && 'bg-gradient-to-br from-indigo-500 to-purple-500 text-white',
        )}
      >
        {isUser ? <User className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
      </div>

      <div
        className={cn(
          'max-w-[85%] min-w-0 text-sm',
          isUser && 'flex flex-col items-end',
        )}
      >
        {isUser ? (
          <div className="rounded-2xl rounded-tr-md bg-primary text-primary-foreground px-4 py-2.5">
            <p className="whitespace-pre-wrap">{turn.content}</p>
          </div>
        ) : (
          <div className={cn(
            'rounded-2xl rounded-tl-md px-4 py-3',
            isError
              ? 'bg-destructive/10 border border-destructive/30 text-destructive'
              : 'bg-card border border-border',
          )}>
            <div className="prose prose-sm dark:prose-invert max-w-none prose-headings:text-foreground prose-p:text-foreground/90 prose-strong:text-foreground prose-code:text-foreground prose-pre:bg-muted prose-pre:border prose-pre:border-border prose-a:text-primary">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {turn.content}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
