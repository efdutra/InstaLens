import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ProfileData, User, ScrapeRequest, ScrapeResponse, ApiError } from '../types/instagram'

// Automatically use the same host as the frontend
const API_BASE_URL = `http://${window.location.hostname}:8000`

export const useInstagramStore = defineStore('instagram', () => {
  // State
  const profile = ref<ProfileData | null>(null)
  const followers = ref<User[]>([])
  const following = ref<User[]>([])
  
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const isLoggedIn = ref(false)
  const progressMessage = ref<string>('Starting...')

  // Actions
  const checkAuthStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/status`)
      const data = await response.json()
      isLoggedIn.value = data.logged_in
      return data.logged_in
    } catch (err) {
      console.error('Error checking authentication status:', err)
      isLoggedIn.value = false
      return false
    }
  }

  const waitForLogin = async () => {
    isLoading.value = true
    progressMessage.value = 'Waiting for login in browser...'
    error.value = null

    try {
      const response = await fetch(`${API_BASE_URL}/auth/wait-login`, {
        method: 'POST',
      })

      if (!response.ok) {
        const errorData: ApiError = await response.json()
        throw new Error(errorData.detail || 'Error waiting for login')
      }

      const data = await response.json()
      isLoggedIn.value = true
      progressMessage.value = 'Login completed!'
      await checkAuthStatus()
      return data
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error during login'
      error.value = message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const scrapeProfile = async (request: ScrapeRequest) => {
    isLoading.value = true
    error.value = null
    progressMessage.value = 'Connecting...'

    return new Promise((resolve, reject) => {
      // Construir query params para SSE
      const params = new URLSearchParams({
        username: request.username,
        get_followers: String(request.get_followers),
        get_following: String(request.get_following),
      })
      
      if (request.max_followers) params.append('max_followers', String(request.max_followers))
      if (request.max_following) params.append('max_following', String(request.max_following))

      // Create EventSource to receive real-time progress
      const eventSource = new EventSource(`${API_BASE_URL}/scrape-stream?${params}`)
      let hasError = false  // Flag to avoid multiple errors

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
          const message = 'Error processing received data'
          error.value = message
          reject(new Error(message))
        }
      })

      // Custom error event from backend (don't confuse with connection onerror)
      eventSource.addEventListener('failure', (event: any) => {
        if (hasError) return
        hasError = true
        eventSource.close()
        isLoading.value = false
        
        // Extract error message from backend
        let message = 'Error extracting profile data'
        try {
          const errorData = JSON.parse(event.data)
          message = errorData.detail || message
        } catch {
          message = event.data || message
        }
        
        error.value = message
        reject(new Error(message))
      })

      // Real connection error (won't fire if already had custom error)
      eventSource.onerror = (event) => {
        if (hasError) return
        hasError = true
        eventSource.close()
        isLoading.value = false
        const message = 'Connection lost with server'
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
    progressMessage.value = 'Starting...'
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
      console.error('Error clearing images:', err)
    }
  }

  const exportToCSV = () => {
    if (!profile.value) return

    // Create CSV content
    let csvContent = ''

    // Section 1: Profile Data
    csvContent += '=== PROFILE ===\n'
    csvContent += 'Field,Value\n'
    csvContent += `Username,${profile.value.username}\n`
    csvContent += `Name,${profile.value.name}\n`
    csvContent += `Bio,"${(profile.value.bio || '').replace(/"/g, '""')}"\n`
    csvContent += `Posts,${profile.value.posts_count}\n`
    csvContent += `Followers,${profile.value.followers_count}\n`
    csvContent += `Following,${profile.value.following_count}\n`
    csvContent += `Photo,${profile.value.profile_pic}\n`
    if (profile.value.profile_pic_url) {
      csvContent += `Original Photo,${profile.value.profile_pic_url}\n`
    }
    csvContent += '\n'

    // Section 2: Followers
    if (followers.value.length > 0) {
      csvContent += '=== FOLLOWERS ===\n'
      csvContent += 'Username,Name,URL,Original Photo,Gender\n'
      followers.value.forEach(user => {
        const name = (user.name || '').replace(/"/g, '""')
        const photoUrl = user.profile_pic_url || ''
        const gender = user.gender || 'I'
        const genderLabel = gender === 'M' ? 'Male' : gender === 'F' ? 'Female' : 'Undetermined'
        csvContent += `${user.username},"${name}",${user.profile_url},${photoUrl},${genderLabel}\n`
      })
      csvContent += '\n'
    }

    // Section 3: Following
    if (following.value.length > 0) {
      csvContent += '=== FOLLOWING ===\n'
      csvContent += 'Username,Name,URL,Original Photo,Gender\n'
      following.value.forEach(user => {
        const name = (user.name || '').replace(/"/g, '""')
        const photoUrl = user.profile_pic_url || ''
        const gender = user.gender || 'I'
        const genderLabel = gender === 'M' ? 'Male' : gender === 'F' ? 'Female' : 'Undetermined'
        csvContent += `${user.username},"${name}",${user.profile_url},${photoUrl},${genderLabel}\n`
      })
    }

    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    
    link.setAttribute('href', url)
    link.setAttribute('download', `instagram_${profile.value.username}_${new Date().toISOString().split('T')[0]}.csv`)
    link.style.visibility = 'hidden'
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const exportToJSON = () => {
    if (!profile.value) return

    // Create JSON object
    const data = {
      scraped_at: new Date().toISOString(),
      profile: profile.value,
      followers: followers.value,
      following: following.value,
      stats: {
        total_followers: followers.value.length,
        total_following: following.value.length,
        gender_breakdown_followers: {
          male: followers.value.filter(u => u.gender === 'M').length,
          female: followers.value.filter(u => u.gender === 'F').length,
          undetermined: followers.value.filter(u => !u.gender || u.gender === 'I').length
        },
        gender_breakdown_following: {
          male: following.value.filter(u => u.gender === 'M').length,
          female: following.value.filter(u => u.gender === 'F').length,
          undetermined: following.value.filter(u => !u.gender || u.gender === 'I').length
        }
      }
    }

    // Create blob and download
    const jsonString = JSON.stringify(data, null, 2)
    const blob = new Blob([jsonString], { type: 'application/json;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    
    link.setAttribute('href', url)
    link.setAttribute('download', `instagram_${profile.value.username}_${new Date().toISOString().split('T')[0]}.json`)
    link.style.visibility = 'hidden'
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
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
    exportToCSV,
    exportToJSON,
  }
})
