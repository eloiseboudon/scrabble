let timer

function startAuthHeartbeat() {
  stopAuthHeartbeat()
  timer = setInterval(async () => {
    try {
      console.log('[authHeartbeat] refreshing')
      await apiPost('auth/refresh')
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
