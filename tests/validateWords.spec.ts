import { collectWords } from '@/validateWords.js'

describe('collectWords', () => {
  function makeBoard() {
    return Array.from({ length: 15 }, () => Array(15).fill(''))
  }
  const getTile = (board: string[][]) => (r: number, c: number) => board[r]?.[c] || ''

  it('extends single tile with vertical neighbors', () => {
    const board = makeBoard()
    board[10][5] = 'T'
    board[11][5] = 'U'
    board[12][5] = 'E'
    const words = collectWords(getTile(board), [{ row: 12, col: 5 }])
    expect(words).toContain('TUE')
  })

  it('includes cross words formed by placements', () => {
    const board = makeBoard()
    board[10][5] = 'T'
    board[11][5] = 'U'
    board[12][4] = 'O'
    board[12][5] = 'E'
    const words = collectWords(getTile(board), [{ row: 12, col: 5 }])
    expect(words).toEqual(expect.arrayContaining(['TUE', 'OE']))
  })
})
