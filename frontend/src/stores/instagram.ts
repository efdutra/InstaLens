import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ProfileData, User, ScrapeRequest, ScrapeResponse, ApiError } from '../types/instagram'

const API_BASE_URL = 'http://localhost:8000'

export const useInstagramStore = defineStore('instagram', () => {
  // State
  const profile = ref<ProfileData | null>(null)
  const followers = ref<User[]>([])
  const following = ref<User[]>([])
  
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const isLoggedIn = ref(false)
  const progressMessage = ref<string>('Iniciando...')

  // Actions
  const checkAuthStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/status`)
      const data = await response.json()
      isLoggedIn.value = data.logged_in
      return data.logged_in
    } catch (err) {
      console.error('Erro ao verificar status de autenticação:', err)
      isLoggedIn.value = false
      return false
    }
  }

  const waitForLogin = async () => {
    isLoading.value = true
    progressMessage.value = 'Aguardando login no navegador...'
    error.value = null

    try {
      const response = await fetch(`${API_BASE_URL}/auth/wait-login`, {
        method: 'POST',
      })

      if (!response.ok) {
        const errorData: ApiError = await response.json()
        throw new Error(errorData.detail || 'Erro ao aguardar login')
      }

      const data = await response.json()
      isLoggedIn.value = true
      progressMessage.value = 'Login realizado!'
      await checkAuthStatus()
      return data
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro desconhecido ao fazer login'
      error.value = message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const scrapeProfile = async (request: ScrapeRequest) => {
    isLoading.value = true
    error.value = null
    progressMessage.value = 'Conectando...'

    return new Promise((resolve, reject) => {
      // Construir query params para SSE
      const params = new URLSearchParams({
        username: request.username,
        get_followers: String(request.get_followers),
        get_following: String(request.get_following),
      })
      
      if (request.max_followers) params.append('max_followers', String(request.max_followers))
      if (request.max_following) params.append('max_following', String(request.max_following))

      // Criar EventSource para receber progresso em tempo real
      const eventSource = new EventSource(`${API_BASE_URL}/scrape-stream?${params}`)
      let hasError = false  // Flag para evitar múltiplos erros

      eventSource.addEventListener('progress', (event) => {
        progressMessage.value = event.data
      })

      eventSource.addEventListener('complete', (event) => {
        try {
          const result = JSON.parse(event.data)
          const data = result.data || result
          
          // Extract profile data (remove followers/following arrays)
          const { followers: followersList, following: followingList, ...profileData } = data
          
          // Update state
          profile.value = profileData as ProfileData
          followers.value = followersList || []
          following.value = followingList || []

          eventSource.close()
          isLoading.value = false
          resolve({ profile: profile.value, followers: followers.value, following: following.value })
        } catch (err) {
          if (hasError) return
          hasError = true
          eventSource.close()
          isLoading.value = false
          const message = 'Erro ao processar dados recebidos'
          error.value = message
          reject(new Error(message))
        }
      })

      // Evento customizado de erro do backend (não confundir com onerror de conexão)
      eventSource.addEventListener('failure', (event: any) => {
        if (hasError) return
        hasError = true
        eventSource.close()
        isLoading.value = false
        
        // Extrair mensagem de erro do backend
        let message = 'Erro ao extrair dados do perfil'
        try {
          const errorData = JSON.parse(event.data)
          message = errorData.detail || message
        } catch {
          message = event.data || message
        }
        
        error.value = message
        reject(new Error(message))
      })

      // Erro de conexão real (não disparará se já teve erro customizado)
      eventSource.onerror = (event) => {
        if (hasError) return
        hasError = true
        eventSource.close()
        isLoading.value = false
        const message = 'Conexão perdida com o servidor'
        error.value = message
        reject(new Error(message))
      }
    })
  }

  const clearData = () => {
    profile.value = null
    followers.value = []
    following.value = []
    error.value = null
    progressMessage.value = 'Iniciando...'
  }

  const clearError = () => {
    error.value = null
  }

  const clearBackendImages = async () => {
    try {
      await fetch(`${API_BASE_URL}/clear-images`, {
        method: 'POST',
      })
    } catch (err) {
      console.error('Erro ao limpar imagens:', err)
    }
  }

  return {
    // State
    profile,
    followers,
    following,
    isLoading,
    error,
    isLoggedIn,
    progressMessage,
    
    // Actions
    checkAuthStatus,
    waitForLogin,
    scrapeProfile,
    clearData,
    clearError,
    clearBackendImages,
  }
})
