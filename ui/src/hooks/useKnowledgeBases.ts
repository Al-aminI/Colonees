import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { knowledgeBasesApi } from '@/api/knowledgeBases'
import type { CreateKnowledgeBasePayload } from '@/types'

export function useKnowledgeBases(params?: { enabled_only?: boolean }) {
  return useQuery({ queryKey: ['kb', 'list', params], queryFn: () => knowledgeBasesApi.list(params) })
}

export function useKnowledgeBase(name: string) {
  return useQuery({ queryKey: ['kb', 'detail', name], queryFn: () => knowledgeBasesApi.get(name), enabled: !!name })
}

export function useKBFiles(name: string) {
  return useQuery({ queryKey: ['kb', 'files', name], queryFn: () => knowledgeBasesApi.listFiles(name), enabled: !!name })
}

export function useCreateKnowledgeBase() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: (p: CreateKnowledgeBasePayload) => knowledgeBasesApi.create(p), onSuccess: () => qc.invalidateQueries({ queryKey: ['kb'] }) })
}

export function useDeleteKnowledgeBase() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: (name: string) => knowledgeBasesApi.delete(name), onSuccess: () => qc.invalidateQueries({ queryKey: ['kb'] }) })
}

export function useUploadFile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ kbName, file }: { kbName: string; file: File }) => knowledgeBasesApi.uploadFile(kbName, file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['kb'] }),
  })
}

export function useDeleteKBFile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ kbName, filename }: { kbName: string; filename: string }) => knowledgeBasesApi.deleteFile(kbName, filename),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['kb'] }),
  })
}

export function useSearchKB() {
  return useMutation({
    mutationFn: ({ name, query, topK }: { name: string; query: string; topK?: number }) =>
      knowledgeBasesApi.search(name, query, topK),
  })
}
