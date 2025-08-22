// Define collectWords in the global scope
function collectWords(getTile, placements) {
  if (!placements || placements.length === 0) return []
  const rows = placements.map(p => p.row)
  const cols = placements.map(p => p.col)
  const sameRow = new Set(rows).size === 1
  const sameCol = new Set(cols).size === 1
  if (!sameRow && !sameCol) return []
  let horizontal = sameRow

  // orientation fix for single tile based on neighbors
  if (placements.length === 1) {
    const { row, col } = placements[0]
    const left = getTile(row, col - 1)
    const right = getTile(row, col + 1)
    const up = getTile(row - 1, col)
    const down = getTile(row + 1, col)
    const hasHoriz = left || right
    const hasVert = up || down
    if (hasVert && !hasHoriz) horizontal = false
    else if (hasHoriz && !hasVert) horizontal = true
  }

  const words = []
  const size = 15
  const key = (r, c) => `${r},${c}`
  const placementSet = new Set(placements.map(p => key(p.row, p.col)))

  if (horizontal) {
    const row = rows[0]
    let start = Math.min(...cols)
    while (start > 0 && getTile(row, start - 1)) start--
    let c = start
    let mainWord = ''
    while (c < size) {
      const tile = getTile(row, c)
      if (!tile) break
      mainWord += tile.toUpperCase()
      c++
    }
    if (mainWord) words.push(mainWord)
    for (const { row: r, col: c2 } of placements) {
      let r0 = r
      while (r0 > 0 && getTile(r0 - 1, c2)) r0--
      let rr = r0
      let word = ''
      let touchesPlaced = false
      while (rr < size) {
        const tile = getTile(rr, c2)
        if (!tile) break
        if (placementSet.has(key(rr, c2))) touchesPlaced = true
        word += tile.toUpperCase()
        rr++
      }
      if (touchesPlaced && word.length > 1) words.push(word)
    }
  } else {
    const col = cols[0]
    let start = Math.min(...rows)
    while (start > 0 && getTile(start - 1, col)) start--
    let r = start
    let mainWord = ''
    while (r < size) {
      const tile = getTile(r, col)
      if (!tile) break
      mainWord += tile.toUpperCase()
      r++
    }
    if (mainWord) words.push(mainWord)
    for (const { row: r2, col: c } of placements) {
      let c0 = c
      while (c0 > 0 && getTile(r2, c0 - 1)) c0--
      let cc = c0
      let word = ''
      let touchesPlaced = false
      while (cc < size) {
        const tile = getTile(r2, cc)
        if (!tile) break
        if (placementSet.has(key(r2, cc))) touchesPlaced = true
        word += tile.toUpperCase()
        cc++
      }
      if (touchesPlaced && word.length > 1) words.push(word)
    }
  }

  return [...new Set(words)]
}

// Expose to window object
(function() {
  window.collectWords = collectWords;
})();