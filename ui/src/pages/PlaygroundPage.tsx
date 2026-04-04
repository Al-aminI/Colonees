import { useState, useRef, useEffect } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { ChatMessage, type ChatMessageData } from '@/components/playground/ChatMessage'
import { ChatInput } from '@/components/playground/ChatInput'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import { Copy, ExternalLink } from 'lucide-react'
import { useInvoke } from '@/hooks/useSessions'
import { useColoneesList } from '@/hooks/useColonees'
import { useWorkspaces } from '@/hooks/useWorkspaces'
import { addStoredSession } from '@/hooks/useSessions'
import { generateSessionId, formatResult } from '@/lib/utils'
import { useToast } from '@/components/ui/toast'
import { Link } from 'react-router-dom'

export function PlaygroundPage() {
  const [sessionId] = useState(() => generateSessionId())
  const [messages, setMessages] = useState<ChatMessageData[]>([])
  const [selectedColonees, setSelectedColonees] = useState<string[]>([])
  const [selectedWorkspace, setSelectedWorkspace] = useState<string>('')
  const [showColoneeFilter, setShowColoneeFilter] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const invoke = useInvoke()
  const { data: coloneeData } = useColoneesList({ enabled_only: true })
  const { data: workspaceData } = useWorkspaces({ enabled_only: true })
  const { toast } = useToast()
  const colonees = coloneeData?.colonees ?? []
  const workspaces = workspaceData?.workspaces ?? []

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (goal: string) => {
    const userMsg: ChatMessageData = { role: 'user', content: goal }
    const loadingMsg: ChatMessageData = { role: 'assistant', content: '', isLoading: true }

    setMessages(prev => [...prev, userMsg, loadingMsg])
    addStoredSession(sessionId)

    try {
      const result = await invoke.mutateAsync({
        goal,
        session_id: sessionId,
        workspace: selectedWorkspace || undefined,
        colonees: selectedColonees.length > 0 ? selectedColonees : undefined,
      })

      const content = formatResult(result.result)

      setMessages(prev => [
        ...prev.slice(0, -1),
        { role: 'assistant', content },
      ])
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Unknown error'
      setMessages(prev => [
        ...prev.slice(0, -1),
        { role: 'assistant', content: `Error: ${errMsg}` },
      ])
      toast({ title: 'Request failed', description: errMsg, variant: 'error' })
    }
  }

  const copySessionId = () => {
    navigator.clipboard.writeText(sessionId)
    toast({ title: 'Session ID copied', variant: 'success' })
  }

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)] gap-4">
      <PageHeader
        title="Playground"
        description="Submit goals to the agent swarm and see results in real time"
      />

      {/* Session info bar */}
      <div className="flex items-center gap-3 text-xs text-muted-foreground">
        <span>Session:</span>
        <code className="font-mono">{sessionId}</code>
        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={copySessionId}>
          <Copy className="h-3 w-3" />
        </Button>
        <Link to="/sessions" className="flex items-center gap-1 hover:text-foreground transition-colors">
          <ExternalLink className="h-3 w-3" /> View in Sessions
        </Link>

        {/* Workspace selector */}
        <div className="ml-auto flex items-center gap-2">
          <Select
            value={selectedWorkspace}
            onChange={(e) => setSelectedWorkspace(e.target.value)}
            className="h-7 text-xs w-40"
          >
            <option value="">All Workspaces</option>
            {workspaces.map(w => (
              <option key={w.name} value={w.name}>{w.display_name}</option>
            ))}
          </Select>

          {/* Colonee filter */}
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs"
            onClick={() => setShowColoneeFilter(o => !o)}
          >
            Colonees: {selectedColonees.length === 0 ? 'All' : selectedColonees.length + ' selected'}
          </Button>
          {showColoneeFilter && (
            <div className="absolute right-6 mt-1 z-20 rounded-md border bg-card shadow-lg p-3 min-w-[200px]">
              <div className="fixed inset-0 z-10" onClick={() => setShowColoneeFilter(false)} />
              <div className="relative z-20 space-y-1.5">
                <p className="text-[10px] uppercase tracking-wide text-muted-foreground mb-2">Filter agents</p>
                {colonees.map(c => (
                  <label key={c.name} className="flex items-center gap-2 text-xs cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedColonees.includes(c.name)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedColonees(prev => [...prev, c.name])
                        } else {
                          setSelectedColonees(prev => prev.filter(n => n !== c.name))
                        }
                      }}
                    />
                    {c.display_name}
                  </label>
                ))}
                {selectedColonees.length > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 text-[10px] w-full mt-1"
                    onClick={() => setSelectedColonees([])}
                  >
                    Clear all
                  </Button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Chat area */}
      <Card className="flex-1 flex flex-col overflow-hidden">
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground gap-3">
              <div className="grid grid-cols-2 gap-2 max-w-md">
                {[
                  'Write a Python script that reads a CSV and produces a summary report',
                  'Research the top 5 open-source LLM inference frameworks and compare them',
                  'Analyze this data and identify key trends',
                  'Create a detailed plan for building a REST API with authentication',
                ].map(example => (
                  <button
                    key={example}
                    className="text-left rounded-lg border border-border p-3 text-xs hover:bg-accent transition-colors"
                    onClick={() => handleSend(example)}
                  >
                    {example}
                  </button>
                ))}
              </div>
              <p className="text-xs">Try one of these examples or type your own goal below.</p>
            </div>
          ) : (
            messages.map((msg, i) => <ChatMessage key={i} message={msg} />)
          )}
          <div ref={messagesEndRef} />
        </CardContent>
        <div className="p-4 border-t border-border">
          <ChatInput onSend={handleSend} disabled={invoke.isPending} />
        </div>
      </Card>
    </div>
  )
}
