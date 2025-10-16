from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import os
import shutil
import tempfile
import yaml
import json
from app.services.helm_service import helm_service
from app.services.port_manager import port_manager
from app.services.backup_service import BackupService
from app.services.app_service import AppService
from app.services.k3d_service import k3d_service
import argparse
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Optional

# Parse command line arguments
def parse_args():
    parser = argparse.ArgumentParser(description='ClusterMaster Backend API')
    parser.add_argument('--backup-dir', type=str, help='Directory to store backup files')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on')
    return parser.parse_args()

# Initialize services - check if we're being run directly or through run.py
if __name__ == "__main__":
    args = parse_args()
    backup_service = BackupService(backup_dir=args.backup_dir)
else:
    # When imported (e.g., by uvicorn), check environment variable
    backup_dir = os.environ.get('CLUSTER_BACKUP_DIR')
    backup_service = BackupService(backup_dir=backup_dir)

# Initialize services
app_service = AppService()

_cluster_cache = {}
_cache_ttl_fast = timedelta(seconds=3)  # Szybkie cache dla list (3s)
_cache_ttl_full = timedelta(seconds=2)  # Pełne cache dla szczegółów (2s)  

def get_from_cache(key: str, use_fast_ttl: bool = False) -> Optional[dict]:
    """Pobierz wartość z cache jeśli jest aktualna"""
    if key in _cluster_cache:
        data, timestamp = _cluster_cache[key]
        ttl = _cache_ttl_fast if use_fast_ttl else _cache_ttl_full
        if datetime.now() - timestamp < ttl:
            return data
    return None

def set_in_cache(key: str, data: dict):
    """Zapisz wartość w cache"""
    _cluster_cache[key] = (data, datetime.now())

app = FastAPI(title="ClusterMaster API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def find_kind_executable():
    """Znajdź ścieżkę do kind.exe"""
    # Sprawdź czy kind jest w PATH
    kind_path = shutil.which("kind")
    if kind_path:
        return kind_path
    
    # Sprawdź typowe lokalizacje na Windows
    possible_paths = [
        "C:\\tools\\kind.exe",
        "C:\\Program Files\\kind\\kind.exe",
        "C:\\Windows\\System32\\kind.exe",
        os.path.expanduser("~\\AppData\\Local\\Programs\\kind\\kind.exe")
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

def run_kind_command(args, timeout=30):
    """Uruchom komendę kind z obsługą błędów"""
    kind_path = find_kind_executable()
    
    if not kind_path:
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": "Kind nie został znaleziony. Sprawdź instalację."
        }
    
    try:
        cmd = [kind_path] + args
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=timeout,
            encoding='utf-8',  # DODANE: wymuszenie UTF-8
            errors='replace',  # DODANE: zastąp problematyczne znaki
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": f"Komenda przekroczyła limit czasu ({timeout}s)"
        }
    except Exception as e:
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": str(e)
        }

def create_kind_config(cluster_name, node_count, cluster_ports=None):
    """Utwórz plik konfiguracyjny Kind z mapowaniem portów dla monitoringu"""
    
    config = {
        "kind": "Cluster",
        "apiVersion": "kind.x-k8s.io/v1alpha4",
        "nodes": []
    }
    
    # Control plane z mapowaniem portów dla NodePort monitoringu
    control_plane_node = {
        "role": "control-plane",
        "extraPortMappings": []
    }
    
    # Jeśli podano porty, użyj ich, inaczej użyj domyślnych
    if cluster_ports:
        control_plane_node["extraPortMappings"] = [
            {
                "containerPort": cluster_ports["prometheus"],
                "hostPort": cluster_ports["prometheus"],
                "protocol": "TCP"
            },
            {
                "containerPort": cluster_ports["grafana"],
                "hostPort": cluster_ports["grafana"],
                "protocol": "TCP"
            }
        ]
    else:
        # Domyślne porty dla backward compatibility
        control_plane_node["extraPortMappings"] = [
            {
                "containerPort": 30090,  # Prometheus NodePort
                "hostPort": 30090,       # Host port dla Prometheus
                "protocol": "TCP"
            },
            {
                "containerPort": 30030,  # Grafana NodePort  
                "hostPort": 30030,       # Host port dla Grafana
                "protocol": "TCP"
            }
        ]
    
    config["nodes"].append(control_plane_node)
    
    # Dodaj worker nodes (bez mapowania portów)
    for i in range(node_count - 1):
        config["nodes"].append({"role": "worker"})
    
    # Zapisz konfigurację do tymczasowego pliku
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f, default_flow_style=False)
        print(f"Created Kind config: {f.name}")
        print(f"Config content: {config}")
        return f.name

@app.get("/")
async def root():
    return {"message": "ClusterMaster API is running"}

def parse_node_metrics(metrics_output: str) -> dict:
    """Parsuj output z kubectl top nodes"""
    lines = metrics_output.strip().split('\n')
    total_cpu_usage = 0
    total_memory_usage = 0
    node_count = len(lines)
    nodes_info = []
    
    for line in lines:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 3:
            node_name = parts[0]
            cpu_usage = parts[1]  # np. "100m" lub "1"
            memory_usage = parts[2]  # np. "1000Mi" lub "1Gi"
            
            nodes_info.append({
                "name": node_name,
                "cpu": cpu_usage,
                "memory": memory_usage
            })
    
    return {
        "node_count": node_count,
        "nodes": nodes_info,
        "summary": f"{node_count} wezlow"
    }

def get_basic_node_info(cluster_name: str) -> dict:
    """Pobierz podstawowe informacje o węzłach gdy metryki nie są dostępne"""
    try:
        # Wykryj provider klastra
        provider = detect_cluster_provider(cluster_name)
        context = f"{provider}-{cluster_name}"
        
        nodes_result = subprocess.run([
            "kubectl", "get", "nodes", "--context", context,
            "-o", r"custom-columns=NAME:.metadata.name,STATUS:.status.conditions[-1].type,ROLES:.metadata.labels.node-role\.kubernetes\.io/control-plane",
            "--no-headers"
        ], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=5)
        
        if nodes_result.returncode == 0:
            lines = nodes_result.stdout.strip().split('\n')
            nodes_info = []
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        nodes_info.append({
                            "name": parts[0],
                            "status": parts[1],
                            "role": "control-plane" if len(parts) > 2 and parts[2] else "worker"
                        })
            
            return {
                "node_count": len(nodes_info),
                "nodes": nodes_info,
                "summary": f"{len(nodes_info)} wezlow",
                "note": "Podstawowe informacje (uzyj 'kubectl describe nodes' dla wiecej)"
            }
    except:
        pass
    
    return {
        "error": "Nie mozna pobrac informacji o wezlach",
        "node_count": 0
    }

def detect_cluster_provider(cluster_name: str) -> str:
    """Wykryj providera klastra (kind lub k3d)"""
    # Sprawdź k3d clusters (z obsługą błędów)
    try:
        k3d_clusters = k3d_service.list_clusters()
        if cluster_name in k3d_clusters:
            return "k3d"
    except Exception as e:
        print(f"Nie można sprawdzić klastrów k3d: {e}")
    
    # Sprawdź kind clusters
    try:
        kind_result = run_kind_command(["get", "clusters"])
        if kind_result["returncode"] == 0 and cluster_name in kind_result["stdout"]:
            return "kind"
    except Exception as e:
        print(f"Nie można sprawdzić klastrów Kind: {e}")
    
    # Default to kind if unknown
    return "kind"

