<template>
  <div class="settings">
    <h1>Paramètres</h1>
    <div class="palette-section">
      <label for="palette">Palette de couleurs</label>
      <select id="palette" v-model="selected" @change="updatePalette">
        <option v-for="p in palettes" :key="p" :value="p">{{ p }}</option>
      </select>
    </div>
    <button @click="$emit('back')">Retour</button>
  </div>
</template>

<script setup>
const { onMounted, ref } = Vue

import { API_BASE } from '../api.js'

const emit = defineEmits(['back'])
const palettes = ['palette1', 'palette2', 'palette3', 'palette4', 'palette5']
const selected = ref('palette1')

onMounted(async () => {
  try {
    const res = await fetch(`${API_BASE}/auth/me`, { credentials: 'include' })
    if (res.ok) {
      const data = await res.json()
      selected.value = data.color_palette || 'palette1'
      document.documentElement.setAttribute('data-theme', selected.value)
    }
  } catch (err) {
    console.error('Erreur chargement palette:', err)
  }
})

async function updatePalette() {
  document.documentElement.setAttribute('data-theme', selected.value)
  try {
    await fetch(`${API_BASE}/auth/me/palette`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ palette: selected.value })
    })
  } catch (err) {
    console.error('Erreur mise à jour palette:', err)
  }
}
</script>

<style scoped>
.settings {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  align-items: center;
}

.palette-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}
</style>
