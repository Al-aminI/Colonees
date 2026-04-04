import { useQuery } from '@tanstack/react-query'
import { systemApi } from '@/api/system'

export function usePlatformStatus() {
  return useQuery({
    queryKey: ['platform', 'status'],
    queryFn: systemApi.status,
    refetchInterval: 10_000,
  })
}

export function usePlatformHealth() {
  return useQuery({
    queryKey: ['platform', 'health'],
    queryFn: systemApi.health,
    refetchInterval: 30_000,
  })
}
