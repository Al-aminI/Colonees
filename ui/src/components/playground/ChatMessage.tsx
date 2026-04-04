import { cn, formatResult } from '@/lib/utils'
import { Bot, User } from 'lucide-react'

export interface ChatMessageData {
  role: 'user' | 'assistant'
  content: string
  isLoading?: boolean
}

interface ChatMessageProps {
  message: ChatMessageData
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
      <div
        className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
          isUser ? 'bg-primary text-primary-foreground' : 'bg-secondary',
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>
      <div
        className={cn(
          'max-w-[75%] rounded-lg px-4 py-2.5 text-sm',
          isUser ? 'bg-primary text-primary-foreground' : 'bg-card border border-border',
          message.isLoading && 'animate-pulse',
        )}
      >
        {message.isLoading ? (
          <span className="text-muted-foreground">Thinking…</span>
        ) : typeof message.content === 'string' &&
          !message.content.startsWith('{') &&
          !message.content.startsWith('[') ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
            {formatResult(message.content)}
          </pre>
        )}
      </div>
    </div>
  )
}