def get_enhanced_node_info(cluster_name: str) -> dict:
    """Pobierz rozszerzone informacje o węzłach używając Docker stats"""
    try:
        # Wykryj provider klastra
        provider = detect_cluster_provider(cluster_name)
        context = f"{provider}-{cluster_name}"
        
        # Najpierw pobierz nazwy węzłów
        nodes_result = subprocess.run([
            "kubectl", "get", "nodes", "--context", context,
            "-o", "json"
        ], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=5)
        
        if nodes_result.returncode != 0:
            return get_basic_node_info(cluster_name)
        
        # Parse JSON response
        import json
        nodes_data = json.loads(nodes_result.stdout)
        node_names = [item['metadata']['name'] for item in nodes_data['items']]
        
      
        if node_names:
            docker_stats = subprocess.run([
                "docker", "stats", "--no-stream", "--format", 
                "{{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
            ] + node_names, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=5)
            
            # Parse stats
            stats_map = {}
            if docker_stats.returncode == 0:
                lines = docker_stats.stdout.strip().split('\n')
                for line in lines:
                    parts = line.split('\t')
                    if len(parts) >= 4:
                        container_name = parts[0]
                        stats_map[container_name] = {
                            'cpu': parts[1],
                            'memory': parts[2],
                            'memory_percent': parts[3]
                        }
        
        nodes_info = []
        for node_name in node_names:
            role = "control-plane" if "control-plane" in node_name else "worker"
            
            stats = stats_map.get(node_name, {})
            node_info = {
                "name": node_name,
                "role": role,
                "cpu_usage": stats.get('cpu', 'N/A'),
                "memory_usage": stats.get('memory', 'N/A'),
                "memory_percent": stats.get('memory_percent', 'N/A'),
                "status": "Ready"
            }
            nodes_info.append(node_info)
        
        return {
            "node_count": len(nodes_info),
            "nodes": nodes_info,
            "summary": f"{len(nodes_info)} wezlow",
            "type": "docker_stats",
            "note": "Metryki z Docker (zywe dane CPU/RAM)"
        }
        
    except Exception as e:
        return get_basic_node_info(cluster_name)

async def get_cluster_details_async(cluster_name: str, include_resources: bool = True) -> dict:
    """Asynchronicznie pobierz szczegóły klastra (Kind lub k3d)"""
    loop = asyncio.get_event_loop()
    
    # Wykryj provider klastra
    provider = detect_cluster_provider(cluster_name)
    
    cluster_info = {
        "name": cluster_name,
        "status": "unknown",
        "context": f"{provider}-{cluster_name}",
        "provider": provider
    }
    
    # Użyj ThreadPoolExecutor do wykonania operacji blokujących równolegle
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Sprawdź status klastra
        async def check_status():
            try:
                result = await loop.run_in_executor(
                    executor,
                    lambda: subprocess.run([
                        "kubectl", "get", "nodes", "--context", f"{provider}-{cluster_name}"
                    ], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=1)
                )
                
                if result.returncode == 0:
                    cluster_info["status"] = "ready"
                    # Policz węzły
                    nodes_lines = result.stdout.strip().split('\n')
                    cluster_info["node_count"] = len(nodes_lines) - 1 if len(nodes_lines) > 1 else 0
                else:
                    cluster_info["status"] = "error"
            except Exception as e:
                cluster_info["status"] = "error"
                print(f"Error checking cluster {cluster_name}: {e}")
        
        # Sprawdź monitoring
        async def check_monitoring():
            try:
                # Sprawdź Helm releases zamiast podów - bardziej niezawodne
                result = await loop.run_in_executor(
                    executor,
                    lambda: subprocess.run([
                        "helm", "list", "--namespace", "monitoring",
                        "--kube-context", f"{provider}-{cluster_name}",
                        "--output", "json"
                    ], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=5)
                )
                
                # Sprawdź czy są oba releases (prometheus i grafana)
                if result.returncode == 0 and result.stdout.strip():
                    import json
                    releases = json.loads(result.stdout)
                    has_prometheus = any('prometheus' in release.get('name', '').lower() for release in releases)
                    has_grafana = any('grafana' in release.get('name', '').lower() for release in releases)
                    cluster_info["monitoring"] = {"installed": bool(has_prometheus and has_grafana)}
                else:
                    cluster_info["monitoring"] = {"installed": False}
            except Exception as e:
                cluster_info["monitoring"] = {"installed": False}
        
        # Pobierz porty
        async def get_ports():
            cluster_ports = port_manager.get_cluster_ports(cluster_name)
            if cluster_ports:
                cluster_info["assigned_ports"] = cluster_ports
        
        # Pobierz zasoby (opcjonalnie - najwolniejsze)
        async def get_resources():
            if include_resources:
                try:
                    resources = await loop.run_in_executor(
                        executor,
                        lambda: get_enhanced_node_info(cluster_name)
                    )
                    cluster_info["resources"] = resources
                except:
                    cluster_info["resources"] = get_basic_node_info(cluster_name)
        
        # Uruchom wszystkie operacje równolegle
        tasks = [check_status(), check_monitoring(), get_ports()]
        if include_resources:
            tasks.append(get_resources())
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    return cluster_info

# ENDPOINTS

@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "service": "ClusterMaster API"}

@app.post("/api/v1/cache/clear")
async def clear_cache():
    """Wyczyść cache klastrów (użyj po usunięciu/dodaniu klastra)"""
    _cluster_cache.clear()
    return {"message": "Cache cleared successfully", "cleared": True}

