let timer

function startAuthHeartbeat() {
  stopAuthHeartbeat()
  timer = setInterval(async () => {
    try {
      const url = `${API_BASE}/auth/refresh`
      console.log('[authHeartbeat] refreshing', url)
      await fetch(url, {
        method: 'POST',
        credentials: 'include'
      })
    } catch (err) {
      console.error('[authHeartbeat] refresh failed', err)
    }
  }, 12 * 60 * 1000)
}

function stopAuthHeartbeat() {
  if (timer) {
    clearInterval(timer)
    timer = undefined
  }
}

window.startAuthHeartbeat = startAuthHeartbeat
window.stopAuthHeartbeat = stopAuthHeartbeat