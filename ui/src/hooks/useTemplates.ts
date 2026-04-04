import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { templatesApi } from '@/api/templates'

export function useTemplates(category?: string) {
  return useQuery({ queryKey: ['templates', 'list', category], queryFn: () => templatesApi.list(category) })
}

export function useTemplateCategories() {
  return useQuery({ queryKey: ['templates', 'categories'], queryFn: templatesApi.categories })
}

export function useTemplate(name: string) {
  return useQuery({ queryKey: ['templates', 'detail', name], queryFn: () => templatesApi.get(name), enabled: !!name })
}

export function useApplyTemplate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (name: string) => templatesApi.apply(name),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['workspaces'] })
      qc.invalidateQueries({ queryKey: ['colonees'] })
      qc.invalidateQueries({ queryKey: ['kb'] })
    },
  })
}
