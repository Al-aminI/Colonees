import { useState, useEffect } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { SessionList } from '@/components/sessions/SessionList'
import { MessageBubble } from '@/components/sessions/MessageBubble'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { RefreshCw } from 'lucide-react'
import {
  getStoredSessions,
  removeStoredSession,
  useSessionHistory,
  useClearSession,
} from '@/hooks/useSessions'
import { useToast } from '@/components/ui/toast'

export function SessionsPage() {
  const [sessions, setSessions] = useState<string[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const { toast } = useToast()

  const { data: history, isLoading, refetch } = useSessionHistory(selected ?? '', 100)
  const clearSession = useClearSession()

  useEffect(() => {
    setSessions(getStoredSessions())
  }, [])

  const handleDelete = async (id: string) => {
    if (!confirm('Clear this session history?')) return
    await clearSession.mutateAsync(id)
    removeStoredSession(id)
    setSessions(getStoredSessions())
    if (selected === id) setSelected(null)
    toast({ title: 'Session cleared', variant: 'info' })
  }

  return (
    <div>
      <PageHeader
        title="Sessions"
        description="View conversation history from previous Playground sessions"
      />

      <div className="grid grid-cols-[280px_1fr] gap-6 h-[calc(100vh-12rem)]">
        {/* Session list */}
        <Card className="overflow-y-auto">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Recent Sessions</CardTitle>
          </CardHeader>
          <CardContent className="p-2">
            <SessionList
              sessions={sessions}
              selected={selected}
              onSelect={setSelected}
              onDelete={handleDelete}
            />
          </CardContent>
        </Card>

        {/* History viewer */}
        <Card className="flex flex-col overflow-hidden">
          <CardHeader className="pb-2 shrink-0 flex-row items-center justify-between">
            <CardTitle className="text-sm">
              {selected ? (
                <code className="text-xs">{selected}</code>
              ) : (
                'Select a session'
              )}
            </CardTitle>
            {selected && (
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => refetch()}>
                <RefreshCw className="h-3.5 w-3.5" />
              </Button>
            )}
          </CardHeader>
          <CardContent className="flex-1 overflow-y-auto p-4">
            {!selected && (
              <p className="text-center text-sm text-muted-foreground mt-8">
                Select a session from the left panel.
              </p>
            )}
            {selected && isLoading && (
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-16" />)}
              </div>
            )}
            {selected && history && (
              <div className="space-y-4">
                {history.history.length === 0 ? (
                  <p className="text-center text-sm text-muted-foreground mt-8">No messages yet.</p>
                ) : (
                  history.history.map((turn, i) => (
                    <MessageBubble key={i} turn={turn} />
                  ))
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
