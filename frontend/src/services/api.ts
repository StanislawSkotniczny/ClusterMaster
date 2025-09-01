// Serwis do komunikacji z backend API
const API_BASE_URL = 'http://localhost:8000/api/v1'

export interface ClusterCreateRequest {
    cluster_name: string
    node_count: number
    k8s_version?: string
}

export interface ClusterResponse {
    cluster_name: string
    status: string
    message: string
}

export class ApiService {
    private static async request(endpoint: string, options: RequestInit = {}) {
        const url = `${API_BASE_URL}${endpoint}`

        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        })

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`)
        }

        return response.json()
    }

    // Health check
    static async healthCheck() {
        return this.request('/health')
    }

    // Klastry lokalne
    static async listClusters(): Promise<{ clusters: string[] }> {
        return this.request('/local-cluster/list')
    }

    static async createCluster(data: ClusterCreateRequest): Promise<ClusterResponse> {
        return this.request('/local-cluster/create', {
            method: 'POST',
            body: JSON.stringify(data),
        })
    }

    static async deleteCluster(clusterName: string): Promise<{ message: string }> {
        return this.request(`/local-cluster/${clusterName}`, {
            method: 'DELETE',
        })
    }

    static async getClusterStatus(clusterName: string) {
        return this.request(`/local-cluster/${clusterName}/status`)
    }

    // Debug endpoints
    static async debugDocker() {
        return this.request('/debug/docker')
    }

    static async debugKind() {
        return this.request('/debug/kind')
    }

    // Monitoring
    static async installMonitoring(clusterName: string) {
        return this.request(`/monitoring/install/${clusterName}`, {
            method: 'POST',
        })
    }

    static async getMonitoringStatus(clusterName: string) {
        return this.request(`/monitoring/status/${clusterName}`)
    }
}