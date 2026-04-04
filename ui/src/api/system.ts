import { apiClient } from './client'
import type { HealthResponse, PlatformStatus } from '@/types'

export const systemApi = {
  health: () => apiClient.get<HealthResponse>('/health').then(r => r.data),
  status: () => apiClient.get<PlatformStatus>('/status').then(r => r.data),
}
