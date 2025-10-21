<template>
  <!-- Modal Overlay -->
  <Teleport to="body">
    <Transition name="modal">
      <div 
        v-if="isOpen"
        class="fixed inset-0 z-50 overflow-y-auto"
        @click.self="closeModal"
      >
        <!-- Backdrop -->
        <div class="fixed inset-0 bg-black bg-opacity-50 transition-opacity"></div>
        
        <!-- Modal Content -->
        <div class="flex min-h-full items-center justify-center p-4">
          <div 
            class="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-2xl w-full transform transition-all"
            @click.stop
          >
            <!-- Header -->
            <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <div class="flex items-start justify-between">
                <div class="flex items-center space-x-3">
                  <!-- Icon based on severity -->
                  <div :class="[
                    'flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center',
                    notification.severity === 'success' ? 'bg-green-100 dark:bg-green-900/50' :
                    notification.severity === 'error' ? 'bg-red-100 dark:bg-red-900/50' :
                    notification.severity === 'warning' ? 'bg-yellow-100 dark:bg-yellow-900/50' :
                    'bg-blue-100 dark:bg-blue-900/50'
                  ]">
                    <!-- Success Icon -->
                    <svg 
                      v-if="notification.severity === 'success'"
                      class="w-6 h-6 text-green-600 dark:text-green-400" 
                      fill="currentColor" 
                      viewBox="0 0 20 20"
                    >
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                    </svg>
                    
                    <!-- Error Icon -->
                    <svg 
                      v-else-if="notification.severity === 'error'"
                      class="w-6 h-6 text-red-600 dark:text-red-400" 
                      fill="currentColor" 
                      viewBox="0 0 20 20"
                    >
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                    </svg>
                    
                    <!-- Warning Icon -->
                    <svg 
                      v-else-if="notification.severity === 'warning'"
                      class="w-6 h-6 text-yellow-600 dark:text-yellow-400" 
                      fill="currentColor" 
                      viewBox="0 0 20 20"
                    >
                      <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                    </svg>
                    
                    <!-- Info Icon -->
                    <svg 
                      v-else
                      class="w-6 h-6 text-blue-600 dark:text-blue-400" 
                      fill="currentColor" 
                      viewBox="0 0 20 20"
                    >
                      <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
                    </svg>
                  </div>
                  
                  <div>
                    <h3 class="text-xl font-bold text-gray-900 dark:text-white">
                      {{ notification.title }}
                    </h3>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                      {{ formatRelativeTime(notification.timestamp) }}
                    </p>
                  </div>
                </div>
                
                <!-- Close Button -->
                <button
                  @click="closeModal"
                  class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                </button>
              </div>
            </div>
            
            <!-- Body -->
            <div class="px-6 py-6 space-y-6">
              <!-- Message -->
              <div>
                <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Wiadomość</h4>
                <p class="text-gray-900 dark:text-white text-base leading-relaxed">
                  {{ notification.message }}
                </p>
              </div>
              
              <!-- Metadata -->
              <div v-if="hasMetadata" class="space-y-3">
                <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300">Szczegóły</h4>
                
                <div class="grid grid-cols-2 gap-3">
                  <!-- Cluster -->
                  <div v-if="notification.metadata?.cluster" class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                    <div class="flex items-center space-x-2 text-gray-600 dark:text-gray-400 text-xs mb-1">
                      <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"/>
                      </svg>
                      <span>Klaster</span>
                    </div>
                    <p class="font-medium text-gray-900 dark:text-white">{{ notification.metadata.cluster }}</p>
                  </div>
                  
                  <!-- App Name -->
                  <div v-if="notification.metadata?.app_name" class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                    <div class="flex items-center space-x-2 text-gray-600 dark:text-gray-400 text-xs mb-1">
                      <span>📦</span>
                      <span>Aplikacja</span>
                    </div>
                    <p class="font-medium text-gray-900 dark:text-white">{{ notification.metadata.app_name }}</p>
                  </div>
                  
                  <!-- Backup Name -->
                  <div v-if="notification.metadata?.backup_name" class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                    <div class="flex items-center space-x-2 text-gray-600 dark:text-gray-400 text-xs mb-1">
                      <span>💾</span>
                      <span>Backup</span>
                    </div>
                    <p class="font-medium text-gray-900 dark:text-white">{{ notification.metadata.backup_name }}</p>
                  </div>
                  
                  <!-- Provider -->
                  <div v-if="notification.metadata?.provider" class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                    <div class="flex items-center space-x-2 text-gray-600 dark:text-gray-400 text-xs mb-1">
                      <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M2 5a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V5zm3.293 1.293a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 01-1.414-1.414L7.586 10 5.293 7.707a1 1 0 010-1.414zM11 12a1 1 0 100 2h3a1 1 0 100-2h-3z" clip-rule="evenodd"/>
                      </svg>
                      <span>Provider</span>
                    </div>
                    <p class="font-medium text-gray-900 dark:text-white uppercase">{{ notification.metadata.provider }}</p>
                  </div>
                </div>
              </div>
              
              <!-- Type -->
              <div class="flex items-center space-x-2">
                <span class="text-sm text-gray-500 dark:text-gray-400">Typ:</span>
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200">
                  {{ notification.type }}
                </span>
                <span 
                  v-if="!notification.read"
                  class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-200"
                >
                  Nieprzeczytane
                </span>
              </div>
            </div>
            
            <!-- Footer / Actions -->
            <div class="px-6 py-4 bg-gray-50 dark:bg-gray-900/50 border-t border-gray-200 dark:border-gray-700 rounded-b-2xl flex items-center justify-between flex-wrap gap-3">
              <!-- Mark as Read -->
              <button
                v-if="!notification.read"
                @click="markAsRead"
                :disabled="isMarkingAsRead"
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                <svg v-if="isMarkingAsRead" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                <span>Oznacz jako przeczytane</span>
              </button>
              
              <span v-else class="text-sm text-gray-500 dark:text-gray-400 flex items-center space-x-2">
                <svg class="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                </svg>
                <span>Przeczytane</span>
              </span>
              
              <!-- Go to Cluster -->
              <button
                v-if="notification.metadata?.cluster"
                @click="goToCluster"
                class="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg text-sm font-medium transition-colors flex items-center space-x-2"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"/>
                </svg>
                <span>Przejdź do klastra</span>
              </button>
              
              <!-- Delete Notification -->
              <button
                @click="deleteNotification"
                :disabled="isDeleting"
                class="px-4 py-2 bg-red-600 hover:bg-red-700 dark:bg-red-500 dark:hover:bg-red-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                <svg v-if="isDeleting" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                </svg>
                <span>Usuń powiadomienie</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationsStore } from '@/stores/notifications'
