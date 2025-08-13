<template>
  <div class="profile">
    <h1>Profil</h1>
    <div class="user-info" v-if="user">
      <p><strong>ID :</strong> {{ user.user_id }}</p>
      <p><strong>Email :</strong> {{ user.email }}</p>
      <p><strong>Pseudo :</strong> {{ user.display_name }}</p>
      <p><strong>Avatar :</strong> {{ user.avatar_url }}</p>
    </div>
    <div class="user-games" v-if="user">
      Nombre de parties : {{ user.games_count }}
      Meilleur score : {{ user.best_score }}
      Meilleur mot :
      {{ user.best_word }}
      Pourcentage gagné : {{ user.win_percentage }}
    </div>
    <div class="actions">
      <button @click="$emit('back')">Retour</button>
      <button @click="emit('logout')">Déconnexion</button>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'

const emit = defineEmits(['back', 'logout'])
const user = ref(null)

onMounted(async () => {
  try {
    const res = await fetch('http://localhost:8000/auth/me', { credentials: 'include' })
    if (res.ok) {
      user.value = await res.json()
      const res2 = await fetch('http://localhost:8000/games/user/' + user.value.user_id, { credentials: 'include' })
      Object.assign(user.value, await res2.json())
    }
  } catch (err) {
    // ignore errors
  }
})
</script>

<style scoped>
.actions {
  margin-top: 1rem;
  display: flex;
  gap: 0.5rem;
}
</style>
