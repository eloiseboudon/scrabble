<template>
  <div class="scrabble-grid-container">
    <div class="scrabble-grid">
      <div v-for="(row, rowIndex) in grid" :key="rowIndex" class="row">
        <div v-for="(cell, colIndex) in row" :key="colIndex" class="cell"
          :class="[board[rowIndex][colIndex], { 'has-letter': !!cell }]" @dragover.prevent
          @drop="onDrop($event, rowIndex, colIndex)" @click="remove(rowIndex, colIndex)"
          :draggable="!!cell && !locked[rowIndex][colIndex]" @dragstart="onDragStart($event, rowIndex, colIndex)"
          @touchend.prevent="onTouchEnd(rowIndex, colIndex)" @touchmove.prevent :data-row="rowIndex"
          :data-col="colIndex">
          <template v-if="cell">
            <span class="letter">{{ cell.toUpperCase() }}</span>
            <span class="points">{{ cell === cell.toLowerCase() ? 0 : letterPoints[cell.toUpperCase()] }}</span>
          </template>
          <template v-else>
            <span class="label">{{ label(board[rowIndex][colIndex]) }}</span>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const { letterPoints } = defineProps({ letterPoints: { type: Object, required: true } })
const emit = defineEmits(['placed', 'removed', 'moved'])

const size = 15

// ✅ board RÉACTIF
const boardRef = ref(Array.from({ length: size }, () => Array(size).fill('')))
const board = computed(() => boardRef.value)

function mark(coords, code) { coords.forEach(([r, c]) => (boardRef.value[r][c] = code)) }

mark([[0, 0], [0, 7], [0, 14], [7, 0], [7, 14], [14, 0], [14, 7], [14, 14]], 'TW')
mark([[1, 1], [2, 2], [3, 3], [4, 4], [10, 10], [11, 11], [12, 12], [13, 13], [1, 13], [2, 12], [3, 11], [4, 10], [10, 4], [11, 3], [12, 2], [13, 1]], 'DW')
mark([[1, 5], [1, 9], [5, 1], [5, 5], [5, 9], [5, 13], [9, 1], [9, 5], [9, 9], [9, 13], [13, 5], [13, 9]], 'TL')
mark([[0, 3], [0, 11], [2, 6], [2, 8], [3, 0], [3, 7], [3, 14], [6, 2], [6, 6], [6, 8], [6, 12], [7, 3], [7, 11], [8, 2], [8, 6], [8, 8], [8, 12], [11, 0], [11, 7], [11, 14], [12, 6], [12, 8], [14, 3], [14, 11]], 'DL')
boardRef.value[7][7] = 'CENTER'

const grid = ref(Array.from({ length: size }, () => Array(size).fill('')))
const locked = ref(Array.from({ length: size }, () => Array(size).fill(false)))

function label(type) {
  switch (type) {
    case 'TW': return 'TW'
    case 'DW': return 'DW'
    case 'TL': return 'TL'
    case 'DL': return 'DL'
    case 'CENTER': return '★'
    default: return ''
  }
}

function onDrop(e, row, col) {
  if (grid.value[row][col]) return
  try {
    const data = JSON.parse(e.dataTransfer.getData('text/plain'))
    if (data.source === 'rack' && data.letter) {
      grid.value[row][col] = data.letter
      locked.value[row][col] = false
      emit('placed', {
        row,
        col,
        letter: data.letter,
        from: 'rack',
        rackIndex: data.index,
        ...(data.letter === '*' ? { blank: true } : {})
      })
    } else if (data.source === 'board') {
      if (locked.value[data.row][data.col]) return
      const letter = grid.value[data.row][data.col]
      if (!letter) return
      grid.value[data.row][data.col] = ''
      locked.value[data.row][data.col] = false
      grid.value[row][col] = letter
      locked.value[row][col] = false
      emit('moved', { from: { row: data.row, col: data.col }, to: { row, col }, letter })
    }
  } catch { }
}

