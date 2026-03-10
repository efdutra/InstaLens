<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useInstagramStore } from '../stores/instagram'
import type { ScrapeRequest } from '../types/instagram'
import LoadingSpinner from './LoadingSpinner.vue'
import ProfileCard from './ProfileCard.vue'
import UserList from './UserList.vue'

const store = useInstagramStore()

const username = ref('')
const maxFollowers = ref<number | null>(50)
const maxFollowing = ref<number | null>(50)
const getFollowers = ref(true)
const getFollowing = ref(true)
const activeTab = ref<'followers' | 'following'>('followers')
const isLoggingIn = ref(false)

const hasResults = computed(() => store.profile !== null)
const showForm = computed(() => !store.isLoading && !hasResults.value)

onMounted(async () => {
  await store.checkAuthStatus()
})

const handleLogin = async () => {
  isLoggingIn.value = true
  try {
    await store.waitForLogin()
    alert('✅ Login realizado com sucesso!')
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Erro ao fazer login'
    alert('❌ ' + message)
  } finally {
    isLoggingIn.value = false
  }
}

const handleSubmit = async () => {
  if (!username.value.trim()) {
    store.error = 'Por favor, insira um username'
    return
  }

  store.clearError()

  const request: ScrapeRequest = {
    username: username.value.trim(),
    get_followers: getFollowers.value,
    get_following: getFollowing.value,
  }

  // Adiciona limites apenas se foram definidos
  if (maxFollowers.value && getFollowers.value) {
    request.max_followers = maxFollowers.value
  }

  if (maxFollowing.value && getFollowing.value) {
    request.max_following = maxFollowing.value
  }

  try {
    await store.scrapeProfile(request)
    console.log('✅ Dados extraídos com sucesso!')
  } catch (err) {
    console.error('❌ Erro ao buscar perfil:', err)
  }
}

const handleReset = async () => {
  // Limpar imagens no backend
  await store.clearBackendImages()
  
  // Limpar dados do store
  store.clearData()
  
  // Resetar formulário
  username.value = ''
  maxFollowers.value = 50
  maxFollowing.value = 50
  getFollowers.value = true
  getFollowing.value = true
  activeTab.value = 'followers'
}
</script>

<template>
  <div class="homepage">
    <!-- Hero Section + Form - Só mostra quando não está carregando e não tem resultados -->
    <template v-if="showForm">
      <div class="hero">
        <h2 class="hero__title">Instagram Crawler</h2>
        <p class="hero__subtitle">
          Extraia dados de perfis do Instagram de forma automatizada
        </p>
      </div>

      <!-- Authentication Section -->
      <div class="card auth-card">
        <div v-if="store.isLoggedIn" class="auth-status auth-status--logged">
          <span class="status-icon">✅</span>
          <span class="status-text">Sessão ativa no Instagram</span>
        </div>
        
        <div v-else class="auth-status auth-status--not-logged">
          <span class="status-icon">🔓</span>
          <span class="status-text">Você precisa fazer login no Instagram</span>
          <button 
            @click="handleLogin" 
            class="btn btn-primary btn-login"
            :disabled="isLoggingIn"
          >
            {{ isLoggingIn ? 'Aguardando login...' : 'Fazer Login' }}
          </button>
        </div>
      </div>

      <!-- Form Card -->
      <div class="card form-card">
        <form @submit.prevent="handleSubmit" class="form">
          <!-- Username Input -->
          <div class="form-group">
            <label for="username" class="form-label">Username do Instagram</label>
            <div class="input-wrapper">
              <span class="input-prefix">@</span>
              <input
                id="username"
                v-model="username"
                type="text"
                placeholder="instagram"
                class="input-with-prefix"
                required
              />
            </div>
          </div>

          <!-- Checkboxes -->
          <div class="checkbox-group">
            <label class="checkbox-label">
              <input v-model="getFollowers" type="checkbox" />
              <span>Extrair Seguidores</span>
            </label>

            <label class="checkbox-label">
              <input v-model="getFollowing" type="checkbox" />
              <span>Extrair Seguindo</span>
            </label>
          </div>

          <!-- Quantity Inputs -->
          <div class="quantity-grid">
            <div v-if="getFollowers" class="form-group">
              <label for="maxFollowers" class="form-label">Máx. Seguidores</label>
              <input
                id="maxFollowers"
                v-model.number="maxFollowers"
                type="number"
                min="1"
                placeholder="Vazio = todos"
              />
              <p class="form-hint">Deixe vazio para extrair todos</p>
            </div>

            <div v-if="getFollowing" class="form-group">
              <label for="maxFollowing" class="form-label">Máx. Seguindo</label>
              <input
                id="maxFollowing"
                v-model.number="maxFollowing"
                type="number"
                min="1"
                placeholder="Vazio = todos"
              />
              <p class="form-hint">Deixe vazio para extrair todos</p>
            </div>
          </div>

          <!-- Error Message -->
          <div v-if="store.error" class="error-message">
            <span class="error-icon">⚠️</span>
            {{ store.error }}
          </div>

          <!-- Submit Button -->
          <button 
            type="submit" 
            class="btn btn-primary btn-submit"
            :disabled="!store.isLoggedIn"
          >
            {{ store.isLoggedIn ? 'Buscar Perfil' : 'Faça login primeiro' }}
          </button>
        </form>
      </div>

      <!-- Info Footer -->
      <div class="footer-info">
        <p>⚠️ Projeto educacional. Use por sua conta e risco.</p>
      </div>
    </template>

    <!-- Loading State -->
    <div v-if="store.isLoading" class="results-section">
      <LoadingSpinner :message="store.progressMessage" />
    </div>

    <!-- Results Section -->
    <div v-else-if="hasResults" class="results-section">
      <!-- Profile Card -->
      <ProfileCard v-if="store.profile" :profile="store.profile" />

      <!-- Tabs -->
      <div v-if="store.followers.length > 0 || store.following.length > 0" class="tabs-section">
        <div class="tabs">
          <button
            v-if="store.followers.length > 0"
            class="tab"
            :class="{ active: activeTab === 'followers' }"
            @click="activeTab = 'followers'"
          >
            Seguidores ({{ store.followers.length }})
          </button>
          <button
            v-if="store.following.length > 0"
            class="tab"
            :class="{ active: activeTab === 'following' }"
            @click="activeTab = 'following'"
          >
            Seguindo ({{ store.following.length }})
          </button>
        </div>

        <!-- User Lists -->
        <div class="tab-content card">
          <UserList
            v-if="activeTab === 'followers' && store.followers.length > 0"
            :users="store.followers"
            title="Seguidores"
          />
          <UserList
            v-if="activeTab === 'following' && store.following.length > 0"
            :users="store.following"
            title="Seguindo"
          />
        </div>
      </div>

      <!-- Reset Button -->
      <div class="reset-section">
        <button @click="handleReset" class="btn btn-primary btn-reset">
          Buscar Novamente
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.homepage {
  max-width: 48rem;
  margin: 0 auto;
}

