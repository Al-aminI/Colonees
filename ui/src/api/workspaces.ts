import { apiClient } from './client'
import type { WorkspaceDefinition, CreateWorkspacePayload, UpdateWorkspacePayload, InvokePayload, InvokeResponse } from '@/types'

export interface WorkspaceInvokeResponse {
  status: string
  workspace: string
  result: unknown
  session_id?: string
}

export interface WorkspaceExport {
  workspace: WorkspaceDefinition
  colonees: Record<string, unknown>[]
  knowledge_bases: Record<string, unknown>[]
  exported_at: string
  version: string
}

export const workspacesApi = {
  list: (params?: { enabled_only?: boolean }) =>
    apiClient.get<{ workspaces: WorkspaceDefinition[]; count: number }>('/workspaces', { params }).then(r => r.data),
  get: (name: string) =>
    apiClient.get<WorkspaceDefinition>(`/workspaces/${name}`).then(r => r.data),
  create: (payload: CreateWorkspacePayload) =>
    apiClient.post<WorkspaceDefinition>('/workspaces', payload).then(r => r.data),
  update: (name: string, payload: UpdateWorkspacePayload) =>
    apiClient.put<WorkspaceDefinition>(`/workspaces/${name}`, payload).then(r => r.data),
  delete: (name: string) =>
    apiClient.delete(`/workspaces/${name}`).then(r => r.data),
  enable: (name: string) =>
    apiClient.post(`/workspaces/${name}/enable`).then(r => r.data),
  disable: (name: string) =>
    apiClient.post(`/workspaces/${name}/disable`).then(r => r.data),

  invoke: (name: string, payload: InvokePayload) =>
    apiClient.post<WorkspaceInvokeResponse>(`/workspaces/${name}/invoke`, payload).then(r => r.data),

  export: (name: string) =>
    apiClient.get<WorkspaceExport>(`/workspaces/${name}/export`).then(r => r.data),

  import: (payload: Record<string, unknown>) =>
    apiClient.post<{ status: string; workspace: string }>('/workspaces/import', payload).then(r => r.data),
}