function remove(row, col) {
  if (locked.value[row][col]) return
  const letter = grid.value[row][col]
  if (!letter) return
  grid.value[row][col] = ''
  locked.value[row][col] = false
  emit('removed', { row, col, letter })
}

function clearAll(placements) {
  placements.forEach(({ row, col }) => {
    if (grid.value[row][col] && !locked.value[row][col]) {
      grid.value[row][col] = ''
      locked.value[row][col] = false
    }
  })
}

function onDragStart(e, row, col) {
  const letter = grid.value[row][col]
  if (!letter || locked.value[row][col]) return
  e.dataTransfer.setData('text/plain', JSON.stringify({ source: 'board', row, col, letter }))
}

function onTouchEnd(row, col) {
  const data = typeof window !== 'undefined' ? window.touchDragData : null
  if (!data || grid.value[row][col]) return
  if (data.source === 'rack' && data.letter) {
    grid.value[row][col] = data.letter
    locked.value[row][col] = false
    emit('placed', {
      row,
      col,
      letter: data.letter,
      from: 'rack',
      rackIndex: data.index,
      ...(data.letter === '*' ? { blank: true } : {})
    })
  }
  if (typeof window !== 'undefined') window.touchDragData = null
}

function takeBack(row, col) {
  const letter = grid.value[row][col]
  if (!letter || locked.value[row][col]) return null
  grid.value[row][col] = ''
  locked.value[row][col] = false
  return letter
}

function setTile(row, col, letter, lock = true) {
  grid.value[row][col] = letter
  locked.value[row][col] = lock
}

function lockTiles(placements) {
  placements.forEach(({ row, col }) => {
    if (grid.value[row][col]) locked.value[row][col] = true
  })
}

function getTile(row, col) {
  return grid.value[row][col]
}

defineExpose({ clearAll, takeBack, setTile, lockTiles, getTile })
</script>

<style scoped>
/* Variables CSS pour les dimensions */
:root {
  --cell-size: clamp(20px, 4.5vw, 32px);
  --grid-gap: 0;
  --grid-border-width: clamp(1px, 0.2vw, 2px);
}

/* Conteneur principal de la grille */
.scrabble-grid-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: var(--spacing-md, 1rem);
  background: rgba(255, 255, 255, 0.5);
  border-radius: var(--radius-lg, 16px);
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.03);
  margin: var(--spacing-lg, 1.5rem) auto;
  width: fit-content;
  max-width: 100%;
}

/* Grille 15x15 */
.scrabble-grid {
  display: grid;
  grid-template-rows: repeat(15, var(--cell-size));
  grid-template-columns: repeat(15, var(--cell-size));
  gap: var(--grid-gap);
  background: #999;
  border: var(--grid-border-width) solid #666;
  /* border-radius: var(--radius-sm, 8px); */
  padding: var(--grid-gap);
  width: fit-content;
  aspect-ratio: 1;
}

/* Lignes (pour compatibilité) */
.row {
  display: contents;
}

/* Cases individuelles */
.cell {
  width: var(--cell-size);
  height: var(--cell-size);
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: bold;
  user-select: none;
  position: relative;
  border-radius: 2px;
  transition: all 0.3s ease;
  cursor: pointer;
  background: #f5f5dc;
  color: #333;
  font-size: clamp(8px, 1.8vw, 12px);
  border: 0.5px solid #666;
}

/* États de hover et active */
.cell:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  z-index: 1;
}

.cell:active {
  transform: scale(0.95);
}

/* Lettres et points */
.letter {
  font-weight: 700;
  font-size: clamp(10px, 2.2vw, 16px);
  color: #333;
  /* text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8); */
}

