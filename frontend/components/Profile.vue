<template>
  <div class="profile">
    <div class="profile-header">
      <h1>Mon Profil</h1>
      <p>Vos statistiques et informations personnelles</p>
    </div>

    <div class="profile-content" v-if="user">
      <!-- Section informations personnelles -->
      <div class="section-container">
        <h2 class="section-title">Informations personnelles</h2>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">Email</span>
            <span class="info-value">{{ user.email }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Pseudo</span>
            <span class="info-value">{{ user.display_name || 'Non défini' }}</span>
          </div>
          <div class="info-item avatar-picker">
            <span class="info-label">Avatar</span>
            <div class="avatar-content">
              <img
                v-if="user.avatar_url"
                :src="user.avatar_url"
                alt="avatar"
                class="avatar-img"
              />
              <div class="avatar-options">
                <img
                  v-for="a in defaultAvatars"
                  :key="a"
                  :src="a"
                  class="avatar-option"
                  @click="selectAvatar(a)"
                />
              </div>
              <input type="file" accept="image/*" @change="onFileChange" />
            </div>
          </div>
          <div class="info-item palette-picker">
            <span class="info-label">Palette</span>
            <div class="palette-options">
              <div
                v-for="p in palettes"
                :key="p.name"
                class="palette-option"
                :class="{ active: selected === p.name }"
                @click="selectPalette(p.name)"
              >
                <span
                  v-for="c in p.colors"
                  :key="c"
                  class="swatch"
                  :style="{ background: c }"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Section statistiques -->
      <div class="section-container">
        <h2 class="section-title">Statistiques de jeu</h2>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-number">{{ user.games_count || 0 }}</div>
            <div class="stat-label">Parties jouées</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ user.best_score || 0 }}</div>
            <div class="stat-label">Meilleur score</div>
          </div>
          <div class="stat-card best-word">
            <div class="stat-number">{{ user.best_word || '---' }}</div>
            <div class="stat-label">Meilleur mot</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ user.win_percentage || 0 }}%</div>
            <div class="stat-label">% victoires</div>
          </div>
        </div>
      </div>
    </div>

    <!-- État de chargement -->
    <div v-else class="loading-container">
      <div class="loading-tile">?</div>
      <p>Chargement du profil...</p>
    </div>

    <!-- Actions -->
    <div class="profile-actions">
      <button class="btn-back" @click="$emit('back')">
        ← Retour
      </button>
      <button class="btn-logout" @click="emit('logout')">
        🚪 Déconnexion
      </button>
      <button class="btn-delete" @click="deleteAccount">
        🗑️ Supprimer le compte
      </button>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'

const emit = defineEmits(['back', 'logout'])
const user = ref(null)
const palettes = [
  { name: 'palette1', colors: ['#F1D87A', '#398df5'] },
  { name: 'palette2', colors: ['#67e8f9', '#f59e0b'] },
  { name: 'palette3', colors: ['#fbbf24', '#7c3aed'] },
  { name: 'palette4', colors: ['#84cc16', '#2563eb'] },
  { name: 'palette5', colors: ['#a78bfa', '#f59e0b'] }
]
const selected = ref('palette1')
const defaultAvatars = Array.from(
  { length: 5 },
  (_, i) => `/img/icone/avatars/default${i + 1}.svg`
)

onMounted(async () => {
  try {
    const res = await fetch('http://localhost:8000/auth/me', { credentials: 'include' })
    if (res.ok) {
      user.value = await res.json()
      selected.value = user.value.color_palette || 'palette1'
      document.documentElement.setAttribute('data-theme', selected.value)
      const res2 = await fetch('http://localhost:8000/games/user/' + user.value.user_id, { credentials: 'include' })
      Object.assign(user.value, await res2.json())
    }
  } catch (err) {
    console.error('Erreur lors du chargement du profil:', err)
  }
})

function selectPalette(palette) {
  selected.value = palette
  updatePalette()
}

async function onFileChange(e) {
  const file = e.target.files[0]
  if (!file) return
  const form = new FormData()
  form.append('file', file)
  try {
    const res = await fetch('http://localhost:8000/auth/me/avatar', {
      method: 'POST',
      credentials: 'include',
      body: form
    })
    if (res.ok) {
      const data = await res.json()
      if (user.value) user.value.avatar_url = data.avatar_url
    }
  } catch (err) {
    console.error('Erreur upload avatar:', err)
  }
}

async function selectAvatar(url) {
  const form = new FormData()
  form.append('choice', url.split('/').pop())
  try {
    const res = await fetch('http://localhost:8000/auth/me/avatar', {
      method: 'POST',
      credentials: 'include',
      body: form
    })
    if (res.ok) {
      const data = await res.json()
      if (user.value) user.value.avatar_url = data.avatar_url
    }
  } catch (err) {
    console.error('Erreur sélection avatar:', err)
  }
}

async function updatePalette() {
  document.documentElement.setAttribute('data-theme', selected.value)
  try {
    await fetch('http://localhost:8000/auth/me/palette', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ palette: selected.value })
    })
    if (user.value) user.value.color_palette = selected.value
  } catch (err) {
    console.error('Erreur mise à jour palette:', err)
  }
}

async function deleteAccount() {
  const confirmed = await window.appConfirm('Êtes-vous sûr de vouloir supprimer votre compte ?')
  if (!confirmed) {
    return
  }
  try {
    await fetch('http://localhost:8000/me/deletion-request', {
      method: 'POST',
      credentials: 'include',
    })
    emit('logout')
    await window.appAlert('Demande de suppression enregistrée')
  } catch (err) {
    console.error('Erreur lors de la suppression du compte:', err)
  }
}
</script>

