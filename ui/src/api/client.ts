import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 180_000,
})

apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    const message: string =
      error.response?.data?.detail ??
      error.response?.data?.message ??
      error.message ??
      'Unknown error'
    return Promise.reject(new Error(message))
  },
)
