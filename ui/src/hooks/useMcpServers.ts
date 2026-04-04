import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { mcpApi } from '@/api/mcp'
import type { CreateMcpServerPayload } from '@/types'

export function useMcpServers() {
  return useQuery({
    queryKey: ['mcp', 'list'],
    queryFn: mcpApi.list,
  })
}

export function useRegisterMcpServer() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateMcpServerPayload) => mcpApi.register(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['mcp'] }),
  })
}

export function useRemoveMcpServer() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (name: string) => mcpApi.remove(name),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['mcp'] }),
  })
}
