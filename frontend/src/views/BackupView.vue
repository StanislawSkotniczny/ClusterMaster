<template>
  <div class="container mx-auto p-6">
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">🗂️ Backup Klastrów</h1>
      <p class="text-gray-600">Twórz i zarządzaj backupami klastrów Kubernetes</p>
      
      <!-- Backup directory info -->
      <div v-if="backupInfo" class="mt-4 bg-blue-50 border border-blue-200 rounded-md p-4">
        <div class="flex items-center">
          <svg class="h-5 w-5 text-blue-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
          </svg>
          <div class="text-sm text-blue-800">
            <span class="font-medium">Katalog backup:</span> {{ backupInfo.backup_directory }}
            <span class="ml-4"><strong>{{ backupInfo.total_backups }}</strong> backupów ({{ (backupInfo.total_size_mb as number)?.toFixed(2) }} MB)</span>
          </div>
        </div>
      </div>
      
      <!-- Directory Change Section -->
      <div class="mt-4 bg-gray-50 border border-gray-200 rounded-md p-4">
        <h3 class="text-lg font-medium text-gray-900 mb-4">Zmiana lokalizacji backupów</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Wybierz nową lokalizację dla backupów:
            </label>
            <div class="flex space-x-2">
              <input
                type="text"
                v-model="newBackupDirectory"
                placeholder="Wpisz ścieżkę do folderu..."
                class="flex-1 min-w-0 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <button
                @click="browseDirectory"
                class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                📁 Przeglądaj
              </button>
            </div>
          </div>
          <div class="flex justify-end space-x-3">
            <button
              @click="resetDirectoryInput"
              class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
            >
              Reset
            </button>
            <button
              @click="changeBackupDirectory"
              :disabled="!newBackupDirectory || changingDirectory"
              class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <template v-if="changingDirectory">
                <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Zmieniam...
              </template>
              <template v-else>
                Zmień lokalizację
              </template>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Backup Section -->
    <div class="bg-white shadow rounded-lg p-6 mb-8">
      <h2 class="text-xl font-semibold text-gray-900 mb-4">Utwórz nowy backup</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Klaster</label>
          <select 
            v-model="selectedCluster" 
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value="">Wybierz klaster</option>
            <option 
              v-for="cluster in clusters" 
              :key="cluster.name" 
              :value="cluster.name"
              :disabled="cluster.status !== 'ready'"
            >
              {{ cluster.name }} ({{ cluster.status }})
            </option>
          </select>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Nazwa backupu (opcjonalne)</label>
          <input 
            v-model="backupName" 
            type="text" 
            placeholder="Automatycznie wygenerowana"
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
        </div>
        
        <div class="flex items-end">
          <button 
            @click="createBackup"
            :disabled="!selectedCluster || creatingBackup"
            class="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-md font-medium"
          >
            <span v-if="creatingBackup" class="flex items-center justify-center">
              <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Tworzenie...
            </span>
            <span v-else>Utwórz backup</span>
          </button>
        </div>
      </div>
      
      <div v-if="backupMessage" class="mt-4 p-4 rounded-md" :class="backupMessageType === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'">
        {{ backupMessage }}
      </div>
    </div>

    <!-- Backups List Section -->
    <div class="bg-white shadow rounded-lg overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-200">
        <div class="flex justify-between items-center">
          <h2 class="text-xl font-semibold text-gray-900">Lista backupów</h2>
          <button 
            @click="loadBackups"
            :disabled="loadingBackups"
            class="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-md font-medium flex items-center"
          >
            <svg v-if="loadingBackups" class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <svg v-else class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            Odśwież
          </button>
        </div>
      </div>

      <div v-if="loadingBackups" class="p-8 text-center text-gray-500">
        <svg class="mx-auto h-12 w-12 animate-spin text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <p class="mt-4">Ładowanie backupów...</p>
      </div>

      <div v-else-if="backups.length === 0" class="p-8 text-center text-gray-500">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-4.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 009.586 13H7"></path>
        </svg>
        <p class="mt-4">Brak backupów</p>
        <p class="text-sm">Utwórz pierwszy backup używając formularza powyżej</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nazwa</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Klaster</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data utworzenia</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rozmiar</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Zasoby</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Akcje</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="backup in backups" :key="backup.backup_name" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">{{ backup.backup_name }}</div>
                <div v-if="backup.error" class="text-sm text-red-600">{{ backup.error }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {{ backup.cluster_name }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ formatDate(backup.created_at) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ backup.size_mb }} MB
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ backup.resources_count }} zasobów
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                <button 
                  @click="downloadBackup(backup.backup_name)"
                  class="text-blue-600 hover:text-blue-900"
                >
                  Pobierz
                </button>
                <button 
                  @click="viewBackupDetails(backup)"
                  class="text-green-600 hover:text-green-900"
                >
                  Szczegóły
                </button>
                <button 
                  @click="confirmRestoreBackup(backup.backup_name)"
                  class="text-purple-600 hover:text-purple-900"
                >
                  Przywróć
                </button>
                <button 
                  @click="confirmDeleteBackup(backup.backup_name)"
                  class="text-red-600 hover:text-red-900"
                >
                  Usuń
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Backup Details Modal -->
    <div v-if="showDetailsModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div class="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-medium text-gray-900">Szczegóły backupu: {{ selectedBackupDetails?.backup_name }}</h3>
          <button @click="showDetailsModal = false" class="text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        
        <div v-if="selectedBackupDetails" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Klaster</label>
              <p class="mt-1 text-sm text-gray-900">{{ selectedBackupDetails.cluster_name }}</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Data utworzenia</label>
              <p class="mt-1 text-sm text-gray-900">{{ formatDate(selectedBackupDetails.created_at) }}</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Rozmiar</label>
              <p class="mt-1 text-sm text-gray-900">{{ selectedBackupDetails.file_info.size_mb }} MB</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Liczba plików</label>
              <p class="mt-1 text-sm text-gray-900">{{ selectedBackupDetails.file_info.file_count }}</p>
            </div>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Zasoby w backupie</label>
            <div class="bg-gray-50 rounded-md p-4 max-h-60 overflow-y-auto">
              <div v-for="resource in selectedBackupDetails.resources" :key="`${resource.type}-${resource.namespace}`" class="mb-2">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                  {{ resource.type }}
                </span>
                <span v-if="resource.namespace" class="ml-2 text-sm text-gray-600">
                  w namespace: {{ resource.namespace }}
                </span>
                <span v-else class="ml-2 text-sm text-gray-600">
                  (zasób klastra)
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div class="mt-3 text-center">
          <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
            <svg class="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
            </svg>
          </div>
          <h3 class="text-lg font-medium text-gray-900 mt-2">Usuń backup</h3>
          <div class="mt-2 px-7 py-3">
            <p class="text-sm text-gray-500">
              Czy na pewno chcesz usunąć backup "{{ backupToDelete }}"? Ta operacja jest nieodwracalna.
            </p>
          </div>
          <div class="items-center px-4 py-3 flex justify-center space-x-4">
            <button @click="showDeleteModal = false" class="px-4 py-2 bg-gray-300 text-gray-800 text-base font-medium rounded-md shadow-sm hover:bg-gray-400">
              Anuluj
            </button>
            <button @click="deleteBackup" :disabled="deletingBackup" class="px-4 py-2 bg-red-500 text-white text-base font-medium rounded-md shadow-sm hover:bg-red-700 disabled:bg-gray-400">
              <span v-if="deletingBackup">Usuwanie...</span>
              <span v-else>Usuń</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Restore Confirmation Modal -->
    <div v-if="showRestoreModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div class="mt-3 text-center">
          <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-purple-100">
            <svg class="h-6 w-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
          </div>
          <h3 class="text-lg font-medium text-gray-900 mt-2">Przywróć backup</h3>
          <div class="mt-2 px-7 py-3">
            <p class="text-sm text-gray-500 mb-4">
              Przywrócić klaster z backupu "{{ backupToRestore }}"?
            </p>
            <div class="text-left">
              <label class="block text-sm font-medium text-gray-700 mb-2">Nazwa nowego klastra (opcjonalne)</label>
              <input 
                v-model="restoreClusterName" 
                type="text" 
                placeholder="Automatycznie wygenerowana"
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
              >
            </div>
          </div>
          <div class="items-center px-4 py-3 flex justify-center space-x-4">
            <button @click="showRestoreModal = false" class="px-4 py-2 bg-gray-300 text-gray-800 text-base font-medium rounded-md shadow-sm hover:bg-gray-400">
              Anuluj
            </button>
            <button @click="restoreBackup" :disabled="restoringBackup" class="px-4 py-2 bg-purple-500 text-white text-base font-medium rounded-md shadow-sm hover:bg-purple-700 disabled:bg-gray-400">
              <span v-if="restoringBackup">Przywracanie...</span>
              <span v-else>Przywróć</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ApiService, type ClusterInfo, type BackupInfo, type BackupDetails } from '@/services/api'

