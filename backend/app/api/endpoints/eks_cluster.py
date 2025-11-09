"""
API endpoints dla AWS EKS clusters
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.services.eks_service import eks_service

router = APIRouter()


class EksClusterRequest(BaseModel):
    """Request do utworzenia klastra EKS"""
    cluster_name: str = Field(..., description="Nazwa klastra")
    region: str = Field(..., description="Region AWS (np. eu-central-1)")
    aws_access_key: str = Field(..., description="AWS Access Key ID")
    aws_secret_key: str = Field(..., description="AWS Secret Access Key")
    node_count: int = Field(2, ge=1, le=10, description="Liczba worker nodes")
    instance_type: str = Field("t3.small", description="Typ instancji EC2")
    vpc_cidr: str = Field("10.0.0.0/16", description="CIDR dla VPC")
    install_monitoring: bool = Field(False, description="Zainstaluj Prometheus/Grafana")


class EksCredentials(BaseModel):
    """Credentials AWS"""
    region: str
    aws_access_key: str
    aws_secret_key: str


class EksClusterResponse(BaseModel):
    """Response z informacjami o klastrze"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    cluster_name: Optional[str] = None
    region: Optional[str] = None
    status: Optional[str] = None
    endpoint: Optional[str] = None


@router.post("/create", response_model=EksClusterResponse)
async def create_eks_cluster(request: EksClusterRequest):
    """
    Utwórz klaster AWS EKS
    
    Credentials są przekazywane w requeście i używane jednorazowo.
    Nie są zapisywane na serwerze.
    """
    try:
        result = eks_service.create_cluster(
            cluster_name=request.cluster_name,
            region=request.region,
            aws_access_key=request.aws_access_key,
            aws_secret_key=request.aws_secret_key,
            node_count=request.node_count,
            instance_type=request.instance_type,
            vpc_cidr=request.vpc_cidr
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to create EKS cluster")
            )
        
        # TODO: Opcjonalnie zainstaluj monitoring
        if request.install_monitoring:
            # Implementacja instalacji monitoringu na EKS
            pass
        
        return EksClusterResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating EKS cluster: {str(e)}"
        )


@router.post("/list")
async def list_eks_clusters(credentials: EksCredentials):
    """
    Lista klastrów EKS w danym regionie
    """
    try:
        result = eks_service.list_clusters(
            region=credentials.region,
            aws_access_key=credentials.aws_access_key,
            aws_secret_key=credentials.aws_secret_key
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to list EKS clusters")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing EKS clusters: {str(e)}"
        )


@router.delete("/{cluster_name}")
async def delete_eks_cluster(
    cluster_name: str,
    credentials: EksCredentials
):
    """
    Usuń klaster EKS
    """
    try:
        result = eks_service.delete_cluster(
            cluster_name=cluster_name,
            region=credentials.region,
            aws_access_key=credentials.aws_access_key,
            aws_secret_key=credentials.aws_secret_key
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to delete EKS cluster")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting EKS cluster: {str(e)}"
        )


@router.get("/{cluster_name}/status")
async def get_eks_cluster_status(
    cluster_name: str,
    region: str,
    aws_access_key: str,
    aws_secret_key: str
):
    """
    Pobierz status klastra EKS
    """
    try:
        result = eks_service.get_cluster_status(
            cluster_name=cluster_name,
            region=region,
            aws_access_key=aws_access_key,
            aws_secret_key=aws_secret_key
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=404,
                detail=result.get("error", "Cluster not found")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting cluster status: {str(e)}"
        )
