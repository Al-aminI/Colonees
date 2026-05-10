import { useState, useRef, useEffect, useCallback } from 'react'
import { ChatMessage, type ChatMessageData } from '@/components/playground/ChatMessage'
import { ChatInput } from '@/components/playground/ChatInput'
import { MessageBubble } from '@/components/sessions/MessageBubble'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Copy, History, Plus, Trash2, X } from 'lucide-react'
import { useInvoke, addStoredSession, getStoredSessions, removeStoredSession, useSessionHistory, useClearSession } from '@/hooks/useSessions'
import { useStreamInvoke, type StreamEvent } from '@/hooks/useStreamInvoke'
import { useWorkspaces } from '@/hooks/useWorkspaces'
import { generateSessionId } from '@/lib/utils'
import { useToast } from '@/components/ui/toast'
import { cn } from '@/lib/utils'

export function PlaygroundPage() {
  const [sessionId, setSessionId] = useState(() => generateSessionId())
  const [messages, setMessages] = useState<ChatMessageData[]>([])
  const [selectedWorkspace, setSelectedWorkspace] = useState<string>('')
  const [showHistory, setShowHistory] = useState(false)
  const [historySessions, setHistorySessions] = useState<string[]>([])
  const [viewingSession, setViewingSession] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { streamInvoke, abort } = useStreamInvoke()
  const { data: workspaceData } = useWorkspaces({ enabled_only: true })
  const { toast } = useToast()
  const workspaces = workspaceData?.workspaces ?? []

  const { data: historyData, isLoading: historyLoading } = useSessionHistory(viewingSession ?? '', 100)
  const clearSession = useClearSession()

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (showHistory) setHistorySessions(getStoredSessions())
  }, [showHistory])

  const handleSend = useCallback(async (goal: string) => {
    const userMsg: ChatMessageData = { role: 'user', content: goal }
    const streamMsg: ChatMessageData = {
      role: 'assistant',
      content: '',
      isStreaming: true,
      streamEvents: [],
    }

    setMessages((prev) => {
      const next = [...prev, userMsg, streamMsg]
      return next
    })
    const msgIndex = messages.length + 1
    addStoredSession(sessionId)

    const events: StreamEvent[] = []
    let content = ''

    await streamInvoke(goal, sessionId, selectedWorkspace || undefined, (event) => {
      events.push(event)
      if (event.type === 'text' && event.content) {
        content += event.content
      }

      setMessages((prev) => {
        const next = [...prev]
        const idx = msgIndex
        if (next[idx]) {
          next[idx] = {
            role: 'assistant',
            content: content,
            isStreaming: event.type !== 'done' && event.type !== 'error',
            streamEvents: [...events],
          }
        }
        return next
      })
    })

    setMessages((prev) => {
      const next = [...prev]
      if (next[msgIndex]) {
        next[msgIndex] = {
          role: 'assistant',
          content: content,
          isStreaming: false,
          streamEvents: events.filter((e) => e.type !== 'error'),
        }
      }
      return next
    })

    const errorEvent = events.find((e) => e.type === 'error')
    if (errorEvent) {
      toast({ title: 'Request failed', description: errorEvent.message, variant: 'error' })
    }
  }, [sessionId, selectedWorkspace, streamInvoke, messages.length, toast])

  const startNewSession = () => {
    abort()
    setSessionId(generateSessionId())
    setMessages([])
    setViewingSession(null)
  }

  const loadSession = (id: string) => {
    setViewingSession(id)
  }

  const deleteSession = async (id: string) => {
    await clearSession.mutateAsync(id)
    removeStoredSession(id)
    setHistorySessions(getStoredSessions())
    if (viewingSession === id) setViewingSession(null)
    toast({ title: 'Session cleared', variant: 'info' })
  }

  return (
    <div className="flex h-[calc(100vh-6rem)] gap-0">
      {showHistory && (
        <div className="w-64 shrink-0 border-r border-border flex flex-col bg-card/50">
          <div className="flex items-center justify-between px-3 py-3 border-b border-border">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">History</span>
            <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setShowHistory(false)}>
              <X className="h-3.5 w-3.5" />
            </Button>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {historySessions.length === 0 ? (
              <p className="text-xs text-muted-foreground text-center mt-6">No past sessions</p>
            ) : (
              historySessions.map((id) => (
                <div
                  key={id}
                  className={cn(
                    'flex items-center gap-1.5 rounded-md px-2 py-1.5 text-xs cursor-pointer group',
                    viewingSession === id ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-accent',
                  )}
                  onClick={() => loadSession(id)}
                >
                  <span className="flex-1 truncate font-mono text-[10px]">{id}</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-5 w-5 opacity-0 group-hover:opacity-100 shrink-0"
                    onClick={(e) => { e.stopPropagation(); deleteSession(id) }}
                  >
                    <Trash2 className="h-2.5 w-2.5" />
                  </Button>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      <div className="flex-1 flex flex-col gap-3 p-4 min-w-0">
        <div className="flex items-center gap-2 text-xs text-muted-foreground shrink-0">
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setShowHistory((h) => !h)} title="Toggle history">
            <History className="h-3.5 w-3.5" />
          </Button>
          <Button variant="ghost" size="sm" className="h-7 text-xs gap-1" onClick={startNewSession}>
            <Plus className="h-3 w-3" /> New
          </Button>
          <code className="font-mono text-[10px] text-muted-foreground truncate max-w-[180px]">{sessionId}</code>
          <Button variant="ghost" size="icon" className="h-6 w-6"
            onClick={() => { navigator.clipboard.writeText(sessionId); toast({ title: 'Copied', variant: 'success' }) }}>
            <Copy className="h-3 w-3" />
          </Button>
          <div className="ml-auto">
            <Select value={selectedWorkspace} onChange={(e) => setSelectedWorkspace(e.target.value)} className="h-7 text-xs w-44">
              <option value="">No workspace (all agents)</option>
              {workspaces.map((w) => (<option key={w.name} value={w.name}>{w.display_name}</option>))}
            </Select>
          </div>
        </div>

        <Card className="flex-1 flex flex-col overflow-hidden">
          {viewingSession ? (
            <>
              <div className="flex items-center justify-between px-4 py-2 border-b border-border shrink-0">
                <div className="flex items-center gap-2">
                  <History className="h-3.5 w-3.5 text-muted-foreground" />
                  <code className="text-xs text-muted-foreground">{viewingSession}</code>
                </div>
                <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={() => setViewingSession(null)}>
                  Back to chat
                </Button>
              </div>
              <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
                {historyLoading ? (
                  <div className="space-y-3">
                    {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-16" />)}
                  </div>
                ) : historyData?.history.length === 0 ? (
                  <p className="text-center text-sm text-muted-foreground mt-8">No messages in this session.</p>
                ) : (
                  historyData?.history.map((turn, i) => (<MessageBubble key={i} turn={turn} />))
                )}
              </CardContent>
            </>
          ) : (
            <>
              <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-muted-foreground gap-3">
                    <div className="grid grid-cols-2 gap-2 max-w-md">
                      {[
                        'What is the current UTC time?',
                        'Fetch https://httpbin.org/json and summarize it',
                        'Query https://httpbin.org/get?test=hello and explain',
                        'What time is it and what is the IP from httpbin.org/ip?',
                      ].map((example) => (
                        <button
                          key={example}
                          className="text-left rounded-lg border border-border p-3 text-xs hover:bg-accent transition-colors"
                          onClick={() => handleSend(example)}
                        >
                          {example}
                        </button>
                      ))}
                    </div>
                    <p className="text-xs">Try an example or type your own goal below.</p>
                  </div>
                ) : (
                  messages.map((msg, i) => <ChatMessage key={i} message={msg} />)
                )}
                <div ref={messagesEndRef} />
              </CardContent>
              <div className="p-4 border-t border-border">
                <ChatInput onSend={handleSend} disabled={messages.some((m) => m.isStreaming)} />
              </div>
            </>
          )}
        </Card>
      </div>
    </div>
  )
}
