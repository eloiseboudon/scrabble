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

<script>
export default {
  name: 'Settings',
  emits: ['back'],
  data() {
    return {
      palettes: ['palette1', 'palette2', 'palette3', 'palette4', 'palette5'],
      selected: 'palette1',
      API_BASE: '/api' // Définir directement ici
    }
  },
  async mounted() {
    try {
      const res = await fetch(`${this.API_BASE}/auth/me`, { credentials: 'include' })
      if (res.ok) {
        const data = await res.json()
        this.selected = data.color_palette || 'palette1'
        document.documentElement.setAttribute('data-theme', this.selected)
      }
    } catch (err) {
      console.error('Erreur chargement palette:', err)
    }
  },
  methods: {
    async updatePalette() {
      document.documentElement.setAttribute('data-theme', this.selected)
      try {
        await fetch(`${this.API_BASE}/auth/me/palette`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ palette: this.selected })
        })
      } catch (err) {
        console.error('Erreur mise à jour palette:', err)
      }
    }
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