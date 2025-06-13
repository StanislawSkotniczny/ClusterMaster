from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import os
import shutil

app = FastAPI(title="ClusterMaster API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
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

@app.get("/")
async def root():
    return {"message": "ClusterMaster API is running"}

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

@app.post("/api/v1/local-cluster/create")
async def create_cluster(cluster_data: dict):
    """Utwórz nowy klaster Kind"""
    cluster_name = cluster_data.get("cluster_name", "test-cluster")
    node_count = cluster_data.get("node_count", 2)
    
    # Sprawdź czy klaster już istnieje
    result = run_kind_command(["get", "clusters"])
    if result["returncode"] == 0 and cluster_name in result["stdout"]:
        return {
            "message": f"Klaster {cluster_name} już istnieje", 
            "status": "exists",
            "cluster_name": cluster_name
        }
    
    # Utwórz klaster
    result = run_kind_command(["create", "cluster", "--name", cluster_name], timeout=300)
    
    if result["returncode"] != 0:
        return {
            "error": f"Nie udało się utworzyć klastra: {result['stderr']}",
            "debug": result
        }
    
    return {
        "message": f"Klaster {cluster_name} utworzony pomyślnie",
        "status": "created",
        "cluster_name": cluster_name
    }

@app.delete("/api/v1/local-cluster/{cluster_name}")
async def delete_cluster(cluster_name: str):
    """Usuń klaster Kind"""
    result = run_kind_command(["delete", "cluster", "--name", cluster_name])
    
    if result["returncode"] != 0:
        return {
            "error": f"Nie udało się usunąć klastra: {result['stderr']}",
            "debug": result
        }
    
    return {"message": f"Klaster {cluster_name} został usunięty"}

@app.get("/api/v1/local-cluster/{cluster_name}/status")
async def get_cluster_status(cluster_name: str):
    """Sprawdź status klastra"""
    # Sprawdź czy klaster istnieje
    result = run_kind_command(["get", "clusters"])
    
    if result["returncode"] != 0:
        return {"error": "Nie można sprawdzić listy klastrów", "debug": result}
    
    if cluster_name not in result["stdout"]:
        return {"error": "Klaster nie istnieje", "cluster_name": cluster_name}
    
    # Sprawdź status węzłów
    kubectl_result = subprocess.run([
        "kubectl", "get", "nodes", 
        "--context", f"kind-{cluster_name}",
        "--no-headers"
    ], capture_output=True, text=True)
    
    return {
        "cluster_name": cluster_name,
        "status": "running" if kubectl_result.returncode == 0 else "error",
        "nodes": kubectl_result.stdout.strip() if kubectl_result.returncode == 0 else "Nie można pobrać statusu węzłów",
        "context": f"kind-{cluster_name}"
    }