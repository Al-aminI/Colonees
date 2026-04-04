import { apiClient } from './client'
import type { McpServerConfig, CreateMcpServerPayload } from '@/types'

interface ListMcpResponse {
  servers: McpServerConfig[]
  count: number
}

export const mcpApi = {
  list: () => apiClient.get<ListMcpResponse>('/mcp/servers').then(r => r.data),
  register: (payload: CreateMcpServerPayload) =>
    apiClient.post('/mcp/servers', payload).then(r => r.data),
  remove: (name: string) =>
    apiClient.delete(`/mcp/servers/${name}`).then(r => r.data),
}
