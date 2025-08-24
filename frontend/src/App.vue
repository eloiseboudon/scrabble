<template>
  <div class="app">
    <!-- Écran de chargement initial -->
    <div v-if="isLoading" class="loading-screen">
      <div class="loading-content">
        <div class="logo-icon">S</div>
        <h1 class="logo-text">Scrabble</h1>
        <div class="loading-spinner"></div>
        <p>Chargement en cours...</p>
      </div>
    </div>

    <!-- Écran d'erreur -->
    <div v-else-if="authError" class="error-screen">
      <h1>Erreur de connexion</h1>
      <p>{{ authError }}</p>
      <button @click="checkAuth">Réessayer</button>
    </div>

    <!-- Application principale -->
    <div v-else>
      <component 
        :is="currentView" 
        @navigate="handleNavigation"
        @login-success="onLoginSuccess"
      />
    </div>
  </div>
</template>

<script>
import Home from './components/Home.vue'
import Game from './components/Game.vue'
import Settings from './components/Settings.vue'
import Profile from './components/Profile.vue'
import Login from './components/Login.vue'
import Popup from './components/Popup.vue'

export default {
  name: 'App',
  components: {
    Home,
    Game,
    Settings,
    Profile,
    Login,
    Popup
  },
  data() {
    return {
      isLoading: true,
      authError: null,
      currentView: 'Home',
      userId: localStorage.getItem('userId')
    }
  },
  async created() {
    await this.checkAuth()
  },
  methods: {
    async checkAuth() {
      this.authError = null
      this.isLoading = true
      
      try {
        // Vérifier l'authentification
        if (this.userId) {
          const response = await apiGet(`/users/${this.userId}`)
          if (response && response.user_id) {
            this.currentView = 'Home'
            return
          }
        }
        this.currentView = 'Login'
      } catch (error) {
        console.error('Auth error:', error)
        this.authError = 'Impossible de vérifier la session. Veuillez vous reconnecter.'
        this.currentView = 'Login'
      } finally {
        this.isLoading = false
      }
    },
    handleNavigation(view) {
      this.currentView = view
    },
    onLoginSuccess(userData) {
      this.userId = userData.user_id
      localStorage.setItem('userId', this.userId)
      this.currentView = 'Home'
    }
  }
}
</script>

<style>
/* Styles globaux */
:root {
  --color-primary: #398df5;
  --color-secondary: #6c757d;
  --color-success: #28a745;
  --color-danger: #dc3545;
  --color-warning: #ffc107;
  --color-light: #f8f9fa;
  --color-dark: #343a40;
  --color-text-primary: #212529;
  --color-text-secondary: #6c757d;
  --color-title: #2c3e50;
  --color-title-gradient: linear-gradient(135deg, #398df5 0%, #2c3e50 100%);
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  line-height: 1.6;
  color: var(--color-text-primary);
  background-color: #f5f7fa;
}

/* Styles de l'application */
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Styles d'écran de chargement */
.loading-screen,
.error-screen {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #fff;
  text-align: center;
  padding: var(--spacing-lg);
}

.loading-content {
  max-width: 400px;
  width: 100%;
  padding: var(--spacing-xl);
  background: white;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
}

.logo-icon {
  width: 80px;
  height: 80px;
  background: var(--color-title-gradient);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 800;
  font-size: 2.5rem;
  box-shadow: 0 8px 20px rgba(57, 141, 245, 0.3);
  margin: 0 auto var(--spacing-lg);
}

.logo-text {
  background: var(--color-title-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 2.5rem;
  font-weight: 800;
  margin: 0 0 var(--spacing-xl) 0;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(57, 141, 245, 0.1);
  border-top: 4px solid var(--color-title);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto var(--spacing-lg);
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-content p {
  color: var(--color-text-secondary);
  margin: 0;
}

/* Styles des boutons */
button {
  background-color: var(--color-primary);
  color: white;
  border: none;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

button:hover {
  background-color: #2c7cd1;
  transform: translateY(-1px);
}

button:active {
  transform: translateY(0);
}

/* Styles des formulaires */
input, select, textarea {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid #ddd;
  border-radius: var(--radius-sm);
  font-size: 1rem;
  margin-bottom: var(--spacing-md);
  transition: border-color 0.2s ease;
}

input:focus, select:focus, textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(57, 141, 245, 0.2);
}

/* Utilitaires */
.text-center { text-align: center; }
.mt-1 { margin-top: var(--spacing-sm); }
.mt-2 { margin-top: var(--spacing-md); }
.mt-3 { margin-top: var(--spacing-lg); }
.mb-1 { margin-bottom: var(--spacing-sm); }
.mb-2 { margin-bottom: var(--spacing-md); }
.mb-3 { margin-bottom: var(--spacing-lg); }
</style>
