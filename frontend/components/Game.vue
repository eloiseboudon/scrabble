<template>
  <div class="game">
    <button @click="$emit('home')">Accueil</button>
    <button @click="$emit('finish')">Terminer la partie</button>
    <Grid
      @placed="$emit('placed', $event)"
      @removed="$emit('removed', $event)"
      @moved="$emit('moved', $event)"
      ref="gridRef"
      :letter-points="letterPoints"
    />
    <div class="rack" @dragover.prevent @drop="$emit('rack-drop', $event, rack.length)">
      <div
        v-for="(letter, idx) in rack"
        :key="idx"
        class="tile"
        draggable="true"
        @dragstart="$emit('drag-start', $event, idx)"
        @dragover.prevent
        @drop="$emit('rack-drop', $event, idx)"
      >
        <span class="letter">{{ letter }}</span>
        <span class="points">{{ letterPoints[letter] }}</span>
      </div>
    </div>
    <div class="validation">
      <button @click="$emit('play')">Valider le coup</button>
      <button @click="$emit('clear')">Effacer</button>
      <button @click="$emit('shuffle')">Échanger</button>
      <button @click="$emit('pass')">Passer</button>
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

