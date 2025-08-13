export async function runBotThinking(popupRef, fn) {
  popupRef.value = { type: 'loading', message: 'Le bot réfléchit' }
  try {
    return await fn()
  } finally {
    popupRef.value = null
  }
}
