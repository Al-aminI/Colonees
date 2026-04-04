import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { workspacesApi } from '@/api/workspaces'
import type { CreateWorkspacePayload, UpdateWorkspacePayload } from '@/types'

export function useWorkspaces(params?: { enabled_only?: boolean }) {
  return useQuery({ queryKey: ['workspaces', 'list', params], queryFn: () => workspacesApi.list(params) })
}

export function useWorkspace(name: string) {
  return useQuery({ queryKey: ['workspaces', 'detail', name], queryFn: () => workspacesApi.get(name), enabled: !!name })
}

export function useCreateWorkspace() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: (p: CreateWorkspacePayload) => workspacesApi.create(p), onSuccess: () => qc.invalidateQueries({ queryKey: ['workspaces'] }) })
}

export function useUpdateWorkspace() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: ({ name, payload }: { name: string; payload: UpdateWorkspacePayload }) => workspacesApi.update(name, payload), onSuccess: () => qc.invalidateQueries({ queryKey: ['workspaces'] }) })
}

export function useDeleteWorkspace() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: (name: string) => workspacesApi.delete(name), onSuccess: () => qc.invalidateQueries({ queryKey: ['workspaces'] }) })
}

export function useToggleWorkspace() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ name, enabled }: { name: string; enabled: boolean }) =>
      enabled ? workspacesApi.enable(name) : workspacesApi.disable(name),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workspaces'] }),
  })
}
