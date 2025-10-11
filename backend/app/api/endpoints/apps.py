from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from ..services.app_service import AppService

router = APIRouter()
app_service = AppService()

class AppInstallRequest(BaseModel):
    name: str
    displayName: str
    namespace: str
    helmChart: str
    values: Dict[str, Any] = {}

@router.post("/install/{cluster_name}")
async def install_app(cluster_name: str, app_data: AppInstallRequest):
    """Install application on cluster"""
    try:
        result = app_service.install_app(cluster_name, app_data.dict())
        
        if result.get('success'):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Installation failed'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Installation error: {str(e)}")

@router.get("/installed/{cluster_name}")
async def get_installed_apps(cluster_name: str):
    """Get installed applications on cluster"""
    try:
        result = app_service.get_installed_apps(cluster_name)
        
        if result.get('success'):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to get apps'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting apps: {str(e)}")

@router.delete("/uninstall/{cluster_name}/{app_name}")
async def uninstall_app(cluster_name: str, app_name: str):
    """Uninstall application from cluster"""
    try:
        result = app_service.uninstall_app(cluster_name, app_name)
        
        if result.get('success'):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Uninstall failed'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Uninstall error: {str(e)}")

@router.get("/available")
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

@router.get("/search")
async def search_helm_charts(query: str, max_results: int = 20):
    """Search for Helm charts in repositories"""
    try:
        if not query or len(query) < 2:
            raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
        
        result = app_service.search_helm_charts(query, max_results)
        
        if result.get('success'):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Search failed'))
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
