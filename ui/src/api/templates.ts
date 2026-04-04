import { apiClient } from './client'
import type { UseCaseTemplate, TemplateCategory, TemplateApplyResult } from '@/types'

export const templatesApi = {
  list: (category?: string) =>
    apiClient.get<{ templates: UseCaseTemplate[]; count: number }>('/templates', { params: category ? { category } : undefined }).then(r => r.data),
  categories: () =>
    apiClient.get<{ categories: TemplateCategory[] }>('/templates/categories').then(r => r.data),
  get: (name: string) =>
    apiClient.get<UseCaseTemplate>(`/templates/${name}`).then(r => r.data),
  apply: (name: string) =>
    apiClient.post<TemplateApplyResult>(`/templates/${name}/apply`).then(r => r.data),
}
