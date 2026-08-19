import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

// Attach token from localStorage automatically
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Redirect to login on 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  login: (username, password) =>
    api.post('/auth/login', { username, password }).then(r => r.data),
}

export const predictApi = {
  predict: (payload) => api.post('/predict', payload).then(r => r.data),
  compare: (payload) => api.post('/compare', payload).then(r => r.data),
}

export const transactionsApi = {
  list: (params = {}) => api.get('/transactions', { params }).then(r => r.data),
  get: (id) => api.get(`/transactions/${id}`).then(r => r.data),
}

export const reviewsApi = {
  create: (payload) => api.post('/reviews', payload).then(r => r.data),
}

export const statsApi = {
  get: () => api.get('/stats').then(r => r.data),
  recentAlerts: (limit = 10) =>
    api.get('/alerts/recent', { params: { limit } }).then(r => r.data),
}

export const healthApi = {
  check: () => api.get('/health').then(r => r.data),
}
