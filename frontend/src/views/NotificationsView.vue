<template>
  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">Powiadomienia</h1>
      <p class="text-gray-600 dark:text-gray-400">Historia wszystkich powiadomień systemowych</p>
    </div>

    <!-- Controls -->
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 mb-6">
      <div class="flex items-center justify-between flex-wrap gap-4">
        <!-- Connection Status -->
        <div class="flex items-center space-x-3">
          <div class="flex items-center space-x-2">
            <span 
              v-if="notificationsStore.connected"
              class="flex h-3 w-3"
            >
              <span class="animate-ping absolute inline-flex h-3 w-3 rounded-full bg-green-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
            </span>
            <span v-else class="inline-flex h-3 w-3 rounded-full bg-red-500"></span>
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
              {{ notificationsStore.connected ? 'Połączono' : 'Rozłączono' }}
            </span>
          </div>
          
          <div class="h-6 w-px bg-gray-300 dark:bg-gray-600"></div>
          
          <span class="text-sm text-gray-600 dark:text-gray-400">
            {{ notificationsStore.unreadCount }} nieprzeczytanych
          </span>
        </div>

        <!-- Actions -->
        <div class="flex items-center space-x-3">
          <!-- Filter -->
          <select 
            v-model="filterSeverity"
            class="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent"
          >
            <option value="all">Wszystkie</option>
            <option value="success">✅ Sukces</option>
            <option value="error">❌ Błędy</option>
            <option value="warning">⚠️ Ostrzeżenia</option>
            <option value="info">ℹ️ Info</option>
          </select>

          <!-- Mark All as Read -->
          <button
            v-if="notificationsStore.unreadCount > 0"
            @click="handleMarkAllAsRead"
            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-colors"
          >
            Oznacz wszystkie jako przeczytane
          </button>

          <!-- Refresh -->
          <button
            @click="handleRefresh"
            :disabled="notificationsStore.loading"
            class="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
            title="Odśwież"
          >
            <svg 
              class="w-5 h-5"
              :class="{ 'animate-spin': notificationsStore.loading }"
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Notifications List -->
    <div class="space-y-3">
      <!-- Loading State -->
      <div 
        v-if="notificationsStore.loading && notificationsStore.notifications.length === 0"
        class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-12 text-center"
      >
        <svg class="animate-spin h-10 w-10 text-blue-500 dark:text-blue-400 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <p class="text-gray-500 dark:text-gray-400">Ładowanie powiadomień...</p>
      </div>

      <!-- Empty State -->
      <div 
        v-else-if="filteredNotifications.length === 0"
        class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-16 text-center"
      >
        <svg class="w-20 h-20 mx-auto mb-4 text-gray-300 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
        </svg>
        <p class="text-lg font-medium text-gray-900 dark:text-white mb-2">Brak powiadomień</p>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          {{ filterSeverity !== 'all' ? 'Nie znaleziono powiadomień dla wybranego filtra' : 'Powiadomienia pojawią się tutaj gdy wystąpią zdarzenia systemowe' }}
        </p>
      </div>

      <!-- Notification Cards -->
      <div 
        v-for="notification in filteredNotifications"
        :key="notification.id"
        @click="handleNotificationClick(notification)"
        :class="[
          'bg-white dark:bg-gray-800 rounded-xl shadow-sm border transition-all cursor-pointer',
          !notification.read 
            ? 'border-blue-300 dark:border-blue-700 bg-blue-50 dark:bg-blue-900/20 hover:shadow-md' 
            : 'border-gray-100 dark:border-gray-700 hover:shadow-md hover:border-gray-200 dark:hover:border-gray-600'
        ]"
      >
        <div class="p-6">
          <div class="flex items-start space-x-4">
            <!-- Icon -->
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
            
            <!-- Content -->
            <div class="flex-1 min-w-0">
              <div class="flex items-start justify-between mb-2">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                  {{ notification.title }}
                </h3>
                <span 
                  v-if="!notification.read"
                  class="flex-shrink-0 inline-block w-2.5 h-2.5 bg-blue-500 rounded-full ml-2"
                  title="Nieprzeczytane"
                ></span>
              </div>
              
              <p class="text-gray-700 dark:text-gray-300 mb-3">
                {{ notification.message }}
              </p>
              
              <div class="flex items-center flex-wrap gap-3 text-sm">
                <div class="flex items-center text-gray-500 dark:text-gray-400">
                  <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"/>
                  </svg>
                  {{ formatRelativeTime(notification.timestamp) }}
                </div>
                
                <span 
                  v-if="notification.metadata?.cluster"
                  class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200"
                >
                  <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"/>
                  </svg>
                  {{ notification.metadata.cluster }}
                </span>
                
                <span 
                  v-if="notification.metadata?.app_name"
                  class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 dark:bg-purple-900/50 text-purple-800 dark:text-purple-200"
                >
                  📦 {{ notification.metadata.app_name }}
                </span>
                
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
                  {{ notification.type }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Notification Modal -->
    <NotificationModal
      v-if="selectedNotification"
      :notification="selectedNotification"
      :is-open="showModal"
      @close="closeModal"
    />
  </main>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useNotificationsStore } from '@/stores/notifications'
import type { Notification } from '@/stores/notifications'
import NotificationModal from '@/components/NotificationModal.vue'

const notificationsStore = useNotificationsStore()
const filterSeverity = ref<'all' | 'success' | 'error' | 'warning' | 'info'>('all')
const showModal = ref(false)
const selectedNotification = ref<Notification | null>(null)

// Filtered notifications
const filteredNotifications = computed(() => {
  if (filterSeverity.value === 'all') {
    return notificationsStore.notifications
  }
  return notificationsStore.notifications.filter(n => n.severity === filterSeverity.value)
})

// Handle notification click - open modal
const handleNotificationClick = (notification: Notification) => {
  selectedNotification.value = notification
  showModal.value = true
}

// Close modal
const closeModal = () => {
  showModal.value = false
  setTimeout(() => {
    selectedNotification.value = null
  }, 300) // Wait for animation
}

// Mark all as read
const handleMarkAllAsRead = async () => {
  await notificationsStore.markAllAsRead()
}

// Refresh
const handleRefresh = () => {
  notificationsStore.fetchHistory()
}

// Format relative time
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
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} tyg. temu`
  
  const diffMonths = Math.floor(diffDays / 30)
  if (diffMonths < 12) return `${diffMonths} mies. temu`
  
  return `${Math.floor(diffMonths / 12)} lat temu`
}
</script>
