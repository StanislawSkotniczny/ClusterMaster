import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface AwsCredentials {
  region: string
  accessKey: string
  secretKey: string
}

export const useAwsStore = defineStore('aws', () => {
  // State
  const credentials = ref<AwsCredentials | null>(null)
  const isConnected = ref(false)

  // Getters
  const hasCredentials = computed(() => !!credentials.value?.accessKey && !!credentials.value?.secretKey)
  const currentRegion = computed(() => credentials.value?.region || 'us-east-1')

  // Actions
  function setCredentials(region: string, accessKey: string, secretKey: string) {
    credentials.value = {
      region,
      accessKey,
      secretKey
    }
    isConnected.value = true
    
    // Persist to localStorage for page refreshes
    localStorage.setItem('aws_credentials', JSON.stringify(credentials.value))
  }

  function clearCredentials() {
    credentials.value = null
    isConnected.value = false
    localStorage.removeItem('aws_credentials')
  }

  function loadCredentials() {
    const stored = localStorage.getItem('aws_credentials')
    if (stored) {
      try {
        credentials.value = JSON.parse(stored)
        isConnected.value = true
      } catch (e) {
        console.error('Failed to parse stored AWS credentials:', e)
        clearCredentials()
      }
    }
  }

  function updateRegion(newRegion: string) {
    if (credentials.value) {
      credentials.value.region = newRegion
      localStorage.setItem('aws_credentials', JSON.stringify(credentials.value))
    }
  }

  // Initialize from localStorage on store creation
  loadCredentials()

  return {
    // State
    credentials,
    isConnected,
    // Getters
    hasCredentials,
    currentRegion,
    // Actions
    setCredentials,
    clearCredentials,
    loadCredentials,
    updateRegion
  }
})
