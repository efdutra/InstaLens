const API_BASE_URL = 'http://localhost:8000'

export function useImageProxy() {
  const getProxiedUrl = (originalUrl: string): string => {
    if (!originalUrl) return ''
    return `${API_BASE_URL}/proxy-image?url=${encodeURIComponent(originalUrl)}`
  }

  return {
    getProxiedUrl
  }
}
