import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2 minutes - needed for Chartink scraping
})

apiClient.interceptors.request.use((config) => {
  const sessionId = localStorage.getItem('sessionId')
  if (sessionId) {
    config.headers['X-Session-ID'] = sessionId
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('sessionId')
      window.location.href = '/auth'
    }
    return Promise.reject(error)
  }
)
