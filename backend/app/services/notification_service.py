"""
Notification Service - Real-time notifications via SSE (Server-Sent Events)
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional
from collections import defaultdict
import uuid

class NotificationService:
    """
    Service for managing real-time notifications using Server-Sent Events (SSE)
    """
    
    def __init__(self):
        # Kolejki powiadomień dla każdego użytkownika: {user_id: Queue}
        self.user_queues: Dict[str, asyncio.Queue] = {}
        
        # Historia powiadomień (ostatnie 50 dla każdego użytkownika)
        self.notification_history: Dict[str, list] = defaultdict(list)
        
        # Max notifications to keep in history per user
        self.max_history_per_user = 50
    
    async def register_user(self, user_id: str) -> asyncio.Queue:
        """
        Register a user and create a queue for their notifications
        
        Args:
            user_id: User identifier
            
        Returns:
            asyncio.Queue for this user's notifications
        """
        if user_id not in self.user_queues:
            self.user_queues[user_id] = asyncio.Queue()
            print(f"[NotificationService] Registered user: {user_id}")
        
        return self.user_queues[user_id]
    
    def unregister_user(self, user_id: str):
        """
        Unregister a user and remove their queue
        
        Args:
            user_id: User identifier
        """
        if user_id in self.user_queues:
            del self.user_queues[user_id]
            print(f"[NotificationService] Unregistered user: {user_id}")
    
    async def send_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        severity: str = "info"
    ):
        """
        Send a notification to a specific user
        
        Args:
            user_id: User identifier
            notification_type: Type of notification (operation, alert, info, etc.)
            title: Notification title
            message: Notification message
            metadata: Additional metadata (cluster_name, operation_id, etc.)
            severity: success, error, warning, info
        """
        notification_id = str(uuid.uuid4())
        notification = {
            "id": notification_id,
            "type": notification_type,
            "severity": severity,
            "title": title,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
            "read": False,
            "user_id": user_id
        }
        
        # Save to Firebase Firestore
        try:
            from .firebase_service import firebase_service
            if firebase_service.db:
                firebase_service.db.collection('notifications').document(notification_id).set(notification)
                print(f"[NotificationService] Saved notification to Firebase: {notification_id}")
        except Exception as e:
            print(f"[NotificationService] Error saving to Firebase: {e}")
        
        # Add to in-memory history (for fast access)
        self.notification_history[user_id].insert(0, notification)
        
        # Keep only last N notifications in memory
        if len(self.notification_history[user_id]) > self.max_history_per_user:
            self.notification_history[user_id] = self.notification_history[user_id][:self.max_history_per_user]
        
        # Send to user's queue if they're connected (real-time SSE)
        if user_id in self.user_queues:
            try:
                await self.user_queues[user_id].put(notification)
                print(f"[NotificationService] Sent notification to {user_id}: {title}")
            except Exception as e:
                print(f"[NotificationService] Error sending notification: {e}")
        else:
            print(f"[NotificationService] User {user_id} not connected, notification saved to Firebase")
    
    async def broadcast_notification(
        self,
        notification_type: str,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        severity: str = "info"
    ):
        """
        Broadcast a notification to all connected users
        
        Args:
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            metadata: Additional metadata
            severity: success, error, warning, info
        """
        for user_id in list(self.user_queues.keys()):
            await self.send_notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                metadata=metadata,
                severity=severity
            )
    
    def get_notification_history(self, user_id: str, limit: int = 20) -> list:
        """
        Get notification history for a user from Firebase
        
        Args:
            user_id: User identifier
            limit: Maximum number of notifications to return
            
        Returns:
            List of notifications
        """
        try:
            from .firebase_service import firebase_service
            if firebase_service.db:
                # Query Firebase Firestore
                notifications_ref = firebase_service.db.collection('notifications')
                query = notifications_ref.where('user_id', '==', user_id).order_by('timestamp', direction='DESCENDING').limit(limit)
                docs = query.stream()
                
                notifications = []
                for doc in docs:
                    notification = doc.to_dict()
                    notifications.append(notification)
                
                print(f"[NotificationService] Loaded {len(notifications)} notifications from Firebase for {user_id}")
                return notifications
        except Exception as e:
            print(f"[NotificationService] Error loading from Firebase: {e}")
        
        # Fallback to in-memory history
        return self.notification_history.get(user_id, [])[:limit]
    
    def get_unread_count(self, user_id: str) -> int:
        """
        Get count of unread notifications for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of unread notifications
        """
        notifications = self.notification_history.get(user_id, [])
        return sum(1 for n in notifications if not n.get("read", False))
    
    def mark_as_read(self, user_id: str, notification_id: str):
        """
        Mark a notification as read in Firebase and memory
        
        Args:
            user_id: User identifier
            notification_id: Notification ID
        """
        # Update in Firebase
        try:
            from .firebase_service import firebase_service
            if firebase_service.db:
                firebase_service.db.collection('notifications').document(notification_id).update({
                    'read': True
                })
                print(f"[NotificationService] Marked notification {notification_id} as read in Firebase")
        except Exception as e:
            print(f"[NotificationService] Error updating Firebase: {e}")
        
        # Update in memory
        notifications = self.notification_history.get(user_id, [])
        for notif in notifications:
            if notif["id"] == notification_id:
                notif["read"] = True
                print(f"[NotificationService] Marked notification {notification_id} as read in memory")
                break
    
    def mark_all_as_read(self, user_id: str):
        """
        Mark all notifications as read for a user in Firebase and memory
        
        Args:
            user_id: User identifier
        """
        # Update in Firebase
        try:
            from .firebase_service import firebase_service
            if firebase_service.db:
                notifications_ref = firebase_service.db.collection('notifications')
                query = notifications_ref.where('user_id', '==', user_id).where('read', '==', False)
                docs = query.stream()
                
                batch = firebase_service.db.batch()
                count = 0
                for doc in docs:
                    batch.update(doc.reference, {'read': True})
                    count += 1
                
                if count > 0:
                    batch.commit()
                    print(f"[NotificationService] Marked {count} notifications as read in Firebase for {user_id}")
        except Exception as e:
            print(f"[NotificationService] Error updating Firebase: {e}")
        
        # Update in memory
        notifications = self.notification_history.get(user_id, [])
        for notif in notifications:
            notif["read"] = True
        print(f"[NotificationService] Marked all notifications as read in memory for {user_id}")
    
    def delete_notification(self, user_id: str, notification_id: str):
        """
        Delete a notification from Firebase and memory
        
        Args:
            user_id: User identifier
            notification_id: Notification ID
        """
        # Delete from Firebase
        try:
            from .firebase_service import firebase_service
            if firebase_service.db:
                firebase_service.db.collection('notifications').document(notification_id).delete()
                print(f"[NotificationService] Deleted notification {notification_id} from Firebase")
        except Exception as e:
            print(f"[NotificationService] Error deleting from Firebase: {e}")
        
        # Delete from memory
        notifications = self.notification_history.get(user_id, [])
        self.notification_history[user_id] = [n for n in notifications if n["id"] != notification_id]
        print(f"[NotificationService] Deleted notification {notification_id} from memory")


# Global singleton instance
notification_service = NotificationService()
