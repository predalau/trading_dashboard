import axios from 'axios'
import { sysLog } from '../stores/log'

const client = axios.create({
  baseURL: '/trading/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
client.interceptors.request.use(
  (config) => {
    // Add any auth tokens here if needed
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor
client.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    sysLog('ERR', `api ${error.config?.method?.toUpperCase() || ''} ${error.config?.url || ''} ${error.response?.status || error.message}`)
    return Promise.reject(error)
  }
)

export default client
