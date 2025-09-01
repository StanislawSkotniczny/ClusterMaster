import os
import subprocess
import shutil
import uuid
from typing import Dict, Any, Optional, Tuple
from jinja2 import Environment, FileSystemLoader
from app.core.config import settings
from app.services.firebase_service import FirestoreService
import asyncio
import threading

class TerraformRunner:
    def __init__(self):
        self.templates_dir = settings.templates_dir
        self.infra_dir = settings.infra_dir
        self.terraform_bin = settings.terraform_bin_path
        
        # Ensure directories exist
        os.makedirs(self.infra_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Setup Jinja2 environment
        self.jinja_env = Environment(loader=FileSystemLoader(self.templates_dir))
    
    def generate_run_id(self) -> str:
        """Generate unique run ID"""
        return str(uuid.uuid4())
    
    def get_run_directory(self, run_id: str) -> str:
        """Get directory path for specific run"""
        return os.path.join(self.infra_dir, run_id)
    
    def render_terraform_config(self, config: Dict[str, Any], run_id: str) -> str:
        """
        Render Terraform configuration from template
        """
        run_dir = self.get_run_directory(run_id)
        os.makedirs(run_dir, exist_ok=True)
        
        # Choose template based on provider
        template_name = f"{config['provider']}_cluster.tf.j2"
        
        try:
            template = self.jinja_env.get_template(template_name)
            terraform_config = template.render(**config)
            
            # Write main.tf file
            main_tf_path = os.path.join(run_dir, "main.tf")
            with open(main_tf_path, 'w') as f:
                f.write(terraform_config)
            
            # Copy provider configuration if exists
            provider_tf_path = os.path.join(self.templates_dir, "providers.tf")
            if os.path.exists(provider_tf_path):
                shutil.copy2(provider_tf_path, os.path.join(run_dir, "providers.tf"))
            
            return run_dir
            
        except Exception as e:
            raise Exception(f"Failed to render Terraform config: {str(e)}")
    
    def run_terraform_command(self, command: list, cwd: str) -> Tuple[int, str, str]:
        """
        Execute terraform command and return result
        """
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Terraform command timed out"
        except Exception as e:
            return 1, "", f"Failed to execute command: {str(e)}"
    
    async def deploy_cluster_async(self, config: Dict[str, Any], run_id: str, user_id: str):
        """
        Deploy cluster asynchronously
        """
        try:
            # Update status to running
            await FirestoreService.update_deployment_status(run_id, "running", "Starting deployment...")
            
            # Render Terraform configuration
            run_dir = self.render_terraform_config(config, run_id)
            
            # Initialize Terraform
            await FirestoreService.update_deployment_status(run_id, "running", "Initializing Terraform...")
            init_code, init_out, init_err = self.run_terraform_command(
                [self.terraform_bin, "init"], run_dir
            )
            
            if init_code != 0:
                error_msg = f"Terraform init failed:\n{init_err}\n{init_out}"
                await FirestoreService.update_deployment_status(run_id, "failed", error_msg)
                return
            
            # Plan Terraform
            await FirestoreService.update_deployment_status(run_id, "running", "Planning deployment...")
            plan_code, plan_out, plan_err = self.run_terraform_command(
                [self.terraform_bin, "plan", "-out=tfplan"], run_dir
            )
            
            if plan_code != 0:
                error_msg = f"Terraform plan failed:\n{plan_err}\n{plan_out}"
                await FirestoreService.update_deployment_status(run_id, "failed", error_msg)
                return
            
            # Apply Terraform
            await FirestoreService.update_deployment_status(run_id, "running", "Applying configuration...")
            apply_code, apply_out, apply_err = self.run_terraform_command(
                [self.terraform_bin, "apply", "-auto-approve", "tfplan"], run_dir
            )
            
            if apply_code != 0:
                error_msg = f"Terraform apply failed:\n{apply_err}\n{apply_out}"
                await FirestoreService.update_deployment_status(run_id, "failed", error_msg)
                return
            
            # Success
            success_msg = f"Deployment completed successfully:\n{apply_out}"
            await FirestoreService.update_deployment_status(run_id, "completed", success_msg)
            
        except Exception as e:
            error_msg = f"Deployment failed with exception: {str(e)}"
            await FirestoreService.update_deployment_status(run_id, "failed", error_msg)
    
    def start_deployment(self, config: Dict[str, Any], run_id: str, user_id: str):
        """
        Start deployment in background thread
        """
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.deploy_cluster_async(config, run_id, user_id))
            loop.close()
        
        thread = threading.Thread(target=run_async)
        thread.daemon = True
        thread.start()
    
    async def destroy_cluster(self, run_id: str) -> bool:
        """
        Destroy cluster using Terraform
        """
        run_dir = self.get_run_directory(run_id)
        
        if not os.path.exists(run_dir):
            return False
        
        try:
            # Update status
            await FirestoreService.update_deployment_status(run_id, "destroying", "Destroying cluster...")
            
            # Run terraform destroy
            destroy_code, destroy_out, destroy_err = self.run_terraform_command(
                [self.terraform_bin, "destroy", "-auto-approve"], run_dir
            )
            
            if destroy_code != 0:
                error_msg = f"Terraform destroy failed:\n{destroy_err}\n{destroy_out}"
                await FirestoreService.update_deployment_status(run_id, "destroy_failed", error_msg)
                return False
            
            # Cleanup directory
            shutil.rmtree(run_dir, ignore_errors=True)
            
            # Update status
            await FirestoreService.update_deployment_status(run_id, "destroyed", "Cluster destroyed successfully")
            await FirestoreService.delete_deployment(run_id)
            
            return True
            
        except Exception as e:
            error_msg = f"Destroy failed with exception: {str(e)}"
            await FirestoreService.update_deployment_status(run_id, "destroy_failed", error_msg)
            return False

terraform_runner = TerraformRunner()