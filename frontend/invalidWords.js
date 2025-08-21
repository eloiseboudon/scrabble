export function extractInvalidWords(detail, mainWord) {
  const words = []
  if (!detail) return words
  if (typeof detail === 'string') {
    const cross = detail.match(/Invalid cross word:\s*(\w+)/i)
    if (cross) {
      words.push(cross[1].toUpperCase())
    } else if (detail === 'Main word not in dictionary' && mainWord) {
      words.push(mainWord.toUpperCase())
    }
  } else if (detail.invalid_words && Array.isArray(detail.invalid_words)) {
    words.push(...detail.invalid_words.map(w => String(w).toUpperCase()))
  }
  return words
}

export async function showInvalidWords(alertFn, detail, mainWord) {
  const words = extractInvalidWords(detail, mainWord)
  if (words.length) {
    const msg = words.length > 1
      ? `Les mots suivants ne sont pas valides : ${words.join(', ')}`
      : `Le mot ${words[0]} n'est pas valide`
    await alertFn(msg)
  }
  return words
}

window.extractInvalidWords = extractInvalidWords;
window.showInvalidWords = showInvalidWords;