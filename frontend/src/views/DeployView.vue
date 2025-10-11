<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Nagłówek z nawigacją -->
    <header class="bg-white shadow-sm sticky top-0 z-10">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex justify-between items-center">
          <h1 class="text-2xl font-bold text-gray-900">ClusterMaster</h1>
          
          <!-- Nawigacja -->
          <nav class="hidden md:flex space-x-6">
            <router-link 
              to="/" 
              class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              :class="{ 'bg-gray-100 text-gray-900': $route.path === '/' }"
            >
              🏠 Pulpit
            </router-link>
            <router-link 
              to="/deploy" 
              class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              :class="{ 'bg-gray-100 text-gray-900': $route.path === '/deploy' }"
            >
              🚀 Deploy
            </router-link>
            <router-link 
              to="/monitoring" 
              class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              :class="{ 'bg-gray-100 text-gray-900': $route.path === '/monitoring' }"
            >
              📊 Monitoring
            </router-link>
            <router-link 
              to="/backup" 
              class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              :class="{ 'bg-gray-100 text-gray-900': $route.path === '/backup' }"
            >
              🗂️ Backup
            </router-link>
          </nav>
          
          <div class="flex items-center space-x-4">
            <button 
              @click="$router.push('/')" 
              class="text-gray-600 hover:text-gray-900 text-sm"
            >
              ← Powrót
            </button>
          </div>
        </div>
      </div>
    </header>
    
    <div class="max-w-4xl mx-auto px-4 py-8">
      <!-- Loading Overlay -->
      <div v-if="isLoading" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white p-8 rounded-lg shadow-xl max-w-md w-full mx-4">
          <div class="text-center">
            <!-- Spinner -->
            <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            
            <!-- Status Message -->
            <h3 class="text-lg font-semibold text-gray-900 mb-2">
              Tworzenie klastra...
            </h3>
            <p class="text-sm text-gray-600 mb-4">{{ statusMessage }}</p>
            
            <!-- Progress Bar -->
            <div class="w-full bg-gray-200 rounded-full h-2 mb-4">
              <div 
                class="bg-blue-600 h-2 rounded-full transition-all duration-500 ease-out"
                :style="{ width: `${progress}%` }"
              ></div>
            </div>
            
            <!-- Progress Percentage -->
            <div class="text-xs text-gray-500">{{ Math.round(progress) }}%</div>
            
            <!-- Anuluj (tylko jeśli nie jest prawie skończone) -->
            <button 
              v-if="progress < 90"
              @click="handleCancel"
              class="mt-4 text-sm text-gray-500 hover:text-gray-700"
            >
              Anuluj
            </button>
          </div>
        </div>
      </div>

      <!-- Header -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <h1 class="text-2xl font-bold text-gray-900 mb-2">Nowy Klaster</h1>
        <p class="text-gray-600">Skonfiguruj i utwórz nowy klaster Kubernetes</p>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSubmit" class="space-y-6">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div class="space-y-6">
            <div class="border-b border-gray-100 pb-6">
              <label for="provider" class="block text-gray-700 font-medium mb-2">Tryb klastra</label>
              <select
                id="provider"
                v-model="form.provider"
                class="form-input w-full rounded-md bg-gray-50 border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200"
                required
              >
                <option value="local">Lokalny (Kind / Minikube)</option>
                <option value="aws">AWS (EKS)</option>
              </select>
            </div>

            <div>
              <label for="clusterName" class="block text-gray-700 font-medium mb-2">Nazwa klastra</label>
              <input
                id="clusterName"
                v-model="form.clusterName"
                type="text"
                placeholder="np. klaster-produkcyjny"
                class="form-input w-full rounded-md bg-gray-50 border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200"
                required
              />
            </div>

            <div>
              <label for="nodeCount" class="block text-gray-700 font-medium mb-2">Liczba węzłów</label>
              <div class="flex items-center">
                <input
                  id="nodeCount"
                  v-model.number="form.nodeCount"
                  type="number"
                  min="1"
                  class="form-input w-36 rounded-md bg-gray-50 border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200"
                  required
                />
                <div class="ml-3">
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {{ form.nodeCount }} {{ form.nodeCount === 1 ? 'węzeł' : form.nodeCount < 5 ? 'węzły' : 'węzłów' }}
                  </span>
                </div>
              </div>
            </div>

            <div v-if="form.provider === 'aws'" class="space-y-4 pt-4">
              <h3 class="text-lg font-medium text-gray-800 mb-4 border-t border-gray-100 pt-4">Konfiguracja AWS</h3>
              
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label for="awsRegion" class="block text-gray-700 font-medium mb-2">Region AWS</label>
                  <input
                    id="awsRegion"
                    v-model="form.awsRegion"
                    type="text"
                    placeholder="np. eu-central-1"
                    class="form-input w-full rounded-md bg-gray-50 border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200"
                    required
                  />
                </div>
                
                <div>
                  <label for="vpcCidr" class="block text-gray-700 font-medium mb-2">CIDR dla VPC</label>
                  <input
                    id="vpcCidr"
                    v-model="form.vpcCidr"
                    type="text"
                    placeholder="10.0.0.0/16"
                    class="form-input w-full rounded-md bg-gray-50 border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200"
                    required
                  />
                </div>
              </div>
              
              <div>
                <label for="instanceType" class="block text-gray-700 font-medium mb-2">Typ instancji EC2</label>
                <select 
                  id="instanceType" 
                  v-model="form.instanceType" 
                  class="form-input w-full rounded-md bg-gray-50 border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200" 
                  required
                >
                  <option value="">— wybierz typ —</option>
                  <option value="t3.small" class="py-1">t3.small (1 CPU, 2 GB RAM)</option>
                  <option value="t3.medium" class="py-1">t3.medium (2 CPU, 4 GB RAM)</option>
                  <option value="m5.large" class="py-1">m5.large (2 CPU, 8 GB RAM)</option>
                  <option value="m5.xlarge" class="py-1">m5.xlarge (4 CPU, 16 GB RAM)</option>
                </select>
              </div>
              
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label for="awsAccessKey" class="block text-gray-700 font-medium mb-2">AWS Access Key ID</label>
                  <input
                    id="awsAccessKey"
                    v-model="form.awsAccessKey"
                    type="text"
                    class="form-input w-full rounded-md bg-gray-50 border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200"
                    required
                  />
                </div>
                <div>
                  <label for="awsSecretKey" class="block text-gray-700 font-medium mb-2">AWS Secret Access Key</label>
                  <input
                    id="awsSecretKey"
                    v-model="form.awsSecretKey"
                    type="password"
                    class="form-input w-full rounded-md bg-gray-50 border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200"
                    required
                  />
                </div>
              </div>
            </div>
            
            <div v-else class="pt-4">
              <h3 class="text-lg font-medium text-gray-800 mb-4 border-t border-gray-100 pt-4">Konfiguracja lokalna</h3>
              
              <!-- K3D vs Kind Selection -->
              <div class="mb-6">
                <label class="block text-gray-700 font-medium mb-3">Provider lokalnego klastra</label>
                <div class="grid grid-cols-2 gap-4">
                  <button
                    type="button"
                    @click="form.localClusterType = 'kind'"
                    class="py-4 px-4 border rounded-lg text-left transition-all"
                    :class="form.localClusterType === 'kind' ? 
                      'bg-blue-50 border-blue-400 shadow-sm' : 
                      'bg-white border-gray-300 hover:border-gray-400'"
                  >
                    <div class="flex items-start">
                      <div class="flex-shrink-0 mr-3">
                        <div class="w-8 h-8 rounded-full flex items-center justify-center"
                          :class="form.localClusterType === 'kind' ? 'bg-blue-500' : 'bg-gray-300'">
                          <span class="text-white text-lg">🔵</span>
                        </div>
                      </div>
                      <div class="flex-1">
                        <div class="font-semibold text-gray-900 mb-1">Kind</div>
                        <div class="text-xs text-gray-600 leading-relaxed">
                          Stabilny i sprawdzony<br>
                          ⚠️ Wymaga rekre...
                        </div>
                      </div>
                    </div>
                  </button>

                  <button
                    type="button"
                    @click="form.localClusterType = 'k3d'"
                    class="py-4 px-4 border rounded-lg text-left transition-all"
                    :class="form.localClusterType === 'k3d' ? 
                      'bg-green-50 border-green-400 shadow-sm' : 
                      'bg-white border-gray-300 hover:border-gray-400'"
                  >
                    <div class="flex items-start">
                      <div class="flex-shrink-0 mr-3">
                        <div class="w-8 h-8 rounded-full flex items-center justify-center"
                          :class="form.localClusterType === 'k3d' ? 'bg-green-500' : 'bg-gray-300'">
                          <span class="text-white text-lg">🚀</span>
                        </div>
                      </div>
                      <div class="flex-1">
                        <div class="font-semibold text-gray-900 mb-1">
                          k3d
                          <span class="ml-1 text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded">ZALECANY</span>
                        </div>
                        <div class="text-xs text-gray-600 leading-relaxed">
                          Lekki i szybki (k3s)<br>
                          ✨ Live scaling bez utraty danych
                        </div>
                      </div>
                    </div>
                  </button>
                </div>
                
                <!-- Info box based on selection -->
                <div v-if="form.localClusterType === 'kind'" 
                  class="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <div class="flex items-start">
                    <span class="text-blue-600 mr-2">ℹ️</span>
                    <div class="text-xs text-blue-800">
                      <strong>Kind (Kubernetes in Docker)</strong> - sprawdzone rozwiązanie do testów.
                      Uwaga: skalowanie wymaga rekreacji klastra (utrata deploymentów).
                    </div>
                  </div>
                </div>
                
                <div v-if="form.localClusterType === 'k3d'" 
                  class="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div class="flex items-start">
                    <span class="text-green-600 mr-2">✨</span>
                    <div class="text-xs text-green-800">
                      <strong>k3d (k3s in Docker)</strong> - lekka dystrybucja Kubernetes.
                      Zalety: szybsze uruchamianie, mniej zasobów, live scaling bez rekreacji!<br>
                      <span class="text-xs text-gray-600 mt-1 block">
                        ⚠️ Wymaga instalacji k3d: <code class="bg-gray-100 px-1">choco install k3d</code> 
                        lub pobierz z <a href="https://k3d.io" target="_blank" class="text-blue-600 underline">k3d.io</a>
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              
              <label for="kubeconfigPath" class="block text-gray-700 font-medium mb-2">Ścieżka kubeconfig</label>
              <input
                id="kubeconfigPath"
                v-model="form.kubeconfigPath"
                type="text"
                placeholder="np. ~/.kube/config"
                class="form-input w-full rounded-md bg-gray-50 border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200"
                required
              />
            </div>
          </div>
          
          <div class="space-y-6">
            <div>
              <h3 class="text-lg font-medium text-gray-800 mb-4">Profil i zasoby</h3>
              
              <label for="clusterProfile" class="block text-gray-700 font-medium mb-2">Profil klastra</label>
              <div class="grid grid-cols-3 gap-4 mb-4">
                <button 
                  type="button" 
                  @click="form.clusterProfile = 'developerski'"
                  class="py-3 px-4 border rounded-lg text-center transition-colors"
                  :class="form.clusterProfile === 'developerski' ? 
                    'bg-blue-50 border-blue-300 text-blue-700' : 
                    'bg-gray-50 border-gray-300 text-gray-700 hover:bg-gray-100'"
                >
                  <div class="font-medium">Developerski</div>
                  <div class="text-xs mt-1">2 CPU / 4 GB RAM</div>
                </button>
                
                <button 
                  type="button" 
                  @click="form.clusterProfile = 'testowy'"
                  class="py-3 px-4 border rounded-lg text-center transition-colors"
                  :class="form.clusterProfile === 'testowy' ? 
                    'bg-green-50 border-green-300 text-green-700' : 
                    'bg-gray-50 border-gray-300 text-gray-700 hover:bg-gray-100'"
                >
                  <div class="font-medium">Testowy</div>
                  <div class="text-xs mt-1">4 CPU / 8 GB RAM</div>
                </button>
                
                <button 
                  type="button" 
                  @click="form.clusterProfile = 'produkcyjny'"
                  class="py-3 px-4 border rounded-lg text-center transition-colors"
                  :class="form.clusterProfile === 'produkcyjny' ? 
                    'bg-amber-50 border-amber-300 text-amber-700' : 
                    'bg-gray-50 border-gray-300 text-gray-700 hover:bg-gray-100'"
                >
                  <div class="font-medium">Produkcyjny</div>
                  <div class="text-xs mt-1">8 CPU / 16 GB RAM</div>
                </button>
              </div>
              
              <input type="hidden" v-model="form.clusterProfile" />
              
              <p class="text-sm text-gray-600 mb-4 italic">
                Wybór profilu automatycznie ustawia zalecane wartości zasobów dla każdego węzła.
              </p>
            </div>

            <div class="bg-gray-50 p-4 rounded-lg">
              <div class="flex items-center justify-between mb-3">
                <label class="block text-gray-700 font-medium">Niestandardowe zasoby (opcjonalnie)</label>
                <span class="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-md">Własne ustawienia</span>
              </div>
              
              <div class="grid grid-cols-3 gap-4">
                <div>
                  <label for="cpu" class="block text-gray-600 text-sm mb-1">CPU (rdzenie)</label>
                  <input
                    id="cpu"
                    v-model.number="form.cpu"
                    type="number"
                    min="1"
                    class="form-input w-full rounded-md bg-white border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200"
                    placeholder="np. 2"
                  />
                </div>
                <div>
                  <label for="memory" class="block text-gray-600 text-sm mb-1">Pamięć (GB)</label>
                  <input
                    id="memory"
                    v-model.number="form.memory"
                    type="number"
                    min="1"
                    class="form-input w-full rounded-md bg-white border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200"
                    placeholder="np. 4"
                  />
                </div>
                <div>
                  <label for="disk" class="block text-gray-600 text-sm mb-1">Dysk (GB)</label>
                  <input
                    id="disk"
                    v-model.number="form.disk"
                    type="number"
                    min="20"
                    class="form-input w-full rounded-md bg-white border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200"
                    placeholder="np. 100"
                  />
                </div>
              </div>
              
              <p class="text-xs text-gray-500 mt-2">
                Pozostaw puste, aby użyć domyślnych wartości z wybranego profilu.
              </p>
            </div>

            <details class="bg-gray-50 p-5 rounded-xl border border-gray-200 group">
              <summary class="cursor-pointer font-semibold text-gray-700 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2 text-gray-500 group-open:rotate-90 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
                Opcje zaawansowane
              </summary>
              
              <div class="mt-4 space-y-5 pt-4 border-t border-gray-200">
                <div>
                  <label for="k8sVersion" class="block text-gray-700 font-medium mb-2">Wersja Kubernetes</label>
                  <select 
                    id="k8sVersion" 
                    v-model="form.k8sVersion" 
                    class="form-input w-full rounded-md bg-white border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200"
                  >
                    <option value="">(domyślna wersja)</option>
                    <option value="1.24">1.24</option>
                    <option value="1.25">1.25</option>
                    <option value="1.26">1.26</option>
                  </select>
                </div>
                
                <div class="p-4 bg-white rounded-lg border border-gray-200">
                  <label class="flex items-center mb-3">
                    <input 
                      type="checkbox" 
                      v-model="form.enableAutoscaling" 
                      class="rounded text-blue-600 focus:ring-blue-500 border-gray-300"
                    />
                    <span class="ml-2 font-medium text-gray-700">Włącz autoskalowanie</span>
                  </label>
                  
                  <div v-if="form.enableAutoscaling" class="mt-3 grid grid-cols-2 gap-4">
                    <div>
                      <label for="minNodes" class="block text-gray-700 text-sm mb-1">Min. węzłów</label>
                      <input
                        id="minNodes"
                        v-model.number="form.minNodes"
                        type="number"
                        min="1"
                        class="form-input w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200"
                      />
                    </div>
                    <div>
                      <label for="maxNodes" class="block text-gray-700 text-sm mb-1">Max. węzłów</label>
                      <input
                        id="maxNodes"
                        v-model.number="form.maxNodes"
                        type="number"
                        min="1"
                        class="form-input w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200"
                      />
                    </div>
                  </div>
                </div>
                
                <div>
                  <label for="tags" class="block text-gray-700 font-medium mb-2">Tagi</label>
                  <input
                    id="tags"
                    v-model="form.tags"
                    type="text"
                    placeholder="np. env=dev,team=devops"
                    class="form-input w-full rounded-md bg-white border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200"
                  />
                  <p class="text-xs text-gray-500 mt-1">
                    Format: key=value, oddzielone przecinkami
                  </p>
                </div>
              </div>
            </details>

            <!-- Dodaj po sekcji z opcjami zaawansowanymi -->
            <div class="bg-blue-50 p-4 rounded-lg border border-blue-200 mt-6">
              <label class="flex items-start">
                <input 
                  type="checkbox" 
                  v-model="form.installMonitoring" 
                  class="mt-1 mr-3 rounded text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <span class="font-medium text-blue-800">🔍 Zainstaluj stack monitoringu</span>
                  <p class="text-sm text-blue-700 mt-1">
                    Automatycznie zainstaluje Prometheus i Grafana po utworzeniu klastra przy użyciu Helm
                  </p>
                  <p class="text-xs text-blue-600 mt-1">
                    📊 Prometheus: http://localhost:30900 | 📈 Grafana: http://localhost:30300 (admin/admin123)
                  </p>
                </div>
              </label>
            </div>
          </div>
        </div>

        <!-- Buttons -->
        <div class="flex justify-end space-x-4 pt-6 border-t border-gray-200">
          <button
            type="button"
            @click="handleCancel"
            :disabled="isLoading"
            class="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Anuluj
          </button>
          <button
            type="submit"
            :disabled="isLoading || !form.clusterName"
            class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <span v-if="isLoading" class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
            <span>{{ isLoading ? 'Tworzenie...' : '+ Utwórz klaster' }}</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue"
