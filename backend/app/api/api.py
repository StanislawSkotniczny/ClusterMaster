from fastapi import APIRouter
from app.api.endpoints import health, local_cluster

api_router = APIRouter()

# Include routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(local_cluster.router, prefix="/local-cluster", tags=["local-cluster"])