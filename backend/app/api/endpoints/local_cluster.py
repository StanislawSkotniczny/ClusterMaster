from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import subprocess
import os
from typing import Optional, List

router = APIRouter()

class LocalClusterRequest(BaseModel):
    cluster_name: str
    node_count: int = 2
    k8s_version: str = "v1.26.0"

class LocalClusterResponse(BaseModel):
    cluster_name: str
    status: str
    message: str
    kubeconfig_path: Optional[str] = None

class ClusterInfo(BaseModel):
    name: str
    status: str
    nodes: Optional[str] = None

@router.post("/create", response_model=LocalClusterResponse)
async def create_local_cluster(request: LocalClusterRequest):
    """
    Utwórz lokalny klaster Kubernetes z Kind
    """
    try:
        cluster_name = request.cluster_name
        
        # Sprawdź czy Kind jest zainstalowany
        result = subprocess.run(["kind", "version"], capture_output=True, text=True)
        if result.returncode != 0:
            raise HTTPException(
                status_code=400,
                detail="Kind nie jest zainstalowany. Zainstaluj: https://kind.sigs.k8s.io/docs/user/quick-start/"
            )
        
        # Sprawdź czy klaster już istnieje
        result = subprocess.run(["kind", "get", "clusters"], capture_output=True, text=True)
        if cluster_name in result.stdout:
            return LocalClusterResponse(
                cluster_name=cluster_name,
                status="exists",
                message=f"Klaster {cluster_name} już istnieje"
            )
        
        # Utwórz konfigurację Kind
        kind_config = f"""apiVersion: kind.x-k8s.io/v1alpha4
kind: Cluster
nodes:
- role: control-plane
"""
        
        # Dodaj worker nodes
        for i in range(request.node_count - 1):
            kind_config += "- role: worker\n"
        
        # Zapisz konfigurację do pliku tymczasowego
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(kind_config)
            config_path = f.name
        
        try:
            # Utwórz klaster
            cmd = [
                "kind", "create", "cluster",
                "--name", cluster_name,
                "--config", config_path,
                "--image", f"kindest/node:{request.k8s_version}"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"Nie udało się utworzyć klastra: {result.stderr}"
                )
            
            return LocalClusterResponse(
                cluster_name=cluster_name,
                status="created",
                message=f"Klaster {cluster_name} utworzony pomyślnie z {request.node_count} węzłami"
            )
            
        finally:
            # Usuń plik tymczasowy
            if os.path.exists(config_path):
                os.unlink(config_path)
        
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail="Tworzenie klastra przekroczyło limit czasu (5 min)"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Błąd podczas tworzenia klastra: {str(e)}"
        )

@router.get("/list", response_model=List[str])
async def list_clusters():
    """
    Lista lokalnych klastrów Kind
    """
    try:
        result = subprocess.run(["kind", "get", "clusters"], capture_output=True, text=True)
        if result.returncode != 0:
            return []
        clusters = result.stdout.strip().split('\n') if result.stdout.strip() else []
        return clusters
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{cluster_name}")
async def delete_cluster(cluster_name: str):
    """
    Usuń lokalny klaster Kind
    """
    try:
        result = subprocess.run([
            "kind", "delete", "cluster", "--name", cluster_name
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Nie udało się usunąć klastra: {result.stderr}"
            )
        
        return {"message": f"Klaster {cluster_name} został usunięty"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{cluster_name}/status", response_model=ClusterInfo)
async def get_cluster_status(cluster_name: str):
    """
    Sprawdź status klastra
    """
    try:
        # Sprawdź czy klaster istnieje
        result = subprocess.run(["kind", "get", "clusters"], capture_output=True, text=True)
        
        if cluster_name not in result.stdout:
            raise HTTPException(status_code=404, detail="Klaster nie istnieje")
        
        # Spróbuj pobrać status nodów
        result = subprocess.run([
            "kubectl", "get", "nodes", 
            "--context", f"kind-{cluster_name}",
            "--no-headers"
        ], capture_output=True, text=True)
        
        status = "running" if result.returncode == 0 else "error"
        nodes_info = result.stdout.strip() if result.returncode == 0 else "Nie można pobrać statusu węzłów"
        
        return ClusterInfo(
            name=cluster_name,
            status=status,
            nodes=nodes_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))