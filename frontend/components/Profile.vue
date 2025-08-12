<template>
  <div class="profile">
    <h1>Profil</h1>
    <div v-if="user">
      <p><strong>ID :</strong> {{ user.user_id }}</p>
      <p><strong>Pseudo :</strong> {{ user.email }}</p>
    </div>
    <div class="actions">
      <button @click="$emit('back')">Retour</button>
      <button @click="emit('logout')">Déconnexion</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const emit = defineEmits(['back', 'logout'])
const user = ref(null)

onMounted(async () => {
  try {
    const res = await fetch('http://localhost:8000/auth/me', { credentials: 'include' })
    if (res.ok) {
      user.value = await res.json()
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