import type { Notification } from '@/stores/notifications'

interface Props {
  notification: Notification
  isOpen: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

const router = useRouter()
const notificationsStore = useNotificationsStore()
const isMarkingAsRead = ref(false)
const isDeleting = ref(false)

const hasMetadata = computed(() => {
  return props.notification.metadata && Object.keys(props.notification.metadata).length > 0
})

const closeModal = () => {
  emit('close')
}

const markAsRead = async () => {
  isMarkingAsRead.value = true
  try {
    await notificationsStore.markAsRead(props.notification.id)
    // Update local notification object
    props.notification.read = true
  } catch (error) {
    console.error('Error marking as read:', error)
  } finally {
    isMarkingAsRead.value = false
  }
}

const goToCluster = () => {
  if (props.notification.metadata?.cluster) {
    router.push(`/clusters/${props.notification.metadata.cluster}`)
    closeModal()
  }
}

const deleteNotification = async () => {
  isDeleting.value = true
  try {
    await notificationsStore.deleteNotification(props.notification.id)
    closeModal()
  } catch (error) {
    console.error('Error deleting notification:', error)
  } finally {
    isDeleting.value = false
  }
}

const formatRelativeTime = (timestamp: string): string => {
  const now = new Date()
  const time = new Date(timestamp)
  const diffMs = now.getTime() - time.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  
  if (diffMins < 1) return 'przed chwilą'
  if (diffMins < 60) return `${diffMins} min temu`
  
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h temu`
  
  const diffDays = Math.floor(diffHours / 24)
  if (diffDays === 1) return 'wczoraj'
  if (diffDays < 7) return `${diffDays} dni temu`
  
  return time.toLocaleDateString('pl-PL')
}
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .bg-white,
.modal-leave-active .bg-white {
  transition: all 0.3s ease;
}

.modal-enter-from .bg-white,
.modal-leave-to .bg-white {
  transform: scale(0.95);
  opacity: 0;
}
</style>