// Reactive data
const clusters = ref<ClusterInfo[]>([])
const backups = ref<BackupInfo[]>([])
const backupInfo = ref<Record<string, unknown> | null>(null)
const selectedCluster = ref('')
const backupName = ref('')
const creatingBackup = ref(false)
const loadingBackups = ref(false)
const backupMessage = ref('')
const backupMessageType = ref<'success' | 'error'>('success')

// Modals
const showDetailsModal = ref(false)
const showDeleteModal = ref(false)
const showRestoreModal = ref(false)
const selectedBackupDetails = ref<BackupDetails | null>(null)
const backupToDelete = ref('')
const backupToRestore = ref('')
const restoreClusterName = ref('')
const deletingBackup = ref(false)
const restoringBackup = ref(false)

// Directory management
const newBackupDirectory = ref('')
const changingDirectory = ref(false)

// Load data on mount
onMounted(async () => {
  await loadClusters()
  await loadBackups()
  await loadBackupInfo()
})

// Methods
const loadClusters = async () => {
  try {
    const response = await ApiService.listClustersDetailed()
    clusters.value = response.clusters || []
  } catch (error) {
    console.error('Error loading clusters:', error)
  }
}

const loadBackups = async () => {
  loadingBackups.value = true
  try {
    const response = await ApiService.listBackups()
    if (response.success) {
      backups.value = response.backups
    }
  } catch (error) {
    console.error('Error loading backups:', error)
  } finally {
    loadingBackups.value = false
  }
}

