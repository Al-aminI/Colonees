import { useCallback, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'

export interface StreamEvent {
  type: 'routing' | 'text' | 'tool_use' | 'tool_result' | 'done' | 'error'
  colonee?: string
  workspace?: string
  agent_id?: string
  phase?: string
  content?: string
  tool_name?: string
  tool_id?: string
  input?: string
  output?: string
  response?: string
  message?: string
}

export function useStreamInvoke() {
  const qc = useQueryClient()
  const abortRef = useRef<AbortController | null>(null)

  const streamInvoke = useCallback(
    async (
      goal: string,
      sessionId: string,
      workspace: string | undefined,
      onEvent: (event: StreamEvent) => void,
    ): Promise<void> => {
      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller

      try {
        const baseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api'
        const resp = await fetch(`${baseUrl}/invoke/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            goal,
            session_id: sessionId,
            workspace: workspace || undefined,
          }),
          signal: controller.signal,
        })

        if (!resp.ok) {
          const err = await resp.text()
          onEvent({ type: 'error', message: err || `HTTP ${resp.status}` })
          return
        }

        const reader = resp.body?.getReader()
        if (!reader) {
          onEvent({ type: 'error', message: 'No response body' })
          return
        }

        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const event: StreamEvent = JSON.parse(line.slice(6))
                onEvent(event)

                if (event.type === 'done' || event.type === 'error') {
                  // Invalidate session history when done
                  if (sessionId) {
                    qc.invalidateQueries({ queryKey: ['sessions', 'history', sessionId] })
                  }
                }
              } catch {
                // skip parse errors
              }
            }
          }
        }
      } catch (err: any) {
        if (err.name !== 'AbortError') {
          onEvent({ type: 'error', message: err.message || 'Stream failed' })
        }
      }
    },
    [qc],
  )

  const abort = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  return { streamInvoke, abort }
}