.hero {
  text-align: center;
  margin-bottom: 3rem;

  &__title {
    font-size: 2.5rem;
    color: $color-primary;
    margin-bottom: 1rem;

    @include tablet {
      font-size: 3rem;
    }
  }

  &__subtitle {
    font-size: 1.125rem;
    color: $color-text-muted;
  }
}

.auth-card {
  margin-bottom: 1.5rem;
}

.auth-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;

  .status-icon {
    font-size: 1.5rem;
  }

  .status-text {
    flex: 1;
    font-size: 0.95rem;
  }

  &--logged {
    .status-text {
      color: $color-primary;
      font-weight: 500;
    }
  }

  &--not-logged {
    .status-text {
      color: $color-text-muted;
    }
  }
}

.btn-login {
  padding: 0.75rem 2rem;
  white-space: nowrap;

  &:disabled {
    opacity: 0.6;
    cursor: wait;
  }
}

.form-card {
  margin-bottom: 2rem;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-label {
  font-size: 0.875rem;
}

.form-hint {
  font-size: 0.75rem;
  color: $color-text-disabled;
  margin-top: 0.25rem;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-prefix {
  position: absolute;
  left: 1rem;
  color: $color-text-disabled;
  pointer-events: none;
}

.input-with-prefix {
  padding-left: 2.5rem !important;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 1rem;

  @include mobile {
    flex-direction: row;
    gap: 2rem;
  }
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  user-select: none;

  span {
    color: $color-text-muted;
    transition: color 0.2s;
  }

  &:hover span {
    color: $color-primary;
  }
}

.quantity-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;

  @include mobile {
    grid-template-columns: repeat(2, 1fr);
  }
}

.btn-submit {
  width: 100%;
  padding: 1rem;
  font-size: 1rem;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none !important;
  }
}

.error-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 0.5rem;
  color: #ef4444;
  font-size: 0.875rem;

  .error-icon {
    font-size: 1rem;
  }
}

.footer-info {
  text-align: center;
  
  p {
    font-size: 0.875rem;
    color: $color-text-disabled;
  }
}

.results-section {
  margin-top: 3rem;
  animation: fadeIn 0.3s ease-in;
}

.tabs-section {
  margin-top: 2rem;
}

.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.tab {
  flex: 1;
  padding: 0.75rem 1rem;
  background: $color-card;
  border: 1px solid $color-border;
  border-radius: 0.5rem 0.5rem 0 0;
  color: $color-text-muted;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    border-color: $color-primary;
    color: $color-primary;
  }

  &.active {
    background: $color-primary;
    border-color: $color-primary;
    color: $color-bg;
  }
}

.tab-content {
  border-radius: 0 0 1rem 1rem;
  
  @include mobile {
    border-radius: 0.5rem;
  }
}

.reset-section {
  margin-top: 3rem;
  text-align: center;
}

.btn-reset {
  padding: 1rem 3rem;
  font-size: 1rem;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