<style scoped>
.profile {
  background: var(--color-surface);
  backdrop-filter: blur(20px);
  border-radius: var(--radius-xl);
  padding: var(--spacing-2xl);
  box-shadow: 0 20px 40px var(--color-shadow);
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  animation: fadeIn 0.6s ease-out;
}

.profile-header {
  text-align: center;
  margin-bottom: var(--spacing-2xl);
}

.profile-header h1 {
  background: var(--color-title-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 3rem;
  font-weight: 800;
  margin-bottom: var(--spacing-md);
}

.profile-header p {
  color: var(--color-text-secondary);
  font-weight: 500;
  font-size: 1.1rem;
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.section-container {
  background: rgba(255, 255, 255, 0.4);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xl);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.section-container:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
}

.section-title {
  color: var(--color-text-primary);
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-sm);
  border-bottom: 2px solid rgba(57, 141, 245, 0.2);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-md);
}

.info-item {
  background: rgba(255, 255, 255, 0.6);
  padding: var(--spacing-lg);
  border-radius: var(--radius-md);
  transition: all 0.3s ease;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.info-item:hover {
  background: rgba(255, 255, 255, 0.8);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.info-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  transition: left 0.5s ease;
}

.info-item:hover::before {
  left: 100%;
}

.info-label {
  font-weight: 700;
  color: var(--color-title);
  font-size: 0.9rem;
  margin-bottom: var(--spacing-sm);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  font-weight: 500;
  color: var(--color-text-primary);
  font-size: 1rem;
  word-break: break-all;
}

.palette-options {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
  justify-content: center;
}

.palette-option {
  display: flex;
  gap: 2px;
  padding: 2px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  border: 2px solid transparent;
}

.palette-option.active {
  border-color: var(--color-title);
}

.avatar-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
}

.avatar-img {
  width: 64px;
  height: 64px;
  border-radius: 50%;
}

.avatar-options {
  display: flex;
  gap: var(--spacing-sm);
}

.avatar-option {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.avatar-option:hover {
  transform: scale(1.1);
}

.swatch {
  width: 20px;
  height: 20px;
  border-radius: var(--radius-xs);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: var(--spacing-lg);
}

.stat-card {
  background: var(--color-primary);
  border-radius: var(--radius-md);
  padding: var(--spacing-xl);
  text-align: center;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px var(--color-shadow);
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
  transform: rotate(45deg);
  transition: transform 0.5s ease;
}

.stat-card:hover {
  transform: translateY(-5px) scale(1.02);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.stat-card:hover::before {
  transform: rotate(45deg) translate(20px, 20px);
}

.stat-number {
  font-size: 2.5rem;
  font-weight: 800;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
  position: relative;
  z-index: 1;
}

.stat-label {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  position: relative;
  z-index: 1;
}

.best-word .stat-number {
  font-size: 1.8rem;
  letter-spacing: 2px;
  font-family: 'Courier New', monospace;
  font-weight: 700;
}

.loading-container {
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--color-text-secondary);
}

.loading-tile {
  width: 60px;
  height: 60px;
  background: var(--color-primary);
  border-radius: var(--radius-sm);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-lg);
  animation: spin 2s linear infinite;
  box-shadow: 0 4px 12px var(--color-shadow);
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.loading-container p {
  font-size: 1.1rem;
  font-weight: 500;
}

.profile-actions {
  display: flex;
  justify-content: center;
  gap: var(--spacing-lg);
  margin-top: var(--spacing-2xl);
  flex-wrap: wrap;
}

.btn-back,
.btn-logout,
.btn-delete {
  background: var(--color-secondary);
  color: white;
  border: none;
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: var(--radius-md);
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px var(--color-shadow);
  white-space: nowrap;
  min-width: 140px;
}

.btn-back:hover,
.btn-logout:hover,
.btn-delete:hover {
  background: var(--color-primary);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px var(--color-shadow);
}

.btn-back:active,
.btn-logout:active,
.btn-delete:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px var(--color-shadow);
}

.btn-logout {
  background: linear-gradient(135deg, #F6BA79, #F29C3F);
}

.btn-logout:hover {
  background: linear-gradient(135deg, #F9C68A, #F6BA79);
  box-shadow: 0 6px 20px rgba(242, 156, 63, 0.3);
}

.btn-delete {
  background: linear-gradient(135deg, #e74c3c, #c0392b);
}

.btn-delete:hover {
  background: linear-gradient(135deg, #ff6b5a, #e74c3c);
  box-shadow: 0 6px 20px rgba(231, 76, 60, 0.3);
}

.btn-back:focus,
.btn-logout:focus {
  outline: 2px solid var(--color-title);
  outline-offset: 2px;
}

/* Responsive */
@media (max-width: 768px) {
  .profile {
    padding: var(--spacing-lg);
  }

  .profile-header h1 {
    font-size: 2rem;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .profile-actions {
    flex-direction: column;
    align-items: center;
  }

  .btn-back,
  .btn-logout,
  .btn-delete {
    width: 100%;
    max-width: 200px;
  }
}

@media (max-width: 480px) {
  .profile {
    padding: var(--spacing-md);
    border-radius: 0;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .stat-card {
    padding: var(--spacing-lg);
  }

  .stat-number {
    font-size: 2rem;
  }

  .best-word .stat-number {
    font-size: 1.5rem;
  }
}
</style>
