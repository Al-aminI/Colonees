import { apiClient } from './client'
import type { SessionHistory, InvokePayload, InvokeResponse } from '@/types'

export const sessionsApi = {
  getHistory: (sessionId: string, limit?: number) =>
    apiClient
      .get<SessionHistory>(`/history/${sessionId}`, { params: { limit } })
      .then(r => r.data),

  clearHistory: (sessionId: string) =>
    apiClient.delete(`/history/${sessionId}`).then(r => r.data),

  invoke: (payload: InvokePayload) =>
    apiClient.post<InvokeResponse>('/invoke', payload).then(r => r.data),
}
