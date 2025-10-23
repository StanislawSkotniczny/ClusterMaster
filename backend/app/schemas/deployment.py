from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.models.deployment import ClusterProvider, DeploymentStatus

class DeploymentCreate(BaseModel):
    provider: ClusterProvider
    cluster_name: str = Field(..., min_length=1)
    node_count: int = Field(..., ge=1)
    
    # AWS specific
    aws_region: Optional[str] = None
    instance_type: Optional[str] = None
    vpc_cidr: Optional[str] = None
    aws_access_key: Optional[str] = None
    aws_secret_key: Optional[str] = None
    
    # Local specific
    kubeconfig_path: Optional[str] = None
    
    # Resources
    cpu: Optional[int] = None
    memory: Optional[int] = None
    disk: Optional[int] = None
    
    # Advanced options
    k8s_version: Optional[str] = None
    enable_autoscaling: Optional[bool] = False
    min_nodes: Optional[int] = None
    max_nodes: Optional[int] = None
    tags: Optional[Dict[str, str]] = None

class DeploymentResponse(BaseModel):
    id: str
    user_id: str
    status: DeploymentStatus
    cluster_name: str
    provider: ClusterProvider
    node_count: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    logs: Optional[str] = None

class DeploymentStartResponse(BaseModel):
    run_id: str
    message: str
    status: str