import { apiClient } from './client'
import type { KnowledgeBaseDefinition, CreateKnowledgeBasePayload, KBFileInfo, KBSearchResult } from '@/types'

export const knowledgeBasesApi = {
  list: (params?: { enabled_only?: boolean }) =>
    apiClient.get<{ knowledge_bases: KnowledgeBaseDefinition[]; count: number }>('/knowledge-bases', { params }).then(r => r.data),
  get: (name: string) =>
    apiClient.get<KnowledgeBaseDefinition>(`/knowledge-bases/${name}`).then(r => r.data),
  create: (payload: CreateKnowledgeBasePayload) =>
    apiClient.post<KnowledgeBaseDefinition>('/knowledge-bases', payload).then(r => r.data),
  update: (name: string, payload: Partial<KnowledgeBaseDefinition>) =>
    apiClient.put<KnowledgeBaseDefinition>(`/knowledge-bases/${name}`, payload).then(r => r.data),
  delete: (name: string) =>
    apiClient.delete(`/knowledge-bases/${name}`).then(r => r.data),
  uploadFile: (name: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return apiClient.post(`/knowledge-bases/${name}/upload`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
  },
  deleteFile: (name: string, filename: string) =>
    apiClient.delete(`/knowledge-bases/${name}/files/${encodeURIComponent(filename)}`).then(r => r.data),
  listFiles: (name: string) =>
    apiClient.get<{ files: KBFileInfo[]; count: number }>(`/knowledge-bases/${name}/files`).then(r => r.data),
  search: (name: string, query: string, topK = 5) =>
    apiClient.post<{ results: KBSearchResult[]; query: string; knowledge_base: string }>(`/knowledge-bases/${name}/search`, { query, top_k: topK }).then(r => r.data),
}
