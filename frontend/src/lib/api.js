import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || 'https://devintel-backend.onrender.com'

const client = axios.create({
  baseURL: BASE,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.response.use(
  (res) => res,
  (err) => {
    console.warn('API Error:', err.message)
    return Promise.reject(err)
  }
)

export const predictChurn = (profile) => client.post('/predict/churn', profile)
export const predictCareer = (profile) => client.post('/predict/career', profile)
export const searchSimilar = (query) => client.post('/search/similar', { query })
export const getClusters = () => client.get('/data/clusters')
export const getForecast = (tech) => client.get(`/data/forecast/${tech}`)

export default client
