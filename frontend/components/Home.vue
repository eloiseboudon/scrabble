<template>
  <div class="home">
    <img src="logo-scrabble.png" alt="Logo Scrabble" class="logo">
    <!-- <h1>Scrabble</h1> -->
    <div v-if="!showOptions">
      <button @click="showOptions = true">Créer une nouvelle partie</button>
    </div>
    <div v-else class="new-game-options">
      <div class="buttons">
        <button @click="inviteFriend = true">Jouer contre un ami</button>
        <button @click="vsBot">Jouer contre un bot</button>
        <button @click="cancel">Annuler</button>
      </div>

      <div v-if="inviteFriend" class="form-group">
        <input id="username" v-model="opponent" type="text" placeholder="Pseudo de l'ami" required
          class="search-friend-input" />
        <button @click="vsFriend">Inviter</button>
      </div>

    </div>
    <div id="ongoing-games" class="game-menu">
      <h2>Parties en cours</h2>
      <ul>
        <li v-for="game in ongoingGames" :key="game.id">
          <a href="#" @click.prevent="$emit('resume', game)">Partie {{ game.id }}</a>
        </li>
        <li v-if="ongoingGames.length === 0">Aucune</li>
      </ul>
    </div>
    <div id="finished-games" class="game-menu">
      <h2>Parties terminées</h2>
      <ul>
        <li v-for="game in finishedGames" :key="game.id">Partie {{ game.id }}</li>
        <li v-if="finishedGames.length === 0">Aucune</li>
      </ul>
    </div>


    <nav class="nav">
      <a href="#" @click.prevent="$emit('navigate', 'profile')">Profil</a>
      <a href="#" @click.prevent="$emit('navigate', 'settings')">Paramètres</a>
    </nav>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  ongoingGames: { type: Array, default: () => [] },
  finishedGames: { type: Array, default: () => [] }
})

const emit = defineEmits(['new-game-friend', 'new-game-bot', 'resume', 'navigate'])

const showOptions = ref(false)
const opponent = ref('')
const inviteFriend = ref(false)

function vsFriend() {
  if (opponent.value.trim() !== '') {
    emit('new-game-friend', opponent.value.trim())
    opponent.value = ''
    showOptions.value = false
  }
}

function vsBot() {
  emit('new-game-bot')
  showOptions.value = false
}

function cancel() {
  opponent.value = ''
  showOptions.value = false
}
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

.new-game-options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-items: center;
}

.new-game-options .buttons {
  display: flex;
  gap: 0.5rem;
}

img.logo {
  max-width: 200px;
}



.search-friend-input {
  background: rgba(255, 255, 255, 0.9);
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  font-size: 1rem;
  font-family: inherit;
  color: var(--color-text-primary);
  transition: all 0.3s ease;
  outline: none;
}

.search-friend-input:focus {
  border-color: var(--color-title);
  box-shadow: 0 0 0 3px rgba(57, 141, 245, 0.1);
  background: rgba(255, 255, 255, 1);
}

.search-friend-input::placeholder {
  color: var(--color-text-secondary);
}
</style>
