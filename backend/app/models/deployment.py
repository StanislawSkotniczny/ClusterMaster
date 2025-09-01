from typing import Optional, Dict, Any
from enum import Enum

class DeploymentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DESTROYING = "destroying"
    DESTROYED = "destroyed"
    DESTROY_FAILED = "destroy_failed"

class ClusterProvider(str, Enum):
    LOCAL = "local"
    AWS = "aws"