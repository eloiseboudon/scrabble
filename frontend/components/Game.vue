<template>
  <div class="game">
    <div class="grid-menu">
      <button @click="$emit('home')">Accueil</button>
      <button @click="$emit('finish')">Terminer la partie</button>
    </div>

    <Grid ref="gridRef" :letter-points="letterPoints" @placed="handlePlaced" @removed="handleRemoved"
      @moved="emit('moved', $event)" />

    <div class="rack" @dragover.prevent @drop="$emit('rack-drop', $event, rack.length)">
      <div v-for="(letter, idx) in rack" :key="idx" class="tile" draggable="true"
        @dragstart="$emit('drag-start', $event, idx)" @dragover.prevent @drop="$emit('rack-drop', $event, idx)"
        @touchstart.prevent="onTouchStart(idx, $event)">
        <span class="letter">{{ letter }}</span>
        <span class="points">{{ letterPoints[letter] }}</span>
      </div>
    </div>


    <div class="validation">
      <div class="score">
        <div class="score-line">
          <img v-if="playerAvatar" :src="playerAvatar" alt="avatar" class="avatar" />
          <span>{{ userName }} {{ score }}</span>
        </div>
        <div class="score-line">
          <img v-if="opponentAvatar" :src="opponentAvatar" alt="avatar adversaire" class="avatar" />
          <span>{{ opponentName }} {{ score_adversaire }}</span>
        </div>
      </div>
      <button @click="$emit('clear')">
        Effacer
      </button>
      <button @click="$emit('shuffle')">
        Mélanger
      </button>
      <button v-show="placements" @click="onPlay">
        Jouer <span>{{ props.wordValid ? '▶️' : '❌' }}</span>
      </button>
      <button v-show="!placements" @click="onPass">
        Passer
      </button>
    </div>
  </div>
</template>
<script setup>
import Grid from './Grid.vue'
const { onBeforeUnmount, ref } = Vue

const props = defineProps({
  rack: { type: Array, default: () => [] },
  result: { type: String, default: '' },
  letterPoints: { type: Object, default: () => ({}) },
  score: { type: Number, default: 0 },
  score_adversaire: { type: Number, default: 0 },
  wordValid: { type: Boolean, default: false },
  playerAvatar: { type: String, default: '' },
  opponentAvatar: { type: String, default: '' },
  userName: { type: String, default: '' },
  opponentName: { type: String, default: '' }
})

const emit = defineEmits([
  'home', 'finish', 'placed', 'removed', 'moved',
  'rack-drop', 'drag-start', 'play', 'clear', 'shuffle', 'pass'
])

const gridRef = ref(null)
const placements = ref(0)

// --- état de drag tactile ---
let dragging = null          // { idx, letter }
let ghostEl = null

function handlePlaced(payload) {
  placements.value++
  emit('placed', payload)
}

function handleRemoved(payload) {
  if (placements.value > 0) placements.value--
  emit('removed', payload)
}

function onPlay() {
  if (placements.value > 0) emit('play')
}

function onPass() {
  if (placements.value === 0) emit('pass')
}

// DÉMARRER DRAG TACTILE DEPUIS LE RACK
function onTouchStart(idx, ev) {
  const touch = ev.touches?.[0]
  if (!touch) {
    if (typeof window !== 'undefined') {
      window.touchDragData = { source: 'rack', letter: props.rack[idx], index: idx }
    }
    return
  }
  dragging = { idx, letter: props.rack[idx] }
  createGhost(touch.clientX, touch.clientY, props.rack[idx])

  // listeners globaux le temps du drag
  document.addEventListener('touchmove', onTouchMove, { passive: false })
  document.addEventListener('touchend', onTouchEnd, { passive: false })
}

function onTouchMove(ev) {
  const t = ev.touches?.[0]
  if (!t) return
  // Empêche le scroll pendant le drag
  ev.preventDefault()
  moveGhost(t.clientX, t.clientY)
}

function onTouchEnd(ev) {
  const t = ev.changedTouches?.[0]
  if (!t) return
  // Où a-t-on lâché ?
  const el = document.elementFromPoint(t.clientX, t.clientY)

  // 1) Sur une cellule de la grille ?
  const cell = el?.closest?.('.cell[data-row][data-col]')
  if (cell && dragging) {
    const row = Number(cell.dataset.row)
    const col = Number(cell.dataset.col)
    // pose “visuelle” immédiate via l’API exposée du Grid
    gridRef.value?.setTile(row, col, dragging.letter, false)
    placements.value++
    emit('placed', { row, col, letter: dragging.letter, blank: false })
    cleanupDrag()
    return
  }

  // 2) Sur la zone rack ? → on laisse tes events existants gérer
  const rackZone = el?.closest?.('.rack')
  if (rackZone && dragging) {
    // déclenche le drop rack existant à l’index de fin approximatif
    // Ici simple : on ajoute à la fin
    emit('rack-drop', { clientX: t.clientX, clientY: t.clientY }, props.rack.length)
  }

  cleanupDrag()
}

function createGhost(x, y, letter) {
  ghostEl = document.createElement('div')
  ghostEl.className = 'tile ghost'
  ghostEl.textContent = letter
  Object.assign(ghostEl.style, {
    position: 'fixed',
    left: '0px',
    top: '0px',
    transform: `translate(${x}px, ${y}px)`,
    pointerEvents: 'none',
    zIndex: 9999
  })
  document.body.appendChild(ghostEl)
}

function moveGhost(x, y) {
  if (!ghostEl) return
  ghostEl.style.transform = `translate(${x}px, ${y}px)`
}

function cleanupDrag() {
  dragging = null
  if (ghostEl) {
    ghostEl.remove()
    ghostEl = null
  }
  document.removeEventListener('touchmove', onTouchMove)
  document.removeEventListener('touchend', onTouchEnd)
  if (typeof window !== 'undefined') window.touchDragData = null
}

// --- wrappers existants exposés
function setTile(r, c, l, lock = true) {
  gridRef.value?.setTile(r, c, l, lock)
  if (!lock) placements.value++
}
function takeBack(r, c) {
  const letter = gridRef.value?.takeBack(r, c)
  if (letter) placements.value = Math.max(0, placements.value - 1)
  return letter
}
function clearAll(tiles) {
  gridRef.value?.clearAll(tiles)
  placements.value = Math.max(0, placements.value - (tiles?.length || placements.value))
}
function lockTiles(tiles) {
  gridRef.value?.lockTiles(tiles)
  placements.value = Math.max(0, placements.value - (tiles?.length || placements.value))
}

function getTile(r, c) {
  return gridRef.value?.getTile(r, c) || ''
}

defineExpose({ gridRef, setTile, takeBack, clearAll, lockTiles, getTile })

onBeforeUnmount(() => cleanupDrag())
</script>

<style scoped>
.score {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 0.5rem;
}

.score-line {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
}
</style>
