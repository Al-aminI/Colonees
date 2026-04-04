import { apiClient } from './client'
import type { WorkspaceDefinition, CreateWorkspacePayload, UpdateWorkspacePayload } from '@/types'

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
}
