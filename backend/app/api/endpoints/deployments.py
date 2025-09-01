from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.schemas.deployment import DeploymentCreate, DeploymentResponse, DeploymentStartResponse
from app.services.firebase_service import verify_token, FirestoreService
from app.services.terraform_runner import terraform_runner
from app.core.security import get_current_user_id

router = APIRouter()

@router.post("/deploy", response_model=DeploymentStartResponse)
async def create_deployment(
    deployment: DeploymentCreate,
    token_data: dict = Depends(verify_token)
):
    """
    Create new cluster deployment
    """
    user_id = get_current_user_id(token_data)
    
    # Validate configuration based on provider
    if deployment.provider == "aws":
        if not all([deployment.aws_region, deployment.instance_type, 
                   deployment.vpc_cidr, deployment.aws_access_key, deployment.aws_secret_key]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="AWS provider requires all AWS-specific fields"
            )
    elif deployment.provider == "local":
        if not deployment.kubeconfig_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Local provider requires kubeconfig_path"
            )
    
    # Generate run ID
    run_id = terraform_runner.generate_run_id()
    
    # Save deployment to Firestore
    deployment_data = deployment.dict()
    deployment_data['run_id'] = run_id
    
    await FirestoreService.save_deployment(user_id, deployment_data)
    
    # Start deployment process in background
    terraform_runner.start_deployment(deployment_data, run_id, user_id)
    
    return DeploymentStartResponse(
        run_id=run_id,
        message="Deployment started successfully",
        status="pending"
    )

@router.get("/deployments", response_model=List[DeploymentResponse])
async def get_deployments(
    token_data: dict = Depends(verify_token)
):
    """
    Get all deployments for the current user
    """
    user_id = get_current_user_id(token_data)
    deployments = await FirestoreService.get_user_deployments(user_id)
    
    return [DeploymentResponse(**deployment) for deployment in deployments]

@router.delete("/deploy/{run_id}")
async def destroy_deployment(
    run_id: str,
    token_data: dict = Depends(verify_token)
):
    """
    Destroy cluster deployment
    """
    user_id = get_current_user_id(token_data)
    
    # Verify user owns this deployment
    deployments = await FirestoreService.get_user_deployments(user_id)
    deployment = next((d for d in deployments if d.get('run_id') == run_id), None)
    
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found"
        )
    
    success = await terraform_runner.destroy_cluster(run_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to destroy cluster"
        )
    
    return {"message": "Cluster destruction initiated"}

@router.get("/deploy/{run_id}/status")
async def get_deployment_status(
    run_id: str,
    token_data: dict = Depends(verify_token)
):
    """
    Get specific deployment status
    """
    user_id = get_current_user_id(token_data)
    
    deployments = await FirestoreService.get_user_deployments(user_id)
    deployment = next((d for d in deployments if d.get('run_id') == run_id), None)
    
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found"
        )
    
    return DeploymentResponse(**deployment)