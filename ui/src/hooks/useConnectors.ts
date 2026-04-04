import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { connectorsApi } from '@/api/connectors'
import type { CreateConnectorPayload } from '@/types'

export function useConnectors(params?: { type?: string; workspace?: string }) {
  return useQuery({ queryKey: ['connectors', 'list', params], queryFn: () => connectorsApi.list(params) })
}

export function useConnector(name: string) {
  return useQuery({ queryKey: ['connectors', 'detail', name], queryFn: () => connectorsApi.get(name), enabled: !!name })
}

export function useCreateConnector() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (p: CreateConnectorPayload) => connectorsApi.create(p),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['connectors'] }),
  })
}

export function useDeleteConnector() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (name: string) => connectorsApi.delete(name),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['connectors'] }),
  })
}

export function useConnectConnector() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (name: string) => connectorsApi.connect(name),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['connectors'] }),
  })
}

export function useSyncConnector() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (name: string) => connectorsApi.sync(name),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['connectors'] }),
  })
}

export function useConnectorTools(name: string) {
  return useQuery({
    queryKey: ['connectors', 'tools', name],
    queryFn: () => connectorsApi.tools(name),
    enabled: !!name,
  })
}

export function useConnectorCatalog() {
  return useQuery({ queryKey: ['connectors', 'catalog'], queryFn: connectorsApi.catalog })
}

export function useConnectorCatalogCategories() {
  return useQuery({ queryKey: ['connectors', 'catalog', 'categories'], queryFn: connectorsApi.catalogCategories })
}

export function useCreateFromCatalog() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ catalogId, payload }: { catalogId: string; payload: CreateConnectorPayload }) =>
      connectorsApi.createFromCatalog(catalogId, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['connectors'] }),
  })
}
