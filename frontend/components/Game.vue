<template>
  <div class="game">
    <div class="grid-menu"><button @click="$emit('home')">Accueil</button>
      <button @click="$emit('finish')">Terminer la partie</button>
    </div>
    <Grid @placed="$emit('placed', $event)" @removed="$emit('removed', $event)" @moved="$emit('moved', $event)"
      ref="gridRef" :letter-points="letterPoints" />
    <div class="rack" @dragover.prevent @drop="$emit('rack-drop', $event, rack.length)">
      <div v-for="(letter, idx) in rack" :key="idx" class="tile" draggable="true"
        @dragstart="$emit('drag-start', $event, idx)" @dragover.prevent @drop="$emit('rack-drop', $event, idx)">
        <span class="letter">{{ letter }}</span>
        <span class="points">{{ letterPoints[letter] }}</span>
      </div>
    </div>
    <div class="validation">
      <button @click="$emit('clear')"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
          stroke-width="1.5" stroke="currentColor" class="size-6">
          <path stroke-linecap="round" stroke-linejoin="round"
            d="M15.59 14.37a6 6 0 0 1-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 0 0 6.16-12.12A14.98 14.98 0 0 0 9.631 8.41m5.96 5.96a14.926 14.926 0 0 1-5.841 2.58m-.119-8.54a6 6 0 0 0-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 0 0-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 0 1-2.448-2.448 14.9 14.9 0 0 1 .06-.312m-2.24 2.39a4.493 4.493 0 0 0-1.757 4.306 4.493 4.493 0 0 0 4.306-1.758M16.5 9a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0Z" />
        </svg>
        Effacer</button>
      <button @click="$emit('shuffle')"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
          stroke-width="1.5" stroke="currentColor" class="size-6">
          <path stroke-linecap="round" stroke-linejoin="round"
            d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
        </svg>
        Échanger</button>
      <button @click="$emit('pass')"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
          stroke-width="1.5" stroke="currentColor" class="size-6">
          <path stroke-linecap="round" stroke-linejoin="round"
            d="M3 8.689c0-.864.933-1.406 1.683-.977l7.108 4.061a1.125 1.125 0 0 1 0 1.954l-7.108 4.061A1.125 1.125 0 0 1 3 16.811V8.69ZM12.75 8.689c0-.864.933-1.406 1.683-.977l7.108 4.061a1.125 1.125 0 0 1 0 1.954l-7.108 4.061a1.125 1.125 0 0 1-1.683-.977V8.69Z" />
        </svg>
        Passer</button>
      <button @click="$emit('play')"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
          stroke-width="1.5" stroke="currentColor" class="size-6">
          <path stroke-linecap="round" stroke-linejoin="round"
            d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z" />
        </svg>
        Valider le coup</button>
      <p>{{ result }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Grid from './Grid.vue'

defineProps({
  rack: { type: Array, default: () => [] },
  result: { type: String, default: '' },
  letterPoints: { type: Object, default: () => ({}) }
})

defineEmits([
  'home',
  'finish',
  'placed',
  'removed',
  'moved',
  'rack-drop',
  'drag-start',
  'play',
  'clear',
  'shuffle',
  'pass'
])

const gridRef = ref(null)
defineExpose({ gridRef })
</script>
