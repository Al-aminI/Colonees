import { apiClient } from './client'
import type { ColoneeDefinition, CreateColoneePayload, UpdateColoneePayload } from '@/types'

interface ListColoneesResponse {
  colonees: ColoneeDefinition[]
  count: number
}

export const coloneesApi = {
  list: (params?: { enabled_only?: boolean; tag?: string }) =>
    apiClient.get<ListColoneesResponse>('/colonees', { params }).then(r => r.data),

  get: (name: string) =>
    apiClient.get<ColoneeDefinition>(`/colonees/${name}`).then(r => r.data),

  create: (payload: CreateColoneePayload) =>
    apiClient.post<ColoneeDefinition>('/colonees', payload).then(r => r.data),

  update: (name: string, payload: UpdateColoneePayload) =>
    apiClient.put<ColoneeDefinition>(`/colonees/${name}`, payload).then(r => r.data),

  delete: (name: string) =>
    apiClient.delete<{ status: string; name: string }>(`/colonees/${name}`).then(r => r.data),

  enable: (name: string) =>
    apiClient.post(`/colonees/${name}/enable`).then(r => r.data),

  disable: (name: string) =>
    apiClient.post(`/colonees/${name}/disable`).then(r => r.data),
}
