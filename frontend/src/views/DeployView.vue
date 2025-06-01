<template>
  <div class="min-h-screen bg-gray-50 py-6 px-4 sm:px-6 lg:px-8">
    <div class="max-w-7xl mx-auto">
      <div class="mb-6">
        <h1 class="text-2xl font-bold text-gray-900 mb-1">Nowy Klaster</h1>
        <p class="text-sm text-gray-600">Skonfiguruj i utwórz nowy klaster Kubernetes</p>
      </div>
      
      <form @submit.prevent="handleSubmit" class="bg-white p-6 rounded-xl shadow-lg border border-gray-100">
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
          </div>
        </div>

        <div class="flex justify-end items-center pt-6 mt-8 border-t border-gray-100">
          <button 
            type="button" 
            @click="handleCancel" 
            class="px-5 py-2.5 rounded-lg border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 transition-colors mr-4"
          >
            Anuluj
          </button>
          
          <button 
            type="submit" 
            class="px-6 py-2.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors shadow-sm flex items-center"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Utwórz klaster
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from "vue"
import { defineEmits } from "vue"
import { useRouter } from "vue-router"

const emit = defineEmits<{
  (e: "submitted", config: Record<string, unknown>): void
}>()

const router = useRouter()

const form = reactive({
  // wspolne
  provider: "local",
  clusterName: "",
  nodeCount: 1,

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
})

function handleSubmit() {
  if (!form.clusterName) {
    alert("Podaj nazwę klastra.")
    return
  }
  if (form.nodeCount < 1) {
    alert("Liczba węzłów musi być ≥ 1.")
    return
  }

  const config: Record<string, unknown> = {
    provider: form.provider,
    cluster_name: form.clusterName,
    node_count: form.nodeCount,
  }

  if (form.provider === "aws") {
    if (!form.awsRegion || !form.instanceType || !form.vpcCidr || !form.awsAccessKey || !form.awsSecretKey) {
      alert("Wypełnij wszystkie pola AWS.")
      return
    }
    Object.assign(config, {
      aws_region: form.awsRegion,
      instance_type: form.instanceType,
      vpc_cidr: form.vpcCidr,
      aws_access_key: form.awsAccessKey,
      aws_secret_key: form.awsSecretKey,
    })
  } else {
    if (!form.kubeconfigPath) {
      alert("Podaj ścieżkę kubeconfig.")
      return
    }
    Object.assign(config, {
      kubeconfig_path: form.kubeconfigPath,
    })
  }
  if (!form.cpu && !form.memory && !form.disk) {
    if (form.clusterProfile === "developerski") {
      form.cpu = 2
      form.memory = 4
      form.disk = 50
    } else if (form.clusterProfile === "testowy") {
      form.cpu = 4
      form.memory = 8
      form.disk = 100
    } else if (form.clusterProfile === "produkcyjny") {
      form.cpu = 8
      form.memory = 16
      form.disk = 200
    }
  }

  if (form.cpu && form.memory && form.disk) {
    Object.assign(config, {
      cpu: form.cpu,
      memory: form.memory,
      disk: form.disk,
    })
  }


  if (form.k8sVersion) {
    config.k8s_version = form.k8sVersion
  }
  if (form.enableAutoscaling) {
    if (form.minNodes < 1 || form.maxNodes < form.minNodes) {
      alert("Sprawdź wartości min/max dla autoskalowania.")
      return
    }
    Object.assign(config, {
      enable_autoscaling: true,
      min_nodes: form.minNodes,
      max_nodes: form.maxNodes,
    })
  }
  if (form.tags) {
    const tagsObj: Record<string, string> = {}
    form.tags.split(",").forEach(pair => {
      const [k, v] = pair.split("=")
      if (k && v) tagsObj[k.trim()] = v.trim()
    })
    config.tags = tagsObj
  }


  emit("submitted", config)
}

function handleCancel() {
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
