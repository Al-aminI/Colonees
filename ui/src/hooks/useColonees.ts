import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { coloneesApi } from '@/api/colonees'
import type { CreateColoneePayload, UpdateColoneePayload } from '@/types'

export function useColoneesList(params?: { enabled_only?: boolean; tag?: string }) {
  return useQuery({
    queryKey: ['colonees', 'list', params],
    queryFn: () => coloneesApi.list(params),
  })
}

export function useColonee(name: string) {
  return useQuery({
    queryKey: ['colonees', 'detail', name],
    queryFn: () => coloneesApi.get(name),
    enabled: !!name,
  })
}

export function useCreateColonee() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateColoneePayload) => coloneesApi.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['colonees'] }),
  })
}

export function useUpdateColonee() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ name, payload }: { name: string; payload: UpdateColoneePayload }) =>
      coloneesApi.update(name, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['colonees'] }),
  })
}

export function useDeleteColonee() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (name: string) => coloneesApi.delete(name),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['colonees'] }),
  })
}

export function useToggleColonee() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ name, enabled }: { name: string; enabled: boolean }) =>
      enabled ? coloneesApi.enable(name) : coloneesApi.disable(name),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['colonees'] }),
  })
}
