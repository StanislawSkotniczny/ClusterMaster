import firebase_admin
from firebase_admin import credentials, firestore, auth
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
import os
import json
from typing import Dict, Any, Optional

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    try:
        # Priority 1: JSON string from environment variable
        if settings.firebase_credentials_json:
            cred_dict = json.loads(settings.firebase_credentials_json)
            cred = credentials.Certificate(cred_dict)
        # Priority 2: JSON file path
        elif os.path.exists(settings.firebase_credentials_path):
            cred = credentials.Certificate(settings.firebase_credentials_path)
        # Priority 3: Default credentials (for production with service account)
        else:
            cred = credentials.ApplicationDefault()
        
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized successfully")
    except Exception as e:
        print(f"⚠️ Firebase initialization error: {e}")
        # Don't initialize Firebase services if init failed
        firebase_admin._apps.clear()

# Only initialize Firebase services if app was initialized successfully
db = None
if firebase_admin._apps:
    try:
        db = firestore.client()
    except Exception as e:
        print(f"⚠️ Firestore client initialization error: {e}")

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Verify Firebase ID token and return user data
    """
    try:
        token = credentials.credentials
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}"
        )

class FirestoreService:
    @staticmethod
    async def save_deployment(user_id: str, deployment_data: dict) -> str:
        """
        Save deployment to Firestore
        """
        try:
            doc_ref = db.collection('deployments').document()
            deployment_data.update({
                'user_id': user_id,
                'created_at': firestore.SERVER_TIMESTAMP,
                'status': 'pending'
            })
            doc_ref.set(deployment_data)
            return doc_ref.id
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save deployment: {str(e)}"
            )
    
    @staticmethod
    async def get_user_deployments(user_id: str) -> list:
        """
        Get all deployments for a user
        """
        try:
            deployments = []
            docs = db.collection('deployments').where('user_id', '==', user_id).stream()
            
            for doc in docs:
                deployment = doc.to_dict()
                deployment['id'] = doc.id
                deployments.append(deployment)
            
            return deployments
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get deployments: {str(e)}"
            )
    
    @staticmethod
    async def update_deployment_status(deployment_id: str, status: str, logs: Optional[str] = None) -> bool:
        """
        Update deployment status
        """
        try:
            doc_ref = db.collection('deployments').document(deployment_id)
            update_data = {
                'status': status,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            if logs:
                update_data['logs'] = logs
            
            doc_ref.update(update_data)
            return True
        except Exception as e:
            print(f"Failed to update deployment status: {e}")
            return False

    @staticmethod
    async def delete_deployment(deployment_id: str) -> bool:
        """
        Delete deployment from Firestore
        """
        try:
            db.collection('deployments').document(deployment_id).delete()
            return True
        except Exception as e:
            print(f"Failed to delete deployment: {e}")
            return False