<template>
  <div class="scrabble-grid">
    <div
      v-for="(row, rowIndex) in grid"
      :key="rowIndex"
      class="row"
    >
      <div
        v-for="(cell, colIndex) in row"
        :key="colIndex"
        class="cell"
        @click="place(rowIndex, colIndex)"
      >
        {{ cell }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  currentLetter: {
    type: String,
    default: ''
  }
})
const emit = defineEmits(['placed'])

const grid = ref(
  Array.from({ length: 15 }, () => Array(15).fill(''))
)

function place(row, col) {
  if (props.currentLetter && grid.value[row][col] === '') {
    grid.value[row][col] = props.currentLetter
    emit('placed')
  }
}
</script>

<style scoped>
.scrabble-grid {
  display: grid;
  grid-template-rows: repeat(15, 30px);
  grid-template-columns: repeat(15, 30px);
  gap: 2px;
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
  cursor: pointer;
  user-select: none;
}
</style>
