import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Firebase
    firebase_credentials_path: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
    
    # Terraform
    terraform_bin_path: str = os.getenv("TERRAFORM_BIN_PATH", "terraform")
    infra_dir: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "infra")
    templates_dir: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates")
    
    # API
    api_v1_str: str = "/api/v1"
    
    class Config:
        env_file = ".env"

settings = Settings()