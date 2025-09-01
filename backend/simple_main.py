from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import os
import shutil
import tempfile
import yaml
import json
from app.services.helm_service import helm_service
from app.services.port_manager import port_manager

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
        nodes_result = subprocess.run([
            "kubectl", "get", "nodes", "--context", f"kind-{cluster_name}",
            "-o", "custom-columns=NAME:.metadata.name,STATUS:.status.conditions[-1].type,ROLES:.metadata.labels.node-role\.kubernetes\.io/control-plane",
            "--no-headers"
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')
        
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
                "note": "Metryki zasobow niedostepne (metrics-server nie zainstalowany)"
            }
    except:
        pass
    
    return {
        "error": "Nie mozna pobrac informacji o wezlach",
        "node_count": 0
    }

# ENDPOINTS

@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "service": "ClusterMaster API"}

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
    """Lista klastrów Kind"""
    result = run_kind_command(["get", "clusters"])
    
    if result["returncode"] != 0:
        return {
            "clusters": [], 
            "error": result["stderr"] or "Nie można pobrać listy klastrów",
            "debug": result
        }
    
    clusters = result["stdout"].strip().split('\n') if result["stdout"].strip() else []
    return {"clusters": clusters}

@app.get("/api/v1/local-cluster")
async def list_clusters_detailed():
    """Lista klastrów Kind z dodatkowymi informacjami"""
    result = run_kind_command(["get", "clusters"])
    
    if result["returncode"] != 0:
        return {
            "clusters": [], 
            "error": result["stderr"] or "Nie można pobrać listy klastrów",
            "debug": result
        }
    
    cluster_names = result["stdout"].strip().split('\n') if result["stdout"].strip() else []
    
    # Zbierz szczegółowe informacje o każdym klastrze
    detailed_clusters = []
    for cluster_name in cluster_names:
        if not cluster_name.strip():
            continue
            
        cluster_info = {
            "name": cluster_name,
            "status": "unknown",
            "context": f"kind-{cluster_name}"
        }
        
        # Sprawdź status klastra
        try:
            status_result = subprocess.run([
                "kubectl", "get", "nodes", "--context", f"kind-{cluster_name}"
            ], capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            if status_result.returncode == 0:
                cluster_info["status"] = "ready"
                # Policz węzły
                nodes_lines = status_result.stdout.strip().split('\n')
                cluster_info["node_count"] = len(nodes_lines) - 1 if len(nodes_lines) > 1 else 0
            else:
                cluster_info["status"] = "error"
        except:
            cluster_info["status"] = "error"
        
        # Sprawdź czy ma monitoring - sprawdź faktyczne pody, nie tylko namespace
        try:
            monitoring_result = subprocess.run([
                "kubectl", "get", "pods", "--namespace", "monitoring", 
                "--context", f"kind-{cluster_name}",
                "-l", "app.kubernetes.io/name=prometheus",
                "--no-headers"
            ], capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            grafana_result = subprocess.run([
                "kubectl", "get", "pods", "--namespace", "monitoring", 
                "--context", f"kind-{cluster_name}",
                "-l", "app.kubernetes.io/name=grafana", 
                "--no-headers"
            ], capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            # Monitoring jest zainstalowany tylko jeśli są pody Prometheus I Grafana
            has_prometheus = monitoring_result.returncode == 0 and monitoring_result.stdout.strip()
            has_grafana = grafana_result.returncode == 0 and grafana_result.stdout.strip()
            
            cluster_info["monitoring"] = {
                "installed": bool(has_prometheus and has_grafana)
            }
        except:
            cluster_info["monitoring"] = {"installed": False}
        
        # Dodaj informacje o portach
        cluster_ports = port_manager.get_cluster_ports(cluster_name)
        if cluster_ports:
            cluster_info["assigned_ports"] = cluster_ports
        
        # Dodaj informacje o zasobach systemowych
        try:
            # Pobierz metryki węzłów
            nodes_metrics = subprocess.run([
                "kubectl", "top", "nodes", "--context", f"kind-{cluster_name}",
                "--no-headers"
            ], capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            if nodes_metrics.returncode == 0 and nodes_metrics.stdout.strip():
                cluster_info["resources"] = parse_node_metrics(nodes_metrics.stdout)
            else:
                # Fallback - podstawowe info o węzłach
                cluster_info["resources"] = get_basic_node_info(cluster_name)
        except:
            cluster_info["resources"] = {"error": "Nie można pobrać metryk"}
        
        detailed_clusters.append(cluster_info)
    
    return {"clusters": detailed_clusters}

@app.post("/api/v1/local-cluster/create")
async def create_cluster(cluster_data: dict):
    """Utwórz nowy klaster Kind"""
    print(f"DEBUG: Received request: {cluster_data}")  # Debug
    
    cluster_name = cluster_data.get("cluster_name", "test-cluster")
    node_count = cluster_data.get("node_count", 1)
    k8s_version = cluster_data.get("k8s_version")
    install_monitoring = cluster_data.get("install_monitoring", False)  # <-- DODAJ TO
    
    print(f"DEBUG: Install monitoring = {install_monitoring}")  # Debug
    
    # Sprawdź czy klaster już istnieje
    result = run_kind_command(["get", "clusters"])
    if result["returncode"] == 0 and cluster_name in result["stdout"]:
        return {
            "message": f"Klaster {cluster_name} już istnieje", 
            "status": "exists",
            "cluster_name": cluster_name,
            "node_count": node_count
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
            "assigned_ports": cluster_ports
        }
        
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
    """Usuń klaster Kind"""
    
    # Najpierw wyczyść zasoby monitoringu
    cleanup_result = helm_service.cleanup_cluster_resources(cluster_name)
    
    result = run_kind_command(["delete", "cluster", "--name", cluster_name])
    
    if result["returncode"] != 0:
        return {
            "error": f"Nie udało się usunąć klastra: {result['stderr']}",
            "debug": result
        }
    
    return {
        "message": f"Klaster {cluster_name} został usunięty",
        "cleanup": cleanup_result
    }

@app.get("/api/v1/local-cluster/{cluster_name}/status")
async def get_cluster_status(cluster_name: str):
    """Sprawdź status klastra - ulepszona wersja"""
    # Sprawdź czy klaster istnieje
    result = run_kind_command(["get", "clusters"])
    
    if result["returncode"] != 0:
        return {"error": "Nie można sprawdzić listy klastrów", "debug": result}
    
    if cluster_name not in result["stdout"]:
        return {"error": "Klaster nie istnieje", "cluster_name": cluster_name}
    
    try:
        # Sprawdź węzły
        kubectl_result = subprocess.run([
            "kubectl", "get", "nodes", 
            "--context", f"kind-{cluster_name}",
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
                
                # Sprawdź role węzła
                if "node-role.kubernetes.io/control-plane" in node["metadata"].get("labels", {}):
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
            "context": f"kind-{cluster_name}",
            "nodes_info": nodes_info,
            "kubectl_available": kubectl_result.returncode == 0
        }
        
    except Exception as e:
        return {
            "cluster_name": cluster_name,
            "status": "error",
            "error": f"Nie można pobrać szczegółów klastra: {str(e)}",
            "context": f"kind-{cluster_name}"
        }

# Dodaj endpoint do sprawdzania konfiguracji klastra
@app.get("/api/v1/local-cluster/{cluster_name}/config")
async def get_cluster_config(cluster_name: str):
    """Pobierz konfigurację klastra"""
    try:
        # Sprawdź kontenery Docker dla klastra
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
    """Sprawdź zasoby klastra - CPU, RAM, storage"""
    try:
        # Sprawdź węzły i ich zasoby
        kubectl_result = subprocess.run([
            "kubectl", "get", "nodes", 
            "--context", f"kind-{cluster_name}",
            "-o", "json"
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        resources_info = {
            "cluster_name": cluster_name,
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
                
                # Role węzła
                roles = []
                if "node-role.kubernetes.io/control-plane" in node["metadata"].get("labels", {}):
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
        
        # Dodatkowo - sprawdź kontenery Docker
        docker_result = subprocess.run([
            "docker", "stats", "--no-stream", "--format", "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}",
            "test1-control-plane", "test1-worker", "test1-worker2", "test1-worker3"
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        docker_stats = []
        if docker_result.returncode == 0:
            lines = docker_result.stdout.strip().split('\n')
            for line in lines[1:]:  # Pomiń header
                parts = line.split('\t')
                if len(parts) >= 4:
                    docker_stats.append({
                        "container": parts[0],
                        "cpu_percent": parts[1],
                        "memory_usage": parts[2],
                        "memory_percent": parts[3]
                    })
        
        resources_info["docker_stats"] = docker_stats
        resources_info["kubectl_available"] = kubectl_result.returncode == 0
        
        return resources_info
        
    except Exception as e:
        return {
            "cluster_name": cluster_name,
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

@app.get("/api/v1/monitoring/status/{cluster_name}")
async def get_monitoring_status_endpoint(cluster_name: str):
    """Sprawdź status monitoringu"""
    try:
        context = f"kind-{cluster_name}"
        
        # Sprawdź pody monitoringu
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
        
        prometheus_pods = len([p for p in pods_data.get("items", []) if "prometheus" in p["metadata"]["name"]])
        grafana_pods = len([p for p in pods_data.get("items", []) if "grafana" in p["metadata"]["name"]])
        running_pods = len([p for p in pods_data.get("items", []) if p["status"]["phase"] == "Running"])
        total_pods = len(pods_data.get("items", []))
        
        return {
            "cluster_name": cluster_name,
            "monitoring_installed": True,
            "namespace": "monitoring",
            "total_pods": total_pods,
            "running_pods": running_pods,
            "prometheus_pods": prometheus_pods,
            "grafana_pods": grafana_pods,
            "status": "healthy" if total_pods > 0 and running_pods == total_pods else "starting",
            "access_info": {
                "prometheus": f"kubectl port-forward svc/prometheus-server 9090:80 -n monitoring --context {context}",
                "grafana": f"kubectl port-forward svc/grafana 3000:80 -n monitoring --context {context} (admin/admin123)"
            }
        }
        
    except Exception as e:
        return {
            "cluster_name": cluster_name,
            "error": f"Błąd sprawdzania statusu: {str(e)}"
        }

@app.get("/api/v1/monitoring/ports")
async def get_all_cluster_ports():
    """Zwróć wszystkie przypisane porty dla klastrów"""
    try:
        all_ports = port_manager.get_all_ports()
        return {
            "success": True,
            "ports": all_ports
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Błąd pobierania portów: {str(e)}"
        }

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