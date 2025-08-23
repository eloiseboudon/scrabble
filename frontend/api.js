const { protocol, hostname } = window.location

const isProduction = hostname === 'app-scrabble.tulip-saas.fr'
const port = isProduction ? 8001 : 8000

let API_BASE
if (isProduction) {
  API_BASE = `${protocol}//${hostname}:${port}`
} else {
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    API_BASE = `${protocol}//${hostname}:${port}`
  } else {
    API_BASE = 'http://localhost:8000'
  }
}

export async function apiGet(endpoint, options = {}) {
  return fetch(`${API_BASE}/${endpoint}`, {
    method: 'GET',
    credentials: 'include',
    ...options
  })
}

export async function apiPost(endpoint, data, options = {}) {
  const opts = {
    method: 'POST',
    credentials: 'include',
    ...options
  }
  if (data instanceof FormData) {
    opts.body = data
  } else if (data !== undefined) {
    opts.headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) }
    opts.body = JSON.stringify(data)
  }
  return fetch(`${API_BASE}/${endpoint}`, opts)
}

export { API_BASE }

if (typeof window !== 'undefined') {
  window.API_BASE = API_BASE
  window.apiGet = apiGet
  window.apiPost = apiPost
}
