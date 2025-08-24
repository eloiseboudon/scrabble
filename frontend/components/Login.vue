<template>
  <div class="auth-container">
    <div class="auth-card">
      <!-- Logo et titre -->
      <div class="auth-header">
        <div class="auth-logo">
          <div class="logo-icon">S</div>
          <h1 class="logo-text">Scrabble</h1>
        </div>
        <h2 class="auth-title">{{ isRegister ? 'Inscription' : 'Connexion' }}</h2>
        <p class="auth-subtitle">
          {{ isRegister ? 'Créez votre compte pour jouer' : 'Connectez-vous pour continuer' }}
        </p>
      </div>

      <!-- Formulaire -->
      <form @submit.prevent="submit" class="auth-form">
        <div class="form-group">
          <label for="username">Nom d'utilisateur</label>
          <input id="username" v-model="username" type="text" placeholder="Entrez votre nom d'utilisateur" required
            class="auth-input" />
        </div>

        <div class="form-group">
          <label for="password">Mot de passe</label>
          <input id="password" v-model="password" type="password" placeholder="Entrez votre mot de passe" required
            class="auth-input" />
        </div>

        <div class="form-group">
          <label>
            <input type="checkbox" v-model="rememberMe" /> Se souvenir de moi
          </label>
        </div>

        <button type="submit" class="auth-button primary">
          {{ isRegister ? "Créer mon compte" : 'Se connecter' }}
        </button>
      </form>

      <!-- Séparateur -->
      <div class="auth-divider">
        <span>ou</span>
      </div>

      <!-- Connexion Google -->
      <button class="auth-button google" @click="loginGoogle">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path
            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
          <path
            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
          <path
            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
          <path
            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
        </svg>
        Continuer avec Google
      </button>

      <!-- Basculer entre connexion et inscription -->
      <div class="auth-toggle">
        <a href="#" @click.prevent="toggle" class="toggle-link">
          {{ isRegister ? 'Déjà un compte ? Connectez-vous' : 'Pas de compte ? Inscrivez-vous' }}
        </a>
      </div>

      <!-- Message d'erreur -->
      <div v-if="error" class="auth-error">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
          <path
            d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
        </svg>
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { apiPost } from '../api.js'

const emit = defineEmits(['auth'])

const username = ref('')
const password = ref('')
const isRegister = ref(false)
const error = ref('')
const rememberMe = ref(false)

async function submit() {
  error.value = ''
  const endpoint = isRegister.value ? '/auth/register' : '/auth/login'
  try {
    const data = await apiPost(endpoint, {
      username: username.value,
      password: password.value,
      remember_me: rememberMe.value
    })
    emit('auth', data.user_id)
  } catch (err) {
    error.value = err.body?.detail || 'Erreur de connexion. Vérifiez votre connexion internet.'
  }
}

function toggle() {
  isRegister.value = !isRegister.value
  error.value = ''
}

function loginGoogle() {
  window.location.href = '/auth/google/authorize'
}
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  background: var(--color-background);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-lg);
}

.auth-card {
  background: var(--color-surface);
  backdrop-filter: blur(20px);
  border-radius: var(--radius-xl);
  padding: var(--spacing-2xl);
  box-shadow: 0 20px 40px var(--color-shadow);
  width: 100%;
  max-width: 400px;
  animation: fadeIn 0.6s ease-out;
}

.auth-header {
  text-align: center;
  margin-bottom: var(--spacing-xl);
}

.auth-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
}

.logo-icon {
  width: 50px;
  height: 50px;
  background: var(--color-title-gradient);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 800;
  font-size: 1.5rem;
  box-shadow: 0 8px 20px rgba(57, 141, 245, 0.3);
}

.logo-text {
  background: var(--color-title-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 2rem;
  font-weight: 800;
  margin: 0;
}

.auth-title {
  color: var(--color-text-primary);
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 var(--spacing-sm) 0;
}

.auth-subtitle {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  margin: 0;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.form-group label {
  color: var(--color-text-primary);
  font-weight: 600;
  font-size: 0.9rem;
}

.auth-input {
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

.auth-input:focus {
  border-color: var(--color-title);
  box-shadow: 0 0 0 3px rgba(57, 141, 245, 0.1);
  background: rgba(255, 255, 255, 1);
}

.auth-input::placeholder {
  color: var(--color-text-secondary);
}

.auth-button {
  background: var(--color-secondary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  padding: var(--spacing-md) var(--spacing-lg);
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  box-shadow: 0 4px 12px var(--color-shadow);
  font-family: inherit;
}

.auth-button:hover {
  background: var(--color-primary);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px var(--color-shadow);
}

.auth-button:active {
  transform: translateY(0);
}

.auth-button.primary {
  background: var(--color-title-gradient);
  box-shadow: 0 4px 12px rgba(57, 141, 245, 0.3);
}

.auth-button.primary:hover {
  box-shadow: 0 6px 20px rgba(57, 141, 245, 0.4);
  transform: translateY(-2px);
}

.auth-button.google {
  background: rgba(255, 255, 255, 0.9);
  color: var(--color-text-primary);
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.auth-button.google:hover {
  background: rgba(255, 255, 255, 1);
  transform: translateY(-2px);
}

.auth-divider {
  display: flex;
  align-items: center;
  margin: var(--spacing-lg) 0;
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}

.auth-divider::before,
.auth-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: rgba(0, 0, 0, 0.1);
}

.auth-divider span {
  padding: 0 var(--spacing-md);
  background: var(--color-surface);
}

.auth-toggle {
  text-align: center;
  margin-top: var(--spacing-lg);
}

.toggle-link {
  color: var(--color-title);
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s ease;
}

.toggle-link:hover {
  text-decoration: underline;
  color: var(--color-text-primary);
}

.auth-error {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  color: #dc2626;
  font-size: 0.9rem;
  margin-top: var(--spacing-lg);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.auth-error svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

/* Responsive */
@media (max-width: 480px) {
  .auth-container {
    padding: var(--spacing-md);
    align-items: flex-start;
    padding-top: var(--spacing-xl);
  }

  .auth-card {
    padding: var(--spacing-xl);
  }

  .logo-text {
    font-size: 1.5rem;
  }

  .auth-title {
    font-size: 1.25rem;
  }

  .auth-button {
    padding: var(--spacing-md);
    font-size: 0.9rem;
  }
}

/* Animation */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>