import { useRouter } from "vue-router"
import { ApiService } from "@/services/api"

const router = useRouter()
const isLoading = ref(false)
const progress = ref(0)
const statusMessage = ref("")

const form = reactive({
  provider: "local",
  localClusterType: "k3d", // "kind" or "k3d" - default to k3d for better scaling
  clusterName: "",
  nodeCount: 2,

  // AWS
  awsRegion: "",
  instanceType: "",
  vpcCidr: "",
  awsAccessKey: "",
  awsSecretKey: "",

  kubeconfigPath: "",

  clusterProfile: "developerski",

  cpu: null as number | null,
  memory: null as number | null,
  disk: null as number | null,

  k8sVersion: "",
  enableAutoscaling: false,
  minNodes: 1,
  maxNodes: 1,
  tags: "",
  installMonitoring: false,
})

function simulateProgress() {
  progress.value = 0
  const interval = setInterval(() => {
    progress.value += Math.random() * 15
    if (progress.value >= 95) {
      progress.value = 95
      clearInterval(interval)
    }
  }, 1000)
  return interval
}

function validateClusterName(name: string): boolean {
  const dnsRegex = /^[a-z0-9-]+$/
  return dnsRegex.test(name) && name.length > 0 && name.length <= 63
}

async function handleSubmit() {
  if (!form.clusterName) {
    alert("Podaj nazwę klastra.")
    return
  }
  
  if (!validateClusterName(form.clusterName)) {
    alert("Nazwa klastra może zawierać tylko małe litery, cyfry i myślniki (np. 'test-cluster')")
    return
  }
  
  if (form.nodeCount < 1) {
    alert("Liczba węzłów musi być ≥ 1.")
    return
  }

  isLoading.value = true
  statusMessage.value = "Sprawdzanie środowiska..."
  const progressInterval = simulateProgress()

  try {
    // First check if backend is available
    statusMessage.value = "Łączenie z API..."
    await ApiService.healthCheck()
    
    statusMessage.value = "Sprawdzanie Docker i Kind..."
    await new Promise(resolve => setTimeout(resolve, 500))
    
    statusMessage.value = `Tworzenie klastra "${form.clusterName}"...`
    if (form.installMonitoring) {
      statusMessage.value += " (z monitoringiem)"
    }
    
    // Create cluster with monitoring flag and provider
    const clusterData = {
      cluster_name: form.clusterName,
      node_count: form.nodeCount,
      k8s_version: form.k8sVersion || undefined,
      install_monitoring: form.installMonitoring,  // Backend obsłuży instalację
      provider: form.provider === 'local' ? form.localClusterType : 'aws' // Send kind/k3d for local
    }
    
    console.log('Creating cluster with data:', clusterData)
    
    const result = await ApiService.createCluster(clusterData)
    
    console.log('Backend response:', result)
    
    clearInterval(progressInterval)
    progress.value = 100
    
    // Check for errors from backend
    if (result.status === 'error' || result.error) {
      const errorMsg = result.error || "Nieznany błąd podczas tworzenia klastra"
      console.error('Cluster creation failed:', errorMsg)
      throw new Error(errorMsg)
    }
    
    if (result.status === 'success' || result.message) {
      statusMessage.value = result.message || "Klaster utworzony pomyślnie!"
    } else {
      throw new Error("Nieznany błąd podczas tworzenia klastra")
    }
    
    // Wait a bit to show success
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    // Navigate to home with success message
    router.push({
      path: "/",
      query: { 
        success: "true", 
        cluster: form.clusterName,
        message: result.message,
        monitoring: form.installMonitoring ? "true" : "false"
      }
    })
    
  } catch (error: any) {
    clearInterval(progressInterval)
    progress.value = 0
    statusMessage.value = `Błąd: ${error.message}`
    console.error("Błąd tworzenia klastra:", error)
    
    // Show error for 3 seconds
    setTimeout(() => {
      isLoading.value = false
      statusMessage.value = ""
    }, 3000)
  }
}

function handleCancel() {
  if (isLoading.value) {
    if (!confirm("Tworzenie klastra jest w toku. Czy na pewno chcesz anulować?")) {
      return
    }
  }
  router.push("/")
}
</script>

<style scoped>
details > summary::-webkit-details-marker {
  display: none;
}

.form-input {
  @apply transition-colors duration-200;
}

@media (max-width: 1023px) {
  .grid-cols-3 {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
