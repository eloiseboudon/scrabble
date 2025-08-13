let timer;

export function startAuthHeartbeat() {
  stopAuthHeartbeat();
  timer = setInterval(async () => {
    try {
      await fetch('http://localhost:8000/auth/refresh', {
        method: 'POST',
        credentials: 'include'
      });
    } catch {
      // ignore
    }
  }, 12 * 60 * 1000);
}

export function stopAuthHeartbeat() {
  if (timer) {
    clearInterval(timer);
    timer = undefined;
  }
}
