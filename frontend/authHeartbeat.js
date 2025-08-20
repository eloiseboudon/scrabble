import { API_BASE } from './api.js'

let timer

export function startAuthHeartbeat() {
  stopAuthHeartbeat()
  timer = setInterval(async () => {
    try {
      await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        credentials: 'include'
      })
    } catch {
      // ignore
    }
  }, 12 * 60 * 1000)
}

export function stopAuthHeartbeat() {
  if (timer) {
    clearInterval(timer)
    timer = undefined
  }
}
