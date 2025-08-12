<template>
  <div class="auth">
    <h1>{{ isRegister ? 'Inscription' : 'Connexion' }}</h1>
    <form @submit.prevent="submit">
      <input v-model="username" placeholder="Nom d'utilisateur" required />
      <input v-model="password" type="password" placeholder="Mot de passe" required />
      <button type="submit">{{ isRegister ? "S'inscrire" : 'Se connecter' }}</button>
    </form>
    <p>
      <a href="#" @click.prevent="toggle">
        {{ isRegister ? 'Déjà un compte ? Connectez-vous' : 'Pas de compte ? Inscrivez-vous' }}
      </a>
    </p>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['auth'])

const username = ref('')
const password = ref('')
const isRegister = ref(false)
const error = ref('')

async function submit() {
  error.value = ''
  const endpoint = isRegister.value ? 'auth/register' : 'auth/login'
  const res = await fetch(`http://localhost:8000/${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: username.value, password: password.value })
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    error.value = data.detail || 'Erreur'
    return
  }
  const data = await res.json()
  emit('auth', data.user_id)
}

function toggle() {
  isRegister.value = !isRegister.value
  error.value = ''
}
</script>

<style scoped>
.auth {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
}

.auth form {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.error {
  color: red;
}
</style>
