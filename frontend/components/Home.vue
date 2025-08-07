<template>
  <div class="home">
    <h1>Scrabble</h1>
    <button @click="$emit('new-game')">Créer une nouvelle partie</button>

    <h2>Parties en cours</h2>
    <ul>
      <li v-for="game in ongoingGames" :key="game.id">
        <a href="#" @click.prevent="$emit('resume', game)">Partie {{ game.id }}</a>
      </li>
      <li v-if="ongoingGames.length === 0">Aucune</li>
    </ul>

    <h2>Parties terminées</h2>
    <ul>
      <li v-for="game in finishedGames" :key="game.id">Partie {{ game.id }}</li>
      <li v-if="finishedGames.length === 0">Aucune</li>
    </ul>

    <nav class="nav">
      <a href="#" @click.prevent="$emit('navigate', 'profile')">Profil</a>
      <a href="#" @click.prevent="$emit('navigate', 'settings')">Paramètres</a>
    </nav>
  </div>
</template>

<script setup>
defineProps({
  ongoingGames: { type: Array, default: () => [] },
  finishedGames: { type: Array, default: () => [] }
})

defineEmits(['new-game', 'resume', 'navigate'])
</script>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

nav.nav {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}
</style>
