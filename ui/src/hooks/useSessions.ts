import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { sessionsApi } from '@/api/sessions'
import type { InvokePayload } from '@/types'

const STORAGE_KEY = 'colonees:sessions'

export function getStoredSessions(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

export function addStoredSession(sessionId: string) {
  const sessions = getStoredSessions()
  if (!sessions.includes(sessionId)) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify([sessionId, ...sessions].slice(0, 50)))
  }
}

export function removeStoredSession(sessionId: string) {
  const sessions = getStoredSessions().filter(s => s !== sessionId)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions))
}

export function useSessionHistory(sessionId: string, limit?: number) {
  return useQuery({
    queryKey: ['sessions', 'history', sessionId],
    queryFn: () => sessionsApi.getHistory(sessionId, limit),
    enabled: !!sessionId,
  })
}

export function useClearSession() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (sessionId: string) => sessionsApi.clearHistory(sessionId),
    onSuccess: (_data, sessionId) => {
      qc.invalidateQueries({ queryKey: ['sessions', 'history', sessionId] })
    },
  })
}

export function useInvoke() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: InvokePayload) => sessionsApi.invoke(payload),
    onSuccess: (_data, variables) => {
      if (variables.session_id) {
        qc.invalidateQueries({ queryKey: ['sessions', 'history', variables.session_id] })
      }
    },
  })
}
