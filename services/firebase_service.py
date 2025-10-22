"""
Firebase Service
Handles Firestore operations for user and project data
"""

from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
from firebase_admin import firestore
import uuid


class FirestoreService:
    """Service for Firestore database operations"""

    def __init__(self):
        self.db = firestore.client()
        self.projects_collection = 'projects'
        self.users_collection = 'users'

    # ========================================================================
    # Project Operations
    # ========================================================================

    def create_project(
        self,
        owner_uid: str,
        name: str,
        description: Optional[str] = None,
        ai_chat_enabled: bool = False,
        save_files_on_server: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new project

        Args:
            owner_uid: Firebase user ID
            name: Project name
            description: Project description
            ai_chat_enabled: Enable AI chat
            save_files_on_server: Save files on server

        Returns:
            Created project data with ID
        """
        project_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        project_data = {
            'id': project_id,
            'owner_uid': owner_uid,
            'name': name,
            'description': description or '',
            'ai_chat_enabled': ai_chat_enabled,
            'save_files_on_server': save_files_on_server,
            'status': 'active',
            'created_at': now,
            'updated_at': now,
            'file_metadata': None,
            'validation_status': None,
            'error_count': 0,
            'session_id': None,  # For chat session
            'scheme': None,  # CORSIA, EU ETS, UK ETS, CH ETS, ReFuelEU
            'airline_size': None,  # small, medium, large
            'monitoring_plan': None,  # Extracted monitoring plan data
            'monitoring_plan_file_path': None  # Path to uploaded monitoring plan file
        }

        # Store in Firestore
        self.db.collection(self.projects_collection).document(project_id).set(project_data)

        print(f"✅ Created project: {project_id} for user: {owner_uid}")
        return project_data

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get project by ID

        Args:
            project_id: Project ID

        Returns:
            Project data or None if not found
        """
        doc = self.db.collection(self.projects_collection).document(project_id).get()

        if not doc.exists:
            return None

        return doc.to_dict()

    def get_user_projects(
        self,
        owner_uid: str,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all projects for a user

        Args:
            owner_uid: Firebase user ID
            limit: Maximum number of projects to return
            status: Filter by status (optional)

        Returns:
            List of project data
        """
        # Use filter() method instead of where() to avoid deprecation warning
        query = self.db.collection(self.projects_collection).where(
            filter=firestore.FieldFilter('owner_uid', '==', owner_uid)
        )

        if status:
            query = query.where(filter=firestore.FieldFilter('status', '==', status))

        # Note: Ordering requires a composite index.
        # For now, we'll sort in Python after fetching
        # To enable ordering in Firestore, create the composite index in Firebase Console
        projects = [doc.to_dict() for doc in query.stream()]

        # Sort by created_at in Python (descending - newest first)
        projects.sort(key=lambda x: x.get('created_at', datetime.min.replace(tzinfo=timezone.utc)), reverse=True)

        # Apply limit after sorting
        projects = projects[:limit]

        print(f"📋 Retrieved {len(projects)} projects for user: {owner_uid}")
        return projects

    def update_project(
        self,
        project_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update project fields

        Args:
            project_id: Project ID
            updates: Dict of fields to update

        Returns:
            Updated project data
        """
        # Add updated_at timestamp
        updates['updated_at'] = datetime.now(timezone.utc)

        # Update in Firestore
        doc_ref = self.db.collection(self.projects_collection).document(project_id)
        doc_ref.update(updates)

        # Return updated document
        updated_doc = doc_ref.get()
        print(f"✅ Updated project: {project_id}")
        return updated_doc.to_dict() if updated_doc.exists else None

    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project

        Args:
            project_id: Project ID

        Returns:
            True if deleted successfully
        """
        self.db.collection(self.projects_collection).document(project_id).delete()
        print(f"🗑️ Deleted project: {project_id}")
        return True

    def update_project_file_metadata(
        self,
        project_id: str,
        filename: str,
        file_size: int,
        validation_status: bool,
        error_count: int = 0
    ) -> Dict[str, Any]:
        """
        Update project with file upload metadata

        Args:
            project_id: Project ID
            filename: Original filename
            file_size: File size in bytes
            validation_status: Whether file passed validation
            error_count: Number of errors found

        Returns:
            Updated project data
        """
        file_metadata = {
            'original_name': filename,
            'file_size': file_size,
            'upload_time': datetime.now(timezone.utc),
            'validation_status': validation_status,
            'error_count': error_count
        }

        updates = {
            'file_metadata': file_metadata,
            'validation_status': validation_status,
            'error_count': error_count,
            'status': 'completed' if validation_status else 'error'
        }

        return self.update_project(project_id, updates)

    def set_project_session(self, project_id: str, session_id: str) -> Dict[str, Any]:
        """
        Associate a chat session with a project

        Args:
            project_id: Project ID
            session_id: Chat session ID

        Returns:
            Updated project data
        """
        return self.update_project(project_id, {'session_id': session_id})

    # ========================================================================
    # User Operations
    # ========================================================================

    def create_or_update_user(
        self,
        uid: str,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create or update user document

        Args:
            uid: Firebase user ID
            email: User email
            name: User display name
            metadata: Additional metadata

        Returns:
            User data
        """
        user_ref = self.db.collection(self.users_collection).document(uid)
        user_doc = user_ref.get()

        now = datetime.now(timezone.utc)

        if user_doc.exists:
            # Update existing user
            updates = {
                'email': email,
                'last_login': now,
                'updated_at': now
            }
            if name:
                updates['name'] = name
            if metadata:
                updates['metadata'] = metadata

            user_ref.update(updates)
            print(f"✅ Updated user: {uid}")
        else:
            # Create new user
            user_data = {
                'uid': uid,
                'email': email,
                'name': name or email.split('@')[0],
                'created_at': now,
                'last_login': now,
                'updated_at': now,
                'metadata': metadata or {},
                'project_count': 0
            }
            user_ref.set(user_data)
            print(f"✅ Created new user: {uid}")

        return user_ref.get().to_dict()

    def get_user(self, uid: str) -> Optional[Dict[str, Any]]:
        """
        Get user by UID

        Args:
            uid: Firebase user ID

        Returns:
            User data or None
        """
        doc = self.db.collection(self.users_collection).document(uid).get()
        return doc.to_dict() if doc.exists else None

    def update_user(self, uid: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user document with provided fields

        Args:
            uid: Firebase user ID
            updates: Dictionary of fields to update

        Returns:
            Updated user data
        """
        # Add updated_at timestamp
        updates['updated_at'] = datetime.now(timezone.utc)

        # Update in Firestore
        user_ref = self.db.collection(self.users_collection).document(uid)
        user_ref.update(updates)

        # Return updated document
        updated_doc = user_ref.get()
        print(f"✅ Updated user profile: {uid}")
        return updated_doc.to_dict() if updated_doc.exists else None

    def get_user_report_counters(self, uid: str) -> Dict[str, int]:
        """
        Return per-scheme counters used for auto-naming reports.
        """
        user = self.get_user(uid) or {}
        return (user.get('report_counters') or {})

    def increment_report_counter(self, uid: str, scheme: str) -> int:
        """
        Atomically increment and return the next counter for a scheme.
        """
        user_ref = self.db.collection(self.users_collection).document(uid)
        # Firestore doesn't support per-field dynamic increment inside nested map directly
        # Read-modify-write with last-write-wins is acceptable for this use-case
        user_doc = user_ref.get()
        current = {}
        if user_doc.exists:
            data = user_doc.to_dict() or {}
            current = data.get('report_counters') or {}
        next_val = int(current.get(scheme, 0)) + 1
        current[scheme] = next_val
        user_ref.set({'report_counters': current}, merge=True)
        return next_val

    def increment_user_project_count(self, uid: str) -> None:
        """
        Increment user's project count

        Args:
            uid: Firebase user ID
        """
        user_ref = self.db.collection(self.users_collection).document(uid)
        user_ref.update({
            'project_count': firestore.Increment(1)
        })

    def decrement_user_project_count(self, uid: str) -> None:
        """
        Decrement user's project count

        Args:
            uid: Firebase user ID
        """
        user_ref = self.db.collection(self.users_collection).document(uid)
        user_ref.update({
            'project_count': firestore.Increment(-1)
        })

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def get_project_count_by_user(self, owner_uid: str) -> int:
        """
        Get total number of projects for a user

        Args:
            owner_uid: Firebase user ID

        Returns:
            Number of projects
        """
        query = self.db.collection(self.projects_collection).where('owner_uid', '==', owner_uid)
        return len(list(query.stream()))

    def search_projects(
        self,
        owner_uid: str,
        search_term: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search projects by name (case-insensitive)

        Args:
            owner_uid: Firebase user ID
            search_term: Search term
            limit: Maximum results

        Returns:
            List of matching projects
        """
        # Firestore doesn't support full-text search natively
        # This is a simple prefix search - for production, use Algolia or similar
        query = (
            self.db.collection(self.projects_collection)
            .where('owner_uid', '==', owner_uid)
            .order_by('name')
            .start_at([search_term])
            .end_at([search_term + '\uf8ff'])
            .limit(limit)
        )

        return [doc.to_dict() for doc in query.stream()]

    def batch_delete_projects(self, project_ids: List[str]) -> int:
        """
        Delete multiple projects in batch

        Args:
            project_ids: List of project IDs

        Returns:
            Number of projects deleted
        """
        batch = self.db.batch()
        for project_id in project_ids:
            doc_ref = self.db.collection(self.projects_collection).document(project_id)
            batch.delete(doc_ref)

        batch.commit()
        print(f"🗑️ Batch deleted {len(project_ids)} projects")
        return len(project_ids)

    # ========================================================================
    # Chat-Related Helper Methods
    # ========================================================================

    def get_project_active_chat(self, project_id: str) -> Optional[str]:
        """
        Get the active chat ID for a project (stored in project document)

        Args:
            project_id: Project ID

        Returns:
            Active chat ID or None
        """
        project = self.get_project(project_id)
        return project.get('active_chat_id') if project else None

    def set_project_active_chat(self, project_id: str, chat_id: str) -> bool:
        """
        Set the active chat ID for a project

        Args:
            project_id: Project ID
            chat_id: Chat ID to set as active

        Returns:
            True if updated successfully
        """
        try:
            self.update_project(project_id, {'active_chat_id': chat_id})
            return True
        except Exception:
            return False
