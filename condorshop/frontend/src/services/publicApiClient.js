// frontend/src/services/publicApiClient.js
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

// Cliente PÚBLICO: no añade Authorization (JWT),
// solo maneja el session_token para carrito de invitado.
const publicApiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

publicApiClient.interceptors.request.use(
  (config) => {
    const sessionToken = localStorage.getItem('session_token')
    if (sessionToken) {
      config.headers['X-Session-Token'] = sessionToken
    }
    return config
  },
  (error) => Promise.reject(error),
)

publicApiClient.interceptors.response.use(
  (response) => {
    const sessionToken =
      response.headers['x-session-token'] ||
      response.headers['X-Session-Token'] ||
      response.headers.get?.('x-session-token') ||
      response.headers.get?.('X-Session-Token')

    if (sessionToken) {
      localStorage.setItem('session_token', sessionToken)
    }

    return response
  },
  (error) => Promise.reject(error),
)

export default publicApiClient

