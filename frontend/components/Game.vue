<template>
  <div class="game">
    <div class="grid-menu">
      <button @click="$emit('home')">Accueil</button>
      <button @click="$emit('finish')">Terminer la partie</button>
    </div>

    <Grid ref="gridRef" :letter-points="letterPoints" @placed="$emit('placed', $event)"
      @removed="$emit('removed', $event)" @moved="$emit('moved', $event)" />

    <div class="rack" @dragover.prevent @drop="$emit('rack-drop', $event, rack.length)">
      <div v-for="(letter, idx) in rack" :key="idx" class="tile" draggable="true"
        @dragstart="$emit('drag-start', $event, idx)" @dragover.prevent @drop="$emit('rack-drop', $event, idx)">
        <span class="letter">{{ letter }}</span>
        <span class="points">{{ letterPoints[letter] }}</span>
      </div>
    </div>

    <div class="validation">
      <div class="score">
        Toi {{ score }} <br>
        Adversaire {{ score_adversaire }}
      </div>
      <button @click="$emit('clear')">
        Effacer
      </button>
      <button @click="$emit('shuffle')">
        Mélanger
      </button>
      <button v-if="tile" @click="$emit('play')">
        Jouer
      </button>
      <button v-if="!tile" @click="$emit('pass')">
        Passer
      </button>
    </div>
  </div>
</template>
<script setup>
import { defineExpose, ref } from 'vue'
import Grid from './Grid.vue'

defineProps({
  rack: { type: Array, default: () => [] },
  result: { type: String, default: '' },
  letterPoints: { type: Object, default: () => ({}) },
  score: { type: Number, default: 0 },
  score_adversaire: { type: Number, default: 0 }
})

defineEmits([
  'home', 'finish', 'placed', 'removed', 'moved',
  'rack-drop', 'drag-start', 'play', 'clear', 'shuffle', 'pass'
])

const gridRef = ref(null)

// ✅ Expose des wrappers stables
function setTile(r, c, l, lock = true) { gridRef.value?.setTile(r, c, l, lock) }
function takeBack(r, c) { return gridRef.value?.takeBack(r, c) }
function clearAll(placements) { gridRef.value?.clearAll(placements) }
function lockTiles(placements) { gridRef.value?.lockTiles(placements) }

defineExpose({ gridRef, setTile, takeBack, clearAll, lockTiles })
</script>
