<template>
  <div class="relative">
    <!-- Bell Button - Click to go to notifications page -->
    <button 
      @click="goToNotifications" 
      class="relative p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
    >
      <!-- Bell Icon -->
      <svg 
        class="w-6 h-6" 
        fill="none" 
        stroke="currentColor" 
        viewBox="0 0 24 24"
      >
        <path 
          stroke-linecap="round" 
          stroke-linejoin="round" 
          stroke-width="2" 
          d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
        />
      </svg>
      
      <!-- Badge with count -->
      <span 
        v-if="notificationsStore.unreadCount > 0"
        class="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white bg-red-500 rounded-full transform translate-x-1/2 -translate-y-1/2 min-w-[20px]"
      >
        {{ notificationsStore.unreadCount > 99 ? '99+' : notificationsStore.unreadCount }}
      </span>
      
      <!-- Connection indicator (pulse) -->
      <span 
        v-if="notificationsStore.connected"
        class="absolute bottom-1 right-1 flex h-2 w-2"
      >
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
        <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
      </span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useNotificationsStore } from '@/stores/notifications'
import { useRouter } from 'vue-router'

const router = useRouter()
const notificationsStore = useNotificationsStore()

const goToNotifications = () => {
  router.push('/notifications')
}

onMounted(() => {
  // Connect to SSE
  notificationsStore.connect()
  
  // Fetch history
  notificationsStore.fetchHistory()
  
  // Request notification permission
  notificationsStore.requestNotificationPermission()
})

onUnmounted(() => {
  // Disconnect from SSE
  notificationsStore.disconnect()
})
</script>
