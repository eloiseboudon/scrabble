<template>
  <div class="scrabble-grid">
    <div v-for="(row, rowIndex) in grid" :key="rowIndex" class="row">
      <div v-for="(cell, colIndex) in row" :key="colIndex" class="cell" :class="board[rowIndex][colIndex]"
        @dragover.prevent @drop="onDrop($event, rowIndex, colIndex)" @click="remove(rowIndex, colIndex)"
        :draggable="!!cell" @dragstart="onDragStart($event, rowIndex, colIndex)">
        <template v-if="cell">
          <span class="letter">{{ cell }}</span>
          <span class="points">{{ letterPoints[cell] }}</span>
        </template>
        <template v-else>
          {{ label(board[rowIndex][colIndex]) }}
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const { letterPoints } = defineProps({ letterPoints: { type: Object, required: true } })
const emit = defineEmits(['placed', 'removed', 'moved'])

const size = 15
const board = Array.from({ length: size }, () => Array(size).fill(''))

function mark(coords, code) {
  coords.forEach(([r, c]) => (board[r][c] = code))
}

mark(
  [
    [0, 0], [0, 7], [0, 14],
    [7, 0], [7, 14],
    [14, 0], [14, 7], [14, 14]
  ],
  'TW'
)

mark(
  [
    [1, 1], [2, 2], [3, 3], [4, 4],
    [10, 10], [11, 11], [12, 12], [13, 13],
    [1, 13], [2, 12], [3, 11], [4, 10],
    [10, 4], [11, 3], [12, 2], [13, 1]
  ],
  'DW'
)

mark(
  [
    [1, 5], [1, 9],
    [5, 1], [5, 5], [5, 9], [5, 13],
    [9, 1], [9, 5], [9, 9], [9, 13],
    [13, 5], [13, 9]
  ],
  'TL'
)

mark(
  [
    [0, 3], [0, 11],
    [2, 6], [2, 8],
    [3, 0], [3, 7], [3, 14],
    [6, 2], [6, 6], [6, 8], [6, 12],
    [7, 3], [7, 11],
    [8, 2], [8, 6], [8, 8], [8, 12],
    [11, 0], [11, 7], [11, 14],
    [12, 6], [12, 8],
    [14, 3], [14, 11]
  ],
  'DL'
)

board[7][7] = 'CENTER'

const grid = ref(Array.from({ length: size }, () => Array(size).fill('')))

function label(type) {
  switch (type) {
    case 'TW':
      return 'TW'
    case 'DW':
      return 'DW'
    case 'TL':
      return 'TL'
    case 'DL':
      return 'DL'
    case 'CENTER':
      return '★'
    default:
      return ''
  }
}

function onDrop(e, row, col) {
  if (grid.value[row][col]) return
  try {
    const data = JSON.parse(e.dataTransfer.getData('text/plain'))
    if (data.source === 'rack' && data.letter) {
      grid.value[row][col] = data.letter
      board[row][col] += " use"
      emit('placed', { index: data.index, row, col, letter: data.letter })
    } else if (data.source === 'board') {
      const letter = grid.value[data.row][data.col]
      if (!letter) return
      grid.value[data.row][data.col] = ''
      board[data.row][data.col] = board[data.row][data.col].replace(' use', '')
      grid.value[row][col] = letter
      board[row][col] += " use"
      emit('moved', { fromRow: data.row, fromCol: data.col, toRow: row, toCol: col, letter })
    }
  } catch (_) {
    /* ignore malformed drops */
  }
}

function remove(row, col) {
  const letter = grid.value[row][col]
  if (!letter) return
  grid.value[row][col] = ''
  board[row][col] = board[row][col].replace(' use', '')
  emit('removed', { row, col, letter })
}

function clearAll(placements) {
  placements.forEach(({ row, col }) => {
    if (grid.value[row][col]) {
      grid.value[row][col] = ''
      board[row][col] = board[row][col].replace(' use', '')
    }
  })
}

function onDragStart(e, row, col) {
  const letter = grid.value[row][col]
  if (!letter) return
  e.dataTransfer.setData(
    'text/plain',
    JSON.stringify({ source: 'board', row, col, letter })
  )
}

function takeBack(row, col) {
  const letter = grid.value[row][col]
  if (!letter) return null
  grid.value[row][col] = ''
  board[row][col] = board[row][col].replace(' use', '')
  return letter
}

function setTile(row, col, letter) {
  grid.value[row][col] = letter
}

defineExpose({ clearAll, takeBack, setTile })
</script>

<style scoped>
.scrabble-grid {
  display: grid;
  grid-template-rows: repeat(15, 30px);
  grid-template-columns: repeat(15, 30px);
  border: 1px solid #ccc;
}

.row {
  display: contents;
}

.cell {
  border: 1px solid #ccc;
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: bold;
  user-select: none;
  position: relative;
}

.points {
  position: absolute;
  bottom: 2px;
  right: 2px;
  font-size: 0.6rem;
  font-weight: normal;
}

.TW {
  background-color: #CB514E;
  color: #fff;
}

.DW,
.CENTER {
  background-color: #C18AB3;
  color: #fff;
}

.TL {
  background-color: #87B5D2;
  color: #fff;
}

.DL {
  background-color: #90caf9;
  color: #fff;
}

.use {
  background-color: #EBBF56;
  color: #000;
}
</style>