const loadBackupInfo = async () => {
  try {
    const response = await ApiService.getBackupInfo()
    backupInfo.value = response
  } catch (error) {
    console.error('Error loading backup info:', error)
  }
}

// Directory management methods
const resetDirectoryInput = () => {
  newBackupDirectory.value = ''
}

const browseDirectory = async () => {
  // W przeglądarce nie możemy bezpośrednio otworzyć eksploratora plików
  // Implementujemy to poprzez input z placeholder sugerujący ścieżkę
  const suggestion = prompt('Wprowadź ścieżkę do folderu backupów (np. C:\\backups lub D:\\cluster-backups):')
  if (suggestion) {
    newBackupDirectory.value = suggestion
  }
}

const changeBackupDirectory = async () => {
  if (!newBackupDirectory.value) return
  
  changingDirectory.value = true
  try {
    const response = await ApiService.changeBackupDirectory(newBackupDirectory.value)
    if (response.success) {
      // Odśwież informacje o backupach
      await loadBackupInfo()
      await loadBackups()
      
      backupMessage.value = response.message
      backupMessageType.value = 'success'
      
      // Wyczyść input
      newBackupDirectory.value = ''
    } else {
      backupMessage.value = response.error || 'Błąd podczas zmiany katalogu'
      backupMessageType.value = 'error'
    }
  } catch (error) {
    console.error('Error changing backup directory:', error)
    backupMessage.value = 'Błąd podczas zmiany katalogu backupów'
    backupMessageType.value = 'error'
  } finally {
    changingDirectory.value = false
    
    // Ukryj wiadomość po 5 sekundach
    setTimeout(() => {
      backupMessage.value = ''
    }, 5000)
  }
}

const createBackup = async () => {
  if (!selectedCluster.value) return
  
  creatingBackup.value = true
  backupMessage.value = ''
  
  try {
    const response = await ApiService.createBackup(selectedCluster.value, backupName.value || undefined)
    
    if (response.success) {
      backupMessage.value = response.message
      backupMessageType.value = 'success'
      backupName.value = ''
      await loadBackups()
    } else {
      backupMessage.value = response.error || response.message
      backupMessageType.value = 'error'
    }
  } catch (error) {
    backupMessage.value = `Błąd: ${error}`
    backupMessageType.value = 'error'
  } finally {
    creatingBackup.value = false
  }
}

const downloadBackup = async (backupName: string) => {
  try {
    const blob = await ApiService.downloadBackup(backupName)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.style.display = 'none'
    a.href = url
    a.download = `${backupName}.zip`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  } catch (error) {
    console.error('Download error:', error)
    alert('Błąd podczas pobierania backupu')
  }
}

const viewBackupDetails = async (backup: BackupInfo) => {
  try {
    const response = await ApiService.getBackupDetails(backup.backup_name)
    if (response.success && response.backup_details) {
      selectedBackupDetails.value = response.backup_details
      showDetailsModal.value = true
    }
  } catch (error) {
    console.error('Error loading backup details:', error)
  }
}

const confirmDeleteBackup = (backupName: string) => {
  backupToDelete.value = backupName
  showDeleteModal.value = true
}

const confirmRestoreBackup = (backupName: string) => {
  backupToRestore.value = backupName
  restoreClusterName.value = ''
  showRestoreModal.value = true
}

const deleteBackup = async () => {
  deletingBackup.value = true
  try {
    const response = await ApiService.deleteBackup(backupToDelete.value)
    if (response.success) {
      showDeleteModal.value = false
      await loadBackups()
    } else {
      alert(response.error || 'Błąd podczas usuwania backupu')
    }
  } catch (error) {
    console.error('Delete error:', error)
    alert('Błąd podczas usuwania backupu')
  } finally {
    deletingBackup.value = false
    backupToDelete.value = ''
  }
}

const restoreBackup = async () => {
  restoringBackup.value = true
  try {
    const response = await ApiService.restoreBackup(backupToRestore.value, restoreClusterName.value || undefined)
    if (response.success) {
      showRestoreModal.value = false
      alert(response.message)
      // Optionally reload clusters or navigate to clusters view
    } else {
      alert(response.error || 'Błąd podczas przywracania backupu')
    }
  } catch (error) {
    console.error('Restore error:', error)
    alert('Błąd podczas przywracania backupu')
  } finally {
    restoringBackup.value = false
    backupToRestore.value = ''
    restoreClusterName.value = ''
  }
}

const formatDate = (dateString: string) => {
  try {
    const date = new Date(dateString)
    return date.toLocaleString('pl-PL')
  } catch {
    return dateString
  }
}
</script>
