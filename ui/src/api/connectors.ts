import { apiClient } from './client'
import type { ConnectorDefinition, CreateConnectorPayload, ConnectorCatalogEntry, ConnectorCatalogCategory } from '@/types'

export const connectorsApi = {
  // CRUD
  list: (params?: { type?: string; workspace?: string }) =>
    apiClient.get<{ connectors: ConnectorDefinition[]; count: number }>('/connectors', { params }).then(r => r.data),
  get: (name: string) =>
    apiClient.get<ConnectorDefinition>(`/connectors/${name}`).then(r => r.data),
  create: (payload: CreateConnectorPayload) =>
    apiClient.post<ConnectorDefinition>('/connectors', payload).then(r => r.data),
  update: (name: string, payload: Partial<ConnectorDefinition>) =>
    apiClient.put<ConnectorDefinition>(`/connectors/${name}`, payload).then(r => r.data),
  delete: (name: string) =>
    apiClient.delete(`/connectors/${name}`).then(r => r.data),

  // Actions
  connect: (name: string) =>
    apiClient.post<ConnectorDefinition>(`/connectors/${name}/connect`).then(r => r.data),
  sync: (name: string) =>
    apiClient.post<ConnectorDefinition>(`/connectors/${name}/sync`).then(r => r.data),
  tools: (name: string) =>
    apiClient.get<{ connector: string; tools: string[]; count: number }>(`/connectors/${name}/tools`).then(r => r.data),

  // Catalog
  catalog: () =>
    apiClient.get<{ catalog: ConnectorCatalogEntry[]; count: number }>('/connectors/catalog').then(r => r.data),
  catalogCategories: () =>
    apiClient.get<{ categories: ConnectorCatalogCategory[] }>('/connectors/catalog/categories').then(r => r.data),
  createFromCatalog: (catalogId: string, payload: CreateConnectorPayload) =>
    apiClient.post<ConnectorDefinition>(`/connectors/from-catalog/${catalogId}`, payload).then(r => r.data),
}