.points {
  position: absolute;
  bottom: 0px;
  right: 0px;
  font-size: clamp(5px, 1vw, 8px);
  font-weight: 600;
  color: #444;
  /* background: rgba(255, 255, 255, 0.8); */
  /* border-radius: 50%; */
  width: clamp(8px, 1.8vw, 12px);
  height: clamp(8px, 1.8vw, 12px);
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

/* Labels des cases spéciales */
.label {
  font-size: 10px;
  font-weight: 700;
  text-align: center;
  line-height: 1;
}

/* Cases spéciales - Couleurs originales */
.TW {
  background: linear-gradient(to bottom right, #CB514E, #A94442);
  color: #fff;
  box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.2);
}

.DW {
  background: linear-gradient(to bottom right, #C18AB3, #9C6F9E);
  color: #fff;
  box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.2);
}

.CENTER {
  background: linear-gradient(to bottom right, #C18AB3, #9C6F9E);
  color: #fff;
  box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.2);
}

.TL {
  background: linear-gradient(to bottom right, #87B5D2, #5C8EAB);
  color: #fff;
  box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.2);
}

.DL {
  background: linear-gradient(to bottom right, #90caf9, #5a9bdc);
  color: #fff;
  box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.2);
}

/* Cases avec lettres posées */
.has-letter {
  background: linear-gradient(to bottom right, #EBBF56, #D6A63B) !important;
  color: #000 !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15), inset 0 1px 2px rgba(255, 255, 255, 0.5) !important;
  cursor: grab;
}

.has-letter:active {
  cursor: grabbing;
}

/* Responsive pour tablettes */
@media (max-width: 768px) {
  :root {
    --cell-size: clamp(18px, 5.5vw, 28px);
    --grid-gap: 0;
    --grid-border-width: 1px;
  }

  .scrabble-grid-container {
    padding: var(--spacing-sm, 0.5rem);
    margin: var(--spacing-md, 1rem) auto;
    width: 100%;
    max-width: 100%;
  }

  .scrabble-grid {
    max-width: 100%;
  }

  .letter {
    font-size: 12px;
  }

  .points {
    bottom: 1px;
    right: 1px;
    font-size: 10px;
    width: 10px;
    height: 10px;
  }

  .label {
    font-size: 10px;
  }
}

/* Responsive pour mobiles - GRILLE 100% WIDTH SANS BORDURES NI MARGES */
@media (max-width: 480px) {
  :root {
    --cell-size: calc(100vw / 15);
    --grid-gap: 0;
    --grid-border-width: 0px;
  }

  .scrabble-grid-container {
    padding: 0;
    margin: 0;
    width: 100vw;
    max-width: 100vw;
    border-radius: 0;
    background: transparent;
    box-shadow: none;
  }

  .scrabble-grid {
    padding: 0;
    width: 100vw;
    max-width: 100vw;
    border: none;
    border-radius: 0;
    background: transparent;
  }

  .cell {
    border-radius: 0;
    border: 0.5px solid #ccc;
  }

  .letter {
    font-size: 12px;
  }

  .points {
    font-size: 9px;
    width: clamp(6px, 1.5vw, 10px);
    height: clamp(6px, 1.5vw, 10px);
    right: 0px;
  }

  .label {
    font-size: 10px;
  }
}

/* Amélioration des transitions */
.cell {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.cell:hover {
  transition-duration: 0.1s;
}

/* Effet de glissement lors du drag & drop */
.cell[draggable="true"] {
  cursor: grab;
}

.cell[draggable="true"]:active {
  cursor: grabbing;
  transform: scale(1.1) rotate(2deg);
  z-index: 10;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
}

/* Animation pour les nouvelles lettres posées */
@keyframes letterPlace {
  0% {
    transform: scale(0) rotate(180deg);
    opacity: 0;
  }

  50% {
    transform: scale(1.2) rotate(0deg);
  }

  100% {
    transform: scale(1) rotate(0deg);
    opacity: 1;
  }
}

.has-letter .letter {
  animation: letterPlace 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* Effet de focus pour l'accessibilité */
.cell:focus {
  outline: 2px solid var(--color-title, #398df5);
  outline-offset: 2px;
  z-index: 2;
}
</style>