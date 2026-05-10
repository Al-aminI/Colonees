import { useState, useMemo } from 'react'
import { cn } from '@/lib/utils'
import { Bot, User, GitBranch, Wrench, ChevronDown, ChevronRight, Loader2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Badge } from '@/components/ui/badge'
import type { StreamEvent } from '@/hooks/useStreamInvoke'

export interface ChatMessageData {
  role: 'user' | 'assistant'
  content: string
  isLoading?: boolean
  isStreaming?: boolean
  streamEvents?: StreamEvent[]
}

interface ChatMessageProps {
  message: ChatMessageData
}

type Segment =
  | { kind: 'routing'; colonee: string; workspace: string }
  | { kind: 'text'; content: string }
  | { kind: 'tool'; name: string; id: string; input: string }

function buildSegments(events: StreamEvent[]): Segment[] {
  const segments: Segment[] = []

  const routingEvent = events.find((e) => e.type === 'routing' && e.agent_id)
  if (routingEvent) {
    segments.push({
      kind: 'routing',
      colonee: routingEvent.colonee || 'unknown',
      workspace: routingEvent.workspace || 'none',
    })
  }

  let i = 0
  while (i < events.length) {
    const event = events[i]

    if (event.type === 'text') {
      let text = event.content || ''
      let j = i + 1
      while (j < events.length && events[j].type === 'text') {
        text += events[j].content || ''
        j++
      }
      if (text.trim()) {
        segments.push({ kind: 'text', content: text })
      }
      i = j
    } else if (event.type === 'tool_use') {
      const toolId = event.tool_id || ''
      const toolName = event.tool_name || 'unknown'
      // Collect the LAST non-empty input for this tool (final accumulated state)
      let lastInput = ''
      let j = i
      while (j < events.length && events[j].type === 'tool_use' && events[j].tool_id === toolId) {
        const inp = events[j].input
        if (inp && inp.trim() && inp !== '{}') {
          lastInput = inp
        }
        j++
      }
      segments.push({ kind: 'tool', name: toolName, id: toolId, input: lastInput })
      i = j
    } else {
      i++
    }
  }

  return segments
}

function RoutingCard({ colonee, workspace }: { colonee: string; workspace: string }) {
  return (
    <div className="mb-3 rounded-lg border border-primary/20 bg-primary/5 p-3">
      <div className="flex items-center gap-2 mb-2">
        <GitBranch className="h-3.5 w-3.5 text-primary" />
        <span className="text-xs font-semibold text-primary uppercase tracking-wide">Agent Routing</span>
      </div>
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Bot className="h-3 w-3" />
        <span className="font-medium text-foreground">{colonee}</span>
        {workspace !== 'none' && (
          <Badge variant="outline" className="text-[10px] px-1.5 py-0">{workspace}</Badge>
        )}
      </div>
    </div>
  )
}

function ToolCallCard({ name, input, isStreaming }: { name: string; input: string; isStreaming: boolean }) {
  const [expanded, setExpanded] = useState(false)
  const hasInput = input && input !== '{}' && input.trim() !== ''

  return (
    <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 overflow-hidden mb-2">
      <button
        className="flex items-center gap-2 w-full px-3 py-2 text-xs hover:bg-amber-500/10 transition-colors"
        onClick={() => setExpanded((e) => !e)}
      >
        {isStreaming
          ? <Loader2 className="h-3 w-3 text-amber-400 animate-spin shrink-0" />
          : <Wrench className="h-3 w-3 text-amber-400 shrink-0" />
        }
        <span className="font-medium text-amber-300">Tool: {name}</span>
        {isStreaming && (
          <Badge variant="warning" className="text-[10px] px-1.5 py-0 ml-auto">running</Badge>
        )}
        {!isStreaming && hasInput && (
          expanded
            ? <ChevronDown className="h-3 w-3 text-muted-foreground ml-auto shrink-0" />
            : <ChevronRight className="h-3 w-3 text-muted-foreground ml-auto shrink-0" />
        )}
      </button>
      {expanded && (
        <div className="px-3 pb-2">
          <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide mb-1">Input</p>
          {hasInput ? (
            <pre className="text-xs bg-background border border-border rounded p-2 overflow-x-auto whitespace-pre-wrap font-mono">
              {input}
            </pre>
          ) : (
            <p className="text-xs text-muted-foreground italic">No parameters</p>
          )}
        </div>
      )}
    </div>
  )
}

function TextBlock({ content }: { content: string }) {
  return (
    <div className="prose prose-sm dark:prose-invert max-w-none prose-headings:text-foreground prose-p:text-foreground/90 prose-strong:text-foreground prose-code:text-foreground prose-pre:bg-muted prose-pre:border prose-pre:border-border prose-a:text-primary prose-li:text-foreground/90 prose-img:rounded-md">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {content}
      </ReactMarkdown>
    </div>
  )
}

function ThinkingIndicator() {
  return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground py-1">
      <Loader2 className="h-3.5 w-3.5 animate-spin" />
      <span>Thinking</span>
      <span className="animate-pulse">...</span>
    </div>
  )
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'
  const events = message.streamEvents || []
  const segments = useMemo(() => buildSegments(events), [events])
  const isActive = message.isStreaming && !events.some((e) => e.type === 'done')
  const hasContent = segments.length > 0

  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
      <div
        className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
          isUser ? 'bg-primary text-primary-foreground' : 'bg-gradient-to-br from-indigo-500 to-purple-500 text-white',
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      <div className={cn('max-w-[80%] min-w-0', isUser && 'flex flex-col items-end')}>
        {isUser ? (
          <div className="rounded-2xl rounded-tr-md bg-primary text-primary-foreground px-4 py-2.5 text-sm">
            <p className="whitespace-pre-wrap">{message.content}</p>
          </div>
        ) : (message.isLoading && !(message.isStreaming ?? false)) ? (
          <div className="rounded-2xl rounded-tl-md bg-card border border-border px-5 py-4">
            <ThinkingIndicator />
          </div>
        ) : (
          <div className="rounded-2xl rounded-tl-md bg-card border border-border px-5 py-4 space-y-2">
            {!hasContent && isActive ? (
              <ThinkingIndicator />
            ) : (
              <>
                {segments.map((seg, i) => {
                  if (seg.kind === 'routing') {
                    return <RoutingCard key={`routing-${i}`} colonee={seg.colonee} workspace={seg.workspace} />
                  }
                  if (seg.kind === 'tool') {
                    return (
                      <ToolCallCard
                        key={seg.id || `tool-${i}`}
                        name={seg.name}
                        input={seg.input}
                        isStreaming={isActive ?? false}
                      />
                    )
                  }
                  if (seg.kind === 'text') {
                    return <TextBlock key={`text-${i}`} content={seg.content} />
                  }
                  return null
                })}
                {isActive && hasContent && (
                  <span className="inline-block w-1.5 h-4 bg-primary animate-pulse ml-0.5 align-text-bottom rounded-sm" />
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