@app.get("/api/v1/debug/docker")
async def debug_docker():
    """Debug endpoint do sprawdzenia Docker"""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        docker_version = {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
        result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
        docker_ps = {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
        return {
            "docker_version": docker_version,
            "docker_ps": docker_ps,
            "docker_available": docker_version["returncode"] == 0 and docker_ps["returncode"] == 0
        }
    except Exception as e:
        return {
            "error": str(e),
            "docker_available": False
        }

@app.get("/api/v1/debug/kind")
async def debug_kind():
    """Debug endpoint do sprawdzenia Kind"""
    kind_path = find_kind_executable()
    
    if not kind_path:
        return {
            "kind_found": False,
            "kind_path": None,
            "error": "Kind nie został znaleziony"
        }
    
    result = run_kind_command(["version"])
    
    return {
        "kind_found": True,
        "kind_path": kind_path,
        "version_check": {
            "returncode": result["returncode"],
            "stdout": result["stdout"],
            "stderr": result["stderr"]
        }
    }

@app.get("/api/v1/local-cluster/list")
async def list_clusters():
    """Lista klastrów Kind i k3d"""
    all_clusters = []
    
    # Pobierz klastry Kind
    kind_result = run_kind_command(["get", "clusters"])
    if kind_result["returncode"] == 0 and kind_result["stdout"].strip():
        kind_clusters = kind_result["stdout"].strip().split('\n')
        all_clusters.extend(kind_clusters)
    
    # Pobierz klastry k3d
    try:
        k3d_clusters = k3d_service.list_clusters()
        all_clusters.extend(k3d_clusters)
    except Exception as e:
        print(f"Error fetching k3d clusters: {e}")
    
    return {"clusters": all_clusters}

@app.get("/api/v1/local-cluster")
async def list_clusters_detailed(include_resources: bool = False):
    """Lista klastrów Kind i k3d z dodatkowymi informacjami - zoptymalizowana wersja z cache
    
    Args:
        include_resources: Czy dołączyć szczegółowe informacje o zasobach (Docker stats) - wolniejsze
    """
    
    # Sprawdź cache (osobny klucz dla wersji z/bez zasobów)
    cache_key = f"clusters_list_resources_{include_resources}"
    cached_data = get_from_cache(cache_key, use_fast_ttl=not include_resources)
    if cached_data:
        return cached_data
    
    cluster_names = []
    
    # Pobierz klastry Kind
    kind_result = run_kind_command(["get", "clusters"])
    if kind_result["returncode"] == 0 and kind_result["stdout"].strip():
        kind_clusters = [name.strip() for name in kind_result["stdout"].strip().split('\n') if name.strip()]
        cluster_names.extend(kind_clusters)
    
    # Pobierz klastry k3d
    try:
        k3d_clusters = k3d_service.list_clusters()
        cluster_names.extend(k3d_clusters)
    except Exception as e:
        print(f"Error fetching k3d clusters: {e}")
    
    if not cluster_names:
        return {"clusters": []}
    
    # Zbierz szczegółowe informacje o wszystkich klastrach równolegle
    detailed_clusters = await asyncio.gather(
        *[get_cluster_details_async(cluster_name, include_resources) for cluster_name in cluster_names],
        return_exceptions=True
    )
    
    # Filtruj błędy
    valid_clusters = [
        cluster if not isinstance(cluster, Exception) else {
            "name": cluster_names[i] if i < len(cluster_names) else "unknown",
            "status": "error",
            "error": str(cluster)
        }
        for i, cluster in enumerate(detailed_clusters)
    ]
    
    response = {"clusters": valid_clusters}
    
    # Zapisz w cache
    set_in_cache(cache_key, response)
    
    return response

@app.post("/api/v1/local-cluster/create")
async def create_cluster(cluster_data: dict):
    """Utwórz nowy klaster Kind lub k3d"""
    cluster_name = cluster_data.get("cluster_name", "test-cluster")
    node_count = cluster_data.get("node_count", 1)
    k8s_version = cluster_data.get("k8s_version")
    install_monitoring = cluster_data.get("install_monitoring", False)
    provider = cluster_data.get("provider", "kind")  # "kind" lub "k3d"
    
    # Walidacja providera
    if provider not in ["kind", "k3d"]:
        return {"error": f"Nieznany provider: {provider}. Użyj 'kind' lub 'k3d'", "status": "error"}
    
    # === K3D IMPLEMENTATION ===
    if provider == "k3d":
        # Sprawdź czy k3d jest zainstalowany
        if not k3d_service.is_installed():
            return {
                "error": "k3d nie jest zainstalowany. Zainstaluj k3d: https://k3d.io/",
                "status": "error"
            }
        
        # Sprawdź czy klaster już istnieje
        existing_clusters = k3d_service.list_clusters()
        if cluster_name in existing_clusters:
            return {
                "message": f"Klaster {cluster_name} już istnieje",
                "status": "exists",
                "cluster_name": cluster_name,
                "node_count": node_count,
                "provider": "k3d"
            }
        
        try:
            # Przypisz porty dla klastra
            cluster_ports = port_manager.assign_ports_for_cluster(cluster_name)
            
            # k3d używa agents (worker nodes) i servers (control plane)
            # Dla uproszczenia: 1 server + (node_count - 1) agents
            servers = 1
            agents = max(0, node_count - 1)
            
            # Utwórz klaster k3d
            result = k3d_service.create_cluster(
                cluster_name=cluster_name,
                agents=agents,
                servers=servers,
                ports=cluster_ports
            )
            
            if not result["success"]:
                return {
                    "error": f"Nie udało się utworzyć klastra k3d: {result.get('error', 'Unknown error')}",
                    "status": "error",
                    "debug": result
                }
            
            cluster_result = {
                "message": f"Klaster k3d {cluster_name} został utworzony z {agents} agent nodes + {servers} server node = {node_count} węzłów",
                "status": "success",
                "cluster_name": cluster_name,
                "node_count": node_count,
                "agents": agents,
                "servers": servers,
                "context": f"k3d-{cluster_name}",
                "assigned_ports": cluster_ports,
                "provider": "k3d",
                "info": result.get("message", "")
            }
            
            # Wyczyść cache
            _cluster_cache.clear()
            
            # Instalacja monitoringu jeśli zaznaczone
            if install_monitoring:
                print(f"Installing monitoring for k3d cluster {cluster_name}...")
                import time
                time.sleep(15)
                
                try:
                    monitoring_result = helm_service.install_monitoring_stack(cluster_name)
                    if monitoring_result.get("success"):
                        cluster_result["monitoring"] = "installed"
                        cluster_result["monitoring_info"] = monitoring_result.get("message", "")
                    else:
                        cluster_result["monitoring"] = "failed"
                        cluster_result["monitoring_error"] = monitoring_result.get("error", "Unknown error")
                except Exception as e:
                    cluster_result["monitoring"] = "failed"
                    cluster_result["monitoring_error"] = str(e)
            
            return cluster_result
            
        except Exception as e:
            return {"error": f"Błąd podczas tworzenia klastra k3d: {str(e)}", "status": "error"}
    
    # === KIND IMPLEMENTATION (ORIGINAL) ===
    # Sprawdź czy klaster już istnieje
    result = run_kind_command(["get", "clusters"])
    if result["returncode"] == 0 and cluster_name in result["stdout"]:
        return {
            "message": f"Klaster {cluster_name} już istnieje", 
            "status": "exists",
            "cluster_name": cluster_name,
            "node_count": node_count,
            "provider": "kind"
        }
    
    try:
        # Przypisz porty dla klastra przed utworzeniem
        cluster_ports = port_manager.assign_ports_for_cluster(cluster_name)
        
        # Utwórz konfigurację dla wielu węzłów
        config_file = None
        
        args = ["create", "cluster", "--name", cluster_name]
        
        if node_count > 1:
            config_file = create_kind_config(cluster_name, node_count, cluster_ports)
            args.extend(["--config", config_file])
        
        # Dodaj wersję Kubernetes jeśli określona
        if k8s_version:
            args.extend(["--image", f"kindest/node:{k8s_version}"])
        
        # Utwórz klaster (może potrwać kilka minut dla wielu węzłami)
        result = run_kind_command(args, timeout=600)  # 10 minut timeout
        
        # Usuń plik konfiguracyjny
        if config_file:
            import os
            try:
                os.unlink(config_file)
            except:
                pass
        
        if result["returncode"] != 0:
            return {
                "error": f"Nie udało się utworzyć klastra: {result['stderr']}",
                "debug": result
            }
        
        cluster_result = {
            "message": f"Klaster {cluster_name} został utworzony z {node_count} węzłami",
            "status": "success", 
            "cluster_name": cluster_name,
            "node_count": node_count,
            "context": f"kind-{cluster_name}",
            "assigned_ports": cluster_ports,
            "provider": "kind"
        }
        
        # Wyczyść cache
        _cluster_cache.clear()
        
        # DODAJ INSTALACJĘ MONITORINGU JEŚLI ZAZNACZONE
        if install_monitoring:
            print(f"Installing monitoring for cluster {cluster_name}...")
            
            # Poczekaj na gotowość klastra
            import time
            time.sleep(15)  # 15 sekund na inicjalizację
            
            try:
                # Zainstaluj monitoring
                monitoring_result = helm_service.install_monitoring_stack(cluster_name)
                print(f"Monitoring result: {monitoring_result}")
                
                if monitoring_result.get("success"):
                    cluster_result["message"] += " + monitoring zainstalowany"
                    cluster_result["monitoring"] = {
                        "installed": True,
                        "prometheus_url": f"http://localhost:{cluster_ports['prometheus']}",
                        "grafana_url": f"http://localhost:{cluster_ports['grafana']}",
                        "grafana_credentials": "admin/admin123",
                        "access_info": monitoring_result.get("access_info", {})
                    }
                else:
                    cluster_result["message"] += " + problem z monitoringiem"
                    cluster_result["monitoring_error"] = monitoring_result.get("error", "Unknown error")
                    
            except Exception as e:
                print(f"Monitoring installation error: {str(e)}")
                cluster_result["message"] += " + błąd monitoringu"
                cluster_result["monitoring_error"] = str(e)
        
        return cluster_result
        
    except Exception as e:
        return {
            "error": f"Błąd podczas tworzenia klastra: {str(e)}",
            "cluster_name": cluster_name
        }

@app.delete("/api/v1/local-cluster/{cluster_name}")
async def delete_cluster(cluster_name: str):
    """Usuń klaster (Kind lub k3d)"""
    
    # Wykryj provider
    provider = detect_cluster_provider(cluster_name)
    
    # Najpierw wyczyść zasoby monitoringu
    cleanup_result = helm_service.cleanup_cluster_resources(cluster_name)
    
    # Usuń klaster w zależności od providera
    if provider == "k3d":
        try:
            success = k3d_service.delete_cluster(cluster_name)
            if not success:
                return {
                    "error": f"Nie udało się usunąć klastra k3d: {cluster_name}",
                    "provider": "k3d"
                }
        except Exception as e:
            return {
                "error": f"Błąd podczas usuwania klastra k3d: {str(e)}",
                "provider": "k3d"
            }
    else:  # kind
        result = run_kind_command(["delete", "cluster", "--name", cluster_name])
        
        if result["returncode"] != 0:
            return {
                "error": f"Nie udało się usunąć klastra Kind: {result['stderr']}",
                "debug": result,
                "provider": "kind"
            }
    
    # Wyczyść cache
    _cluster_cache.clear()
    
    return {
        "message": f"Klaster {cluster_name} został usunięty",
        "cleanup": cleanup_result,
        "provider": provider
    }

@app.get("/api/v1/local-cluster/{cluster_name}/status")
async def get_cluster_status(cluster_name: str):
    """Sprawdź status klastra (Kind lub k3d) - ulepszona wersja"""
    # Wykryj provider
    provider = detect_cluster_provider(cluster_name)
    
    # Sprawdź czy klaster istnieje
    if provider == "k3d":
        try:
            k3d_clusters = k3d_service.list_clusters()
            if cluster_name not in k3d_clusters:
                return {"error": "Klaster k3d nie istnieje", "cluster_name": cluster_name, "provider": "k3d"}
        except Exception as e:
            return {"error": f"Nie można sprawdzić listy klastrów k3d: {str(e)}", "provider": "k3d"}
    else:  # kind
        result = run_kind_command(["get", "clusters"])
        
        if result["returncode"] != 0:
            return {"error": "Nie można sprawdzić listy klastrów Kind", "debug": result, "provider": "kind"}
        
        if cluster_name not in result["stdout"]:
            return {"error": "Klaster Kind nie istnieje", "cluster_name": cluster_name, "provider": "kind"}
    
    try:
        # Sprawdź węzły
        kubectl_result = subprocess.run([
            "kubectl", "get", "nodes", 
            "--context", f"{provider}-{cluster_name}",
            "-o", "json"
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        nodes_info = {
            "total_nodes": 0,
            "ready_nodes": 0,
            "control_plane_nodes": 0,
            "worker_nodes": 0,
            "nodes": []
        }
        
        if kubectl_result.returncode == 0:
            nodes_data = json.loads(kubectl_result.stdout)
            nodes_info["total_nodes"] = len(nodes_data.get("items", []))
            
            for node in nodes_data.get("items", []):
                node_name = node["metadata"]["name"]
                roles = []
                
                # Sprawdź role węzła (dla Kind i k3d)
                if "node-role.kubernetes.io/control-plane" in node["metadata"].get("labels", {}) or \
                   "node-role.kubernetes.io/master" in node["metadata"].get("labels", {}):
                    roles.append("control-plane")
                    nodes_info["control_plane_nodes"] += 1
                else:
                    roles.append("worker")
                    nodes_info["worker_nodes"] += 1
                
                # Status węzła
                ready = False
                for condition in node["status"].get("conditions", []):
                    if condition["type"] == "Ready" and condition["status"] == "True":
                        ready = True
                        nodes_info["ready_nodes"] += 1
                        break
                
                nodes_info["nodes"].append({
                    "name": node_name,
                    "roles": roles,
                    "ready": ready,
                    "version": node["status"]["nodeInfo"]["kubeletVersion"]
                })
        
        return {
            "cluster_name": cluster_name,
            "status": "running" if kubectl_result.returncode == 0 else "error",
            "context": f"{provider}-{cluster_name}",
            "provider": provider,
            "nodes_info": nodes_info,
            "kubectl_available": kubectl_result.returncode == 0
        }
        
    except Exception as e:
        return {
            "cluster_name": cluster_name,
            "status": "error",
            "error": f"Nie można pobrać szczegółów klastra: {str(e)}",
            "context": f"{provider}-{cluster_name}",
            "provider": provider
        }

# Dodaj endpoint do sprawdzania konfiguracji klastra
@app.get("/api/v1/local-cluster/{cluster_name}/config")
async def get_cluster_config(cluster_name: str):
    """Pobierz konfigurację klastra (Kind lub k3d)"""
    try:
        # Wykryj provider
        provider = detect_cluster_provider(cluster_name)
        
        # Sprawdź kontenery Docker dla klastra
        if provider == "k3d":
            # k3d używa labelki k3d.cluster
            docker_result = subprocess.run([
                "docker", "ps", "--filter", f"label=k3d.cluster.name={cluster_name}",
                "--format", "json"
            ], capture_output=True, text=True)
        else:  # kind
            # Kind używa labelki io.x-k8s.kind.cluster
            docker_result = subprocess.run([
                "docker", "ps", "--filter", f"label=io.x-k8s.kind.cluster={cluster_name}",
                "--format", "json"
            ], capture_output=True, text=True)
        
        containers = []
        if docker_result.returncode == 0:
            for line in docker_result.stdout.strip().split('\n'):
                if line:
                    container = json.loads(line)
                    containers.append({
                        "name": container["Names"],
                        "image": container["Image"],
                        "status": container["Status"],
                        "ports": container["Ports"]
                    })
        
        return {
            "cluster_name": cluster_name,
            "provider": provider,
            "containers": containers,
            "container_count": len(containers)
        }
        
    except Exception as e:
        return {
            "cluster_name": cluster_name,
            "error": f"Nie można pobrać konfiguracji: {str(e)}"
        }

@app.get("/api/v1/local-cluster/{cluster_name}/resources")
async def get_cluster_resources(cluster_name: str):
    """Sprawdź zasoby klastra (Kind lub k3d) - CPU, RAM, storage"""
    try:
        # Wykryj provider
        provider = detect_cluster_provider(cluster_name)
        
        # Sprawdź węzły i ich zasoby
        kubectl_result = subprocess.run([
            "kubectl", "get", "nodes", 
            "--context", f"{provider}-{cluster_name}",
            "-o", "json"
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        resources_info = {
            "cluster_name": cluster_name,
            "provider": provider,
            "total_resources": {
                "cpu": "0",
                "memory": "0Mi",
                "storage": "0Mi"
            },
            "allocatable_resources": {
                "cpu": "0",
                "memory": "0Mi", 
                "storage": "0Mi"
            },
            "nodes": []
        }
        
        if kubectl_result.returncode == 0:
            nodes_data = json.loads(kubectl_result.stdout)
            total_cpu = 0
            total_memory_ki = 0
            allocatable_cpu = 0
            allocatable_memory_ki = 0
            
            for node in nodes_data.get("items", []):
                node_name = node["metadata"]["name"]
                
                # Capacity (całkowite zasoby)
                capacity = node["status"].get("capacity", {})
                node_cpu = capacity.get("cpu", "0")
                node_memory = capacity.get("memory", "0Ki")
                node_storage = capacity.get("ephemeral-storage", "0Ki")
                
                # Allocatable (dostępne zasoby)
                allocatable = node["status"].get("allocatable", {})
                alloc_cpu = allocatable.get("cpu", "0")
                alloc_memory = allocatable.get("memory", "0Ki")
                alloc_storage = allocatable.get("ephemeral-storage", "0Ki")
                
                # Role węzła (dla Kind i k3d)
                roles = []
                if "node-role.kubernetes.io/control-plane" in node["metadata"].get("labels", {}) or \
                   "node-role.kubernetes.io/master" in node["metadata"].get("labels", {}):
                    roles.append("control-plane")
                else:
                    roles.append("worker")
                
                # Konwersja CPU na liczby
                try:
                    cpu_num = float(node_cpu.replace("m", "")) / 1000 if "m" in node_cpu else float(node_cpu)
                    alloc_cpu_num = float(alloc_cpu.replace("m", "")) / 1000 if "m" in alloc_cpu else float(alloc_cpu)
                    total_cpu += cpu_num
                    allocatable_cpu += alloc_cpu_num
                except:
                    cpu_num = 0
                    alloc_cpu_num = 0
                
                # Konwersja pamięci na KB
                try:
                    memory_ki = int(node_memory.replace("Ki", "")) if "Ki" in node_memory else 0
                    alloc_memory_ki_node = int(alloc_memory.replace("Ki", "")) if "Ki" in alloc_memory else 0
                    total_memory_ki += memory_ki
                    allocatable_memory_ki += alloc_memory_ki_node
                except:
                    memory_ki = 0
                    alloc_memory_ki_node = 0
                
                resources_info["nodes"].append({
                    "name": node_name,
                    "roles": roles,
                    "capacity": {
                        "cpu": node_cpu,
                        "memory": node_memory,
                        "storage": node_storage
                    },
                    "allocatable": {
                        "cpu": alloc_cpu,
                        "memory": alloc_memory,
                        "storage": alloc_storage
                    },
                    "resources_summary": {
                        "cpu_cores": cpu_num,
                        "memory_gb": round(memory_ki / 1024 / 1024, 2),
                        "allocatable_cpu_cores": alloc_cpu_num,
                        "allocatable_memory_gb": round(alloc_memory_ki_node / 1024 / 1024, 2)
                    }
                })
            
            # Podsumowanie całego klastra
            resources_info["total_resources"] = {
                "cpu_cores": total_cpu,
                "memory_gb": round(total_memory_ki / 1024 / 1024, 2),
                "node_count": len(nodes_data.get("items", []))
            }
            
            resources_info["allocatable_resources"] = {
                "cpu_cores": allocatable_cpu,
                "memory_gb": round(allocatable_memory_ki / 1024 / 1024, 2),
                "node_count": len(nodes_data.get("items", []))
            }
        
        # Dodatkowo - sprawdź kontenery Docker (pomiń dla uproszczenia, bo nazwy kontenerów się różnią)
        # Można to dodać później jeśli potrzebne
        
        resources_info["kubectl_available"] = kubectl_result.returncode == 0
        
        return resources_info
        
    except Exception as e:
        return {
            "cluster_name": cluster_name,
            "provider": detect_cluster_provider(cluster_name),
            "error": f"Nie można pobrać zasobów klastra: {str(e)}"
        }

@app.get("/api/v1/local-cluster/{cluster_name}/profile")
async def get_cluster_profile(cluster_name: str):
    """Sprawdź profil klastra i porównaj z ustawieniami"""
    try:
        # Pobierz zasoby
        resources_response = await get_cluster_resources(cluster_name)
        
        if "error" in resources_response:
            return resources_response
        
        total_cpu = resources_response.get("total_resources", {}).get("cpu_cores", 0)
        total_memory = resources_response.get("total_resources", {}).get("memory_gb", 0)
        node_count = resources_response.get("total_resources", {}).get("node_count", 0)
        
        # Określ profil na podstawie zasobów
        profile = "niestandardowy"
        if node_count == 1:
            if total_cpu <= 2 and total_memory <= 4:
                profile = "developerski"
            elif total_cpu <= 4 and total_memory <= 8:
                profile = "testowy"
            elif total_cpu >= 8 and total_memory >= 16:
                profile = "produkcyjny"
        
        return {
            "cluster_name": cluster_name,
            "detected_profile": profile,
            "resources": {
                "total_cpu_cores": total_cpu,
                "total_memory_gb": total_memory,
                "node_count": node_count
            },
            "profile_comparison": {
                "developerski": {"cpu": 2, "memory": 4, "nodes": 1},
                "testowy": {"cpu": 4, "memory": 8, "nodes": 1},
                "produkcyjny": {"cpu": 8, "memory": 16, "nodes": 1},
                "aktualny": {"cpu": total_cpu, "memory": total_memory, "nodes": node_count}
            }
        }
        
    except Exception as e:
        return {
            "cluster_name": cluster_name,
            "error": f"Nie można określić profilu klastra: {str(e)}"
        }

# Dodaj endpoint do automatycznej instalacji monitoringu przy tworzeniu klastra
@app.post("/api/v1/local-cluster/create-with-monitoring")
async def create_cluster_with_monitoring(cluster_data: dict):
    """Utwórz klaster z automatyczną instalacją monitoringu"""
    
    # Najpierw utwórz klaster
    cluster_result = await create_cluster(cluster_data)
    
    if "error" in cluster_result:
        return cluster_result
    
    cluster_name = cluster_data.get("cluster_name", "test-cluster")
    install_monitoring = cluster_data.get("install_monitoring", False)
    
    if not install_monitoring:
        return cluster_result
    
    try:
        # Poczekaj chwilę aż klaster będzie gotowy
        import asyncio
        await asyncio.sleep(30)  # 30 sekund na inicjalizację
        
        # Zainstaluj monitoring
        monitoring_result = helm_service.install_monitoring_stack(cluster_name)
        
        return {
            **cluster_result,
            "monitoring": monitoring_result,
            "message": f"{cluster_result['message']} + monitoring stack zainstalowany"
        }
        
    except Exception as e:
        return {
            **cluster_result,
            "monitoring_error": f"Klaster utworzony, ale monitoring nie został zainstalowany: {str(e)}"
        }

# Helper function to check if port-forward is active
def check_port_forward_active(cluster_name: str, port: int) -> bool:
    """Check if kubectl port-forward is running for the given cluster and port"""
    try:
        import psutil
        
        # Get all running processes
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline')
                if cmdline and 'kubectl' in ' '.join(cmdline):
                    # Check if it's a port-forward command for this cluster
                    cmdline_str = ' '.join(cmdline)
                    if 'port-forward' in cmdline_str and cluster_name in cmdline_str and str(port) in cmdline_str:
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return False
    except ImportError:
        # psutil not installed, return False
        return False
    except Exception:
        return False

# Zastąp istniejące endpointy monitoringu:
@app.post("/api/v1/monitoring/install/{cluster_name}")
async def install_monitoring_endpoint(cluster_name: str):
    """Zainstaluj monitoring w istniejącym klastrze"""
    try:
        result = helm_service.install_monitoring_stack(cluster_name)
        return {
            "cluster_name": cluster_name,
            **result
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Błąd instalacji monitoringu: {str(e)}"
        }

@app.delete("/api/v1/monitoring/uninstall/{cluster_name}")
async def uninstall_monitoring_endpoint(cluster_name: str):
    """Usuń monitoring z klastra (Prometheus i Grafana)"""
    try:
        # Usuń prometheus
        prometheus_result = app_service.uninstall_app(cluster_name, "prometheus")
        
        # Usuń grafana
        grafana_result = app_service.uninstall_app(cluster_name, "grafana")
        
        # Sprawdź czy oba się udały
        if prometheus_result.get("success") and grafana_result.get("success"):
            # Usuń przypisane porty
            port_manager.release_ports(cluster_name)
            
            return {
                "success": True,
                "message": "Monitoring został usunięty",
                "prometheus": prometheus_result,
                "grafana": grafana_result
            }
        else:
            errors = []
            if not prometheus_result.get("success"):
                errors.append(f"Prometheus: {prometheus_result.get('error', 'Unknown error')}")
            if not grafana_result.get("success"):
                errors.append(f"Grafana: {grafana_result.get('error', 'Unknown error')}")
            
            return {
                "success": False,
                "error": "; ".join(errors)
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Błąd usuwania monitoringu: {str(e)}"
        }

@app.get("/api/v1/monitoring/status/{cluster_name}")
async def get_monitoring_status_endpoint(cluster_name: str):
    """Sprawdź szczegółowy status monitoringu"""
    try:
        # Detect provider
        k3d_clusters = k3d_service.list_clusters()
        provider = "k3d" if cluster_name in k3d_clusters else "kind"
        context = f"{provider}-{cluster_name}"
        
        # Get pods in monitoring namespace
        kubectl_result = subprocess.run([
            "kubectl", "get", "pods", 
            "--namespace", "monitoring",
            "--context", context,
            "-o", "json"
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        if kubectl_result.returncode != 0:
            return {
                "cluster_name": cluster_name,
                "monitoring_installed": False,
                "message": "Monitoring nie jest zainstalowany"
            }
        
        import json
        pods_data = json.loads(kubectl_result.stdout)
        
        # Organize pods by type
        prometheus_pods_list = []
        grafana_pods_list = []
        
        for pod in pods_data.get("items", []):
            pod_name = pod["metadata"]["name"]
            pod_status = pod["status"]["phase"]
            
            # Check if pod is ready
            ready = False
            if "containerStatuses" in pod["status"]:
                ready = all(c.get("ready", False) for c in pod["status"]["containerStatuses"])
            
            pod_info = {
                "name": pod_name,
                "status": pod_status,
                "ready": ready
            }
            
            if "prometheus" in pod_name.lower():
                prometheus_pods_list.append(pod_info)
            elif "grafana" in pod_name.lower():
                grafana_pods_list.append(pod_info)
        
        # Count running pods
        prometheus_running = sum(1 for p in prometheus_pods_list if p["ready"])
        grafana_running = sum(1 for p in grafana_pods_list if p["ready"])
        
        # Get services
        services_result = subprocess.run([
            "kubectl", "get", "svc",
            "--namespace", "monitoring",
            "--context", context,
            "-o", "json"
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        services = {}
        if services_result.returncode == 0:
            services_data = json.loads(services_result.stdout)
            for svc in services_data.get("items", []):
                svc_name = svc["metadata"]["name"]
                svc_type = svc["spec"].get("type", "ClusterIP")
                ports = []
                for p in svc["spec"].get("ports", []):
                    port_info = {
                        "port": p.get("port"),
                        "targetPort": p.get("targetPort"),
                        "protocol": p.get("protocol", "TCP")
                    }
                    if "nodePort" in p:
                        port_info["nodePort"] = p.get("nodePort")
                    ports.append(port_info)
                
                services[svc_name] = {
                    "type": svc_type,
                    "ports": ports
                }
        
        return {
            "cluster_name": cluster_name,
            "monitoring_installed": True,
            "namespace": "monitoring",
            "prometheus": {
                "pod_count": len(prometheus_pods_list),
                "running": prometheus_running,
                "pods": prometheus_pods_list
            },
            "grafana": {
                "pod_count": len(grafana_pods_list),
                "running": grafana_running,
                "pods": grafana_pods_list
            },
            "services": services,
            "status": "healthy" if (prometheus_running + grafana_running) == (len(prometheus_pods_list) + len(grafana_pods_list)) and (len(prometheus_pods_list) + len(grafana_pods_list)) > 0 else "starting"
        }
        
    except Exception as e:
        return {
            "cluster_name": cluster_name,
            "error": f"Błąd sprawdzania statusu: {str(e)}"
        }

@app.get("/api/v1/monitoring/ports")
async def get_all_cluster_ports():
    """Zwróć wszystkie przypisane porty dla klastrów w formacie dla UI"""
    try:
        all_ports = port_manager.get_all_ports()
        
        # Transform to frontend format
        clusters_data = {}
        for cluster_name, ports in all_ports.items():
            prometheus_port = ports.get("prometheus")
            grafana_port = ports.get("grafana")
            
            # Check if port-forward is active for both services
            prometheus_active = check_port_forward_active(cluster_name, prometheus_port) if prometheus_port else False
            grafana_active = check_port_forward_active(cluster_name, grafana_port) if grafana_port else False
            port_forward_active = prometheus_active and grafana_active
            
            clusters_data[cluster_name] = {
                "ports": {
                    "prometheus": prometheus_port,
                    "grafana": grafana_port
                },
                "urls": {
                    "prometheus_url": f"http://localhost:{prometheus_port}",
                    "grafana_url": f"http://localhost:{grafana_port}"
                },
                "port_forward_active": port_forward_active,
                "port_forward_details": {
                    "prometheus_active": prometheus_active,
                    "grafana_active": grafana_active
                }
            }
        
        return {
            "total_clusters": len(clusters_data),
            "clusters": clusters_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd pobierania portów: {str(e)}")

@app.get("/api/v1/monitoring/ports/{cluster_name}")
async def get_cluster_ports_endpoint(cluster_name: str):
    """Zwróć porty dla konkretnego klastra"""
    try:
        ports = port_manager.get_cluster_ports(cluster_name)
        if not ports:
            return {
                "success": False,
                "error": f"Brak przypisanych portów dla klastra {cluster_name}"
            }
        
        return {
            "success": True,
            "cluster_name": cluster_name,
            "ports": ports,
            "urls": {
                "prometheus_url": f"http://localhost:{ports['prometheus']}",
                "grafana_url": f"http://localhost:{ports['grafana']}"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Błąd pobierania portów: {str(e)}"
        }

@app.post("/api/v1/monitoring/port-forward/start/{cluster_name}")
async def start_port_forward(cluster_name: str):
    """Start kubectl port-forward for monitoring services"""
    try:
        # Get assigned ports
        ports = port_manager.get_cluster_ports(cluster_name)
        if not ports:
            raise HTTPException(status_code=404, detail=f"Brak portów dla klastra {cluster_name}")
        
        # Detect provider
        k3d_clusters = k3d_service.list_clusters()
        provider = "k3d" if cluster_name in k3d_clusters else "kind"
        context = f"{provider}-{cluster_name}"
        
        prometheus_port = ports.get("prometheus")
        grafana_port = ports.get("grafana")
        
        # Start Prometheus port-forward in background
        prometheus_process = subprocess.Popen([
            "kubectl", "port-forward",
            "-n", "monitoring",
            "svc/prometheus-server",
            f"{prometheus_port}:80",
            "--context", context
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Start Grafana port-forward in background
        grafana_process = subprocess.Popen([
            "kubectl", "port-forward",
            "-n", "monitoring",
            "svc/grafana",
            f"{grafana_port}:80",
            "--context", context
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment to check if they started successfully
        await asyncio.sleep(1)
        
        # Check if processes are still running
        prometheus_running = prometheus_process.poll() is None
        grafana_running = grafana_process.poll() is None
        
        if not prometheus_running or not grafana_running:
            # Kill any that did start
            if prometheus_running:
                prometheus_process.kill()
            if grafana_running:
                grafana_process.kill()
            
            return {
                "success": False,
                "error": "Port-forward nie uruchomił się poprawnie"
            }
        
        return {
            "success": True,
            "message": "Port-forward uruchomiony",
            "urls": {
                "prometheus": f"http://localhost:{prometheus_port}",
                "grafana": f"http://localhost:{grafana_port}"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd uruchamiania port-forward: {str(e)}")

@app.post("/api/v1/monitoring/port-forward/stop/{cluster_name}")
async def stop_port_forward(cluster_name: str):
    """Stop kubectl port-forward for monitoring services"""
    try:
        import psutil
        
        # Get assigned ports
        ports = port_manager.get_cluster_ports(cluster_name)
        if not ports:
            raise HTTPException(status_code=404, detail=f"Brak portów dla klastra {cluster_name}")
        
        killed_count = 0
        
        # Find and kill port-forward processes for this cluster
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline')
                if cmdline and 'kubectl' in ' '.join(cmdline):
                    cmdline_str = ' '.join(cmdline)
                    if 'port-forward' in cmdline_str and cluster_name in cmdline_str:
                        proc.kill()
                        killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return {
            "success": True,
            "message": f"Zatrzymano {killed_count} procesów port-forward",
            "killed_processes": killed_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd zatrzymywania port-forward: {str(e)}")

@app.post("/api/v1/monitoring/install-metrics-server/{cluster_name}")
async def install_metrics_server(cluster_name: str):
    """Zainstaluj metrics-server w klastrze do zbierania metryk CPU/RAM"""
    try:
        context = f"kind-{cluster_name}"
        
        # Zainstaluj metrics-server
        kubectl_result = subprocess.run([
            "kubectl", "apply", 
            "-f", "https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml",
            "--context", context
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        if kubectl_result.returncode != 0:
            return {
                "success": False,
                "error": f"Błąd instalacji metrics-server: {kubectl_result.stderr}"
            }
        
        # Patch metrics-server dla Kind (wyłącz TLS verification)
        patch_result = subprocess.run([
            "kubectl", "patch", "deployment", "metrics-server",
            "-n", "kube-system",
            "--context", context,
            "-p", '{"spec":{"template":{"spec":{"containers":[{"name":"metrics-server","args":["--cert-dir=/tmp","--secure-port=4443","--kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname","--kubelet-use-node-status-port","--metric-resolution=15s","--kubelet-insecure-tls"]}]}}}}'
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        return {
            "success": True,
            "message": "Metrics-server zainstalowany pomyślnie",
            "note": "Poczekaj ~30 sekund na uruchomienie, potem odśwież dane"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Błąd instalacji metrics-server: {str(e)}"
        }

# BACKUP ENDPOINTS

@app.post("/api/v1/backup/create/{cluster_name}")
async def create_backup(cluster_name: str, backup_name: str = None):
    """Utwórz backup klastra"""
    result = backup_service.create_cluster_backup(cluster_name, backup_name)
    return result

@app.post("/api/v1/backup/change-directory")
async def change_backup_directory(request: dict):
    """Zmień katalog backup"""
    new_directory = request.get("directory")
    if not new_directory:
        return {
            "success": False,
            "error": "Directory path is required",
            "message": "Ścieżka do katalogu jest wymagana"
        }
    
    result = backup_service.change_backup_directory(new_directory)
    return result

@app.get("/api/v1/backup/info")
async def get_backup_info():
    """Pobierz informacje o katalogu backup"""
    return backup_service.get_backup_directory_info()

@app.get("/api/v1/backup/list")
async def list_backups():
    """Lista wszystkich backupów"""
    backups = backup_service.list_backups()
    return {
        "success": True,
        "backups": backups,
        "total_count": len(backups)
    }

@app.get("/api/v1/backup/details/{backup_name}")
async def get_backup_details(backup_name: str):
    """Pobierz szczegóły backupu"""
    return backup_service.get_backup_details(backup_name)

@app.delete("/api/v1/backup/delete/{backup_name}")
async def delete_backup(backup_name: str):
    """Usuń backup"""
    return backup_service.delete_backup(backup_name)

@app.post("/api/v1/backup/restore/{backup_name}")
async def restore_backup(backup_name: str, new_cluster_name: str = None):
    """Przywróć klaster z backupu"""
    result = backup_service.restore_cluster_backup(backup_name, new_cluster_name)
    return result

@app.get("/api/v1/backup/download/{backup_name}")
async def download_backup(backup_name: str):
    """Pobierz plik backupu"""
    from fastapi.responses import FileResponse
    import os
    
    backup_file = f"backups/{backup_name}.zip"
    if os.path.exists(backup_file):
        return FileResponse(
            path=backup_file,
            filename=f"{backup_name}.zip",
            media_type="application/zip"
        )
    else:
        return {
            "success": False,
            "error": "Backup file not found"
        }

# ==================== APPS ENDPOINTS ====================

from pydantic import BaseModel
from typing import Dict, Any

class AppInstallRequest(BaseModel):
    name: str
    displayName: str
    namespace: str
    helmChart: str
    values: Dict[str, Any] = {}

@app.post("/api/v1/apps/install/{cluster_name}")
async def install_app(cluster_name: str, app_data: AppInstallRequest):
    """Install application on cluster"""
    try:
        result = app_service.install_app(cluster_name, app_data.dict())
        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"Installation error: {str(e)}"
        }

@app.get("/api/v1/apps/installed/{cluster_name}")
async def get_installed_apps(cluster_name: str):
    """Get installed applications on cluster"""
    try:
        result = app_service.get_installed_apps(cluster_name)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting apps: {str(e)}"
        }

@app.delete("/api/v1/apps/uninstall/{cluster_name}/{app_name}")
async def uninstall_app(cluster_name: str, app_name: str):
    """Uninstall application from cluster"""
    try:
        result = app_service.uninstall_app(cluster_name, app_name)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"Uninstall error: {str(e)}"
        }

@app.get("/api/v1/apps/search")
async def search_helm_charts(query: str, max_results: int = 20):
    """Search for Helm charts in repositories"""
    try:
        if not query or len(query) < 2:
            return {
                "success": False,
                "error": "Query must be at least 2 characters",
                "charts": []
            }
        
        result = app_service.search_helm_charts(query, max_results)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Search error: {str(e)}",
            "charts": []
        }

@app.get("/api/v1/apps/available")
async def get_available_apps():
    """Get list of available applications"""
    return {
        "success": True,
        "categories": [
            {
                "name": "databases",
                "displayName": "Bazy danych",
                "apps": [
                    {"name": "postgresql", "displayName": "PostgreSQL", "icon": "🐘"},
                    {"name": "mysql", "displayName": "MySQL", "icon": "🐬"},
                    {"name": "mongodb", "displayName": "MongoDB", "icon": "🍃"},
                    {"name": "redis", "displayName": "Redis", "icon": "🔴"}
                ]
            },
            {
                "name": "messaging", 
                "displayName": "Message Brokers",
                "apps": [
                    {"name": "rabbitmq", "displayName": "RabbitMQ", "icon": "🐰"},
                    {"name": "kafka", "displayName": "Apache Kafka", "icon": "📡"}
                ]
            }
        ]
    }

# ===== CLUSTER SCALING ENDPOINTS =====

@app.get("/api/v1/clusters/{cluster_name}/scaling/config")
async def get_cluster_scaling_config(cluster_name: str):
    """Get current scaling configuration for Kind or k3d cluster"""
    try:
        # Detect provider
        provider = detect_cluster_provider(cluster_name)
        
        # === K3D IMPLEMENTATION ===
        if provider == "k3d":
            cluster_info = k3d_service.get_cluster_info(cluster_name)
            
            if not cluster_info.get("success"):
                return {
                    "success": False,
                    "error": cluster_info.get("error", "Failed to get k3d cluster info")
                }
            
            nodes = cluster_info.get("nodes", [])
            server_count = sum(1 for n in nodes if n.get("role") == "server")
            agent_count = sum(1 for n in nodes if n.get("role") == "agent")
            
            return {
                "success": True,
                "provider": "k3d",
                "config": {
                    "controlPlaneNodes": server_count,
                    "workerNodes": agent_count,
                    "totalNodes": server_count + agent_count,
                    "cpuPerNode": 0,  # k3d doesn't set explicit CPU limits by default
                    "ramPerNode": 0   # k3d doesn't set explicit RAM limits by default
                },
                "info": "k3d supports LIVE node scaling without cluster recreation"
            }
        
        # === KIND IMPLEMENTATION (ORIGINAL) ===
        # Get all nodes for this cluster
        result = subprocess.run(
            ['kubectl', 'get', 'nodes', '--context', f'kind-{cluster_name}', '-o', 'json'],
            capture_output=True,
            text=True,
            check=True
        )
        
        nodes_data = json.loads(result.stdout)
        nodes = nodes_data.get('items', [])
        
        # Separate control plane and worker nodes
        control_plane_count = 0
        worker_count = 0
        
        for node in nodes:
            labels = node.get('metadata', {}).get('labels', {})
            if 'node-role.kubernetes.io/control-plane' in labels or 'node-role.kubernetes.io/master' in labels:
                control_plane_count += 1
            else:
                worker_count += 1
        
        # Get Docker container info for a worker node to check resources
        cpu_per_node = 2  # default
        ram_per_node = 4096  # default in MB
        
        if worker_count > 0:
            # Find a worker node container
            docker_result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={cluster_name}-worker', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                check=True
            )
            
            if docker_result.stdout.strip():
                container_name = docker_result.stdout.strip().split('\n')[0]
                
                # Get container info
                inspect_result = subprocess.run(
                    ['docker', 'inspect', container_name],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                container_info = json.loads(inspect_result.stdout)[0]
                host_config = container_info.get('HostConfig', {})
                
                # CPU (NanoCpus / 1e9)
                nano_cpus = host_config.get('NanoCpus', 0)
                if nano_cpus > 0:
                    cpu_per_node = int(nano_cpus / 1e9)
                
                # Memory in MB
                memory = host_config.get('Memory', 0)
                if memory > 0:
                    ram_per_node = int(memory / (1024 * 1024))
        
        return {
            "success": True,
            "provider": "kind",
            "config": {
                "controlPlaneNodes": control_plane_count,
                "workerNodes": worker_count,
                "totalNodes": control_plane_count + worker_count,
                "cpuPerNode": cpu_per_node,
                "ramPerNode": ram_per_node
            },
            "warning": "Kind requires cluster recreation for scaling changes"
        }
        
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "error": f"Failed to get cluster config: {e.stderr}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/v1/clusters/{cluster_name}/scaling/resources")
async def get_cluster_resource_usage(cluster_name: str):
    """Get real-time CPU and RAM usage for cluster nodes"""
    try:
        # Get Docker stats for all containers in this cluster
        stats_result = subprocess.run(
            ['docker', 'stats', '--no-stream', '--filter', f'name={cluster_name}', 
             '--format', '{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}'],
            capture_output=True,
            text=True,
            check=True
        )
        
        nodes_usage = []
        total_cpu = 0.0
        total_mem_mb = 0.0
        
        for line in stats_result.stdout.strip().split('\n'):
            if not line:
                continue
                
            parts = line.split('\t')
            if len(parts) < 4:
                continue
                
            name = parts[0]
            cpu_str = parts[1].replace('%', '')
            mem_usage = parts[2]  # e.g., "450.5MiB / 8GiB"
            mem_percent = parts[3].replace('%', '')
            
            # Parse memory usage
            mem_used_mb = 0
            mem_limit_mb = 0
            if '/' in mem_usage:
                used, limit = mem_usage.split('/')
                
                # Parse used memory
                if 'GiB' in used:
                    mem_used_mb = float(used.replace('GiB', '').strip()) * 1024
                elif 'MiB' in used:
                    mem_used_mb = float(used.replace('MiB', '').strip())
                
                # Parse limit memory
                if 'GiB' in limit:
                    mem_limit_mb = float(limit.replace('GiB', '').strip()) * 1024
                elif 'MiB' in limit:
                    mem_limit_mb = float(limit.replace('MiB', '').strip())
            
            # Determine node type
            node_type = 'worker'
            if 'control-plane' in name:
                node_type = 'control-plane'
            
            nodes_usage.append({
                "name": name,
                "type": node_type,
                "cpu_percent": float(cpu_str) if cpu_str else 0.0,
                "memory_used_mb": round(mem_used_mb, 2),
                "memory_limit_mb": round(mem_limit_mb, 2),
                "memory_percent": float(mem_percent) if mem_percent else 0.0
            })
            
            total_cpu += float(cpu_str) if cpu_str else 0.0
            total_mem_mb += mem_used_mb
        
        # Calculate averages
        node_count = len(nodes_usage)
        avg_cpu = round(total_cpu / node_count, 2) if node_count > 0 else 0
        
        return {
            "success": True,
            "cluster_name": cluster_name,
            "nodes": nodes_usage,
            "summary": {
                "total_nodes": node_count,
                "avg_cpu_percent": avg_cpu,
                "total_memory_mb": round(total_mem_mb, 2)
            }
        }
        
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "error": f"Failed to get resource usage: {e.stderr if e.stderr else str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/api/v1/clusters/{cluster_name}/scaling/apply")
async def apply_cluster_scaling(cluster_name: str, scaling_config: dict):
    """
    Apply scaling changes to cluster.
    Kind: Recreates cluster (data loss warning).
    k3d: Live node addition/removal without recreate!
    """
    try:
        worker_nodes = scaling_config.get('workerNodes', 2)
        cpu_per_node = scaling_config.get('cpuPerNode', 2)
        ram_per_node = scaling_config.get('ramPerNode', 4096)
        
        operations = []
        
        # Detect provider
        provider = detect_cluster_provider(cluster_name)
        
        # === K3D IMPLEMENTATION (LIVE SCALING!) ===
        if provider == "k3d":
            operations.append(f"🎯 Scaling k3d cluster '{cluster_name}' to {worker_nodes} agent nodes...")
            
            # Use k3d's live scaling
            scale_result = k3d_service.scale_cluster(cluster_name, worker_nodes)
            
            if not scale_result.get("success"):
                return {
                    "success": False,
                    "error": scale_result.get("error", "Failed to scale k3d cluster"),
                    "operations": operations
                }
            
            # Add k3d operations to our log
            operations.extend(scale_result.get("operations", []))
            
            # Get updated cluster info
            cluster_info = k3d_service.get_cluster_info(cluster_name)
            nodes = cluster_info.get("nodes", [])
            agent_count = sum(1 for n in nodes if n.get("role") == "agent")
            
            return {
                "success": True,
                "message": f"✅ k3d cluster scaled to {agent_count} agent nodes (LIVE - no recreate!)",
                "operations": operations,
                "provider": "k3d",
                "info": "✨ k3d supports live scaling - your deployments are preserved!"
            }
        
        # === KIND IMPLEMENTATION (RECREATE) ===
        # Create new cluster configuration
        config_data = {
            "kind": "Cluster",
            "apiVersion": "kind.x-k8s.io/v1alpha4",
            "nodes": [
                {"role": "control-plane"}
            ]
        }
        
        # Add worker nodes
        for i in range(worker_nodes):
            config_data["nodes"].append({"role": "worker"})
        
        # Write config to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            # Delete old cluster
            operations.append("🗑️ Deleting old cluster...")
            subprocess.run(
                ['kind', 'delete', 'cluster', '--name', cluster_name],
                capture_output=True,
                text=True,
                check=False  # Don't fail if cluster doesn't exist
            )
            
            # Small delay to ensure cleanup
            import time
            time.sleep(2)
            
            # Invalidate cache
            _cluster_cache.clear()
            
            # Create new cluster with updated config
            operations.append(f"🚀 Creating cluster with {worker_nodes} worker node(s)...")
            create_result = subprocess.run(
                ['kind', 'create', 'cluster', '--name', cluster_name, '--config', config_path, '--wait', '60s'],
                capture_output=True,
                text=True,
                check=True
            )
            
            operations.append("✅ Cluster recreated successfully")
            
            # Wait for nodes to be fully ready
            operations.append("⏳ Waiting for nodes to become ready...")
            time.sleep(5)
            
            # Verify nodes
            verify_result = subprocess.run(
                ['kubectl', 'get', 'nodes', '--context', f'kind-{cluster_name}', '--no-headers'],
                capture_output=True,
                text=True,
                check=True
            )
            
            node_count = len(verify_result.stdout.strip().split('\n'))
            operations.append(f"📊 Cluster now has {node_count} total nodes (1 control-plane + {worker_nodes} workers)")
            
        finally:
            # Clean up temp file
            if os.path.exists(config_path):
                os.unlink(config_path)
        
        return {
            "success": True,
            "message": f"Cluster successfully scaled to {worker_nodes} worker nodes",
            "operations": operations,
            "provider": "kind",
            "warning": "⚠️ Cluster was recreated - all previous deployments and data were reset"
        }
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        return {
            "success": False,
            "error": f"Failed to scale cluster: {error_msg}",
            "operations": operations
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "operations": operations
        }
