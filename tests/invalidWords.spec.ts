import { showInvalidWords } from '@/invalidWords.js'
import { vi } from 'vitest'

describe('showInvalidWords', () => {
  it('alerts invalid main word', async () => {
    const alert = vi.fn()
    await showInvalidWords(alert, 'Main word not in dictionary', 'ABC')
    expect(alert).toHaveBeenCalledWith("Le mot ABC n'est pas valide")
  })

  it('alerts invalid cross word', async () => {
    const alert = vi.fn()
    await showInvalidWords(alert, 'Invalid cross word: DOG', '')
    expect(alert).toHaveBeenCalledWith("Le mot DOG n'est pas valide")
  })

  it('alerts multiple invalid words from detail object', async () => {
    const alert = vi.fn()
    await showInvalidWords(alert, { invalid_words: ['abc', 'def'] }, '')
    expect(alert).toHaveBeenCalledWith('Les mots suivants ne sont pas valides : ABC, DEF')
  })

  it('returns empty array and no alert for unrelated errors', async () => {
    const alert = vi.fn()
    const words = await showInvalidWords(alert, 'other error', 'ABC')
    expect(words).toEqual([])
    expect(alert).not.toHaveBeenCalled()
  })
})
