"""
Project Service
Business logic for project management
"""

from typing import Optional, Dict, List, Any
from services.firebase_service import FirestoreService
from services.storage_service import StorageService
import os


class ProjectService:
    """Service for project business logic"""

    def __init__(self):
        self.firestore = FirestoreService()
        self.storage = StorageService()

    # ========================================================================
    # Project Lifecycle
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
        Create a new project with validation

        Args:
            owner_uid: Firebase user ID
            name: Project name
            description: Project description
            ai_chat_enabled: Enable AI chat
            save_files_on_server: Save files on server

        Returns:
            Created project data
        """
        # Create project in Firestore
        project = self.firestore.create_project(
            owner_uid=owner_uid,
            name=name,
            description=description,
            ai_chat_enabled=ai_chat_enabled,
            save_files_on_server=save_files_on_server
        )

        # Create storage directory if needed
        if save_files_on_server:
            self.storage.create_project_directory(project['id'])

        # Update user project count
        self.firestore.increment_user_project_count(owner_uid)

        return project

    def get_project_with_validation(
        self,
        project_id: str,
        owner_uid: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get project and validate ownership

        Args:
            project_id: Project ID
            owner_uid: Expected owner UID

        Returns:
            Project data if exists and user is owner, None otherwise
        """
        project = self.firestore.get_project(project_id)

        if not project:
            return None

        # Validate ownership
        if project['owner_uid'] != owner_uid:
            return None

        return project

    def update_project(
        self,
        project_id: str,
        owner_uid: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update project with ownership validation

        Args:
            project_id: Project ID
            owner_uid: User UID (for ownership check)
            updates: Fields to update

        Returns:
            Updated project or None if not authorized
        """
        # Validate ownership first
        project = self.get_project_with_validation(project_id, owner_uid)
        if not project:
            return None

        # Disallow changing owner_uid
        if 'owner_uid' in updates:
            del updates['owner_uid']

        # Handle toggle changes
        if 'save_files_on_server' in updates:
            if updates['save_files_on_server'] and not project.get('save_files_on_server'):
                # Enabling file storage - create directory
                self.storage.create_project_directory(project_id)
            elif not updates['save_files_on_server'] and project.get('save_files_on_server'):
                # Disabling file storage - clean up files
                self.storage.delete_project_files(project_id)

        return self.firestore.update_project(project_id, updates)

    def delete_project(
        self,
        project_id: str,
        owner_uid: str
    ) -> bool:
        """
        Delete project with ownership validation and cleanup

        Args:
            project_id: Project ID
            owner_uid: User UID (for ownership check)

        Returns:
            True if deleted, False if not authorized
        """
        # Validate ownership
        project = self.get_project_with_validation(project_id, owner_uid)
        if not project:
            return False

        # Delete files if stored on server
        if project.get('save_files_on_server'):
            self.storage.delete_project_files(project_id)

        # Delete from Firestore
        self.firestore.delete_project(project_id)

        # Update user project count
        self.firestore.decrement_user_project_count(owner_uid)

        return True

    # ========================================================================
    # Project File Operations
    # ========================================================================

    def handle_file_upload(
        self,
        project_id: str,
        owner_uid: str,
        file,
        upload_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle CSV file upload for a project

        Args:
            project_id: Project ID
            owner_uid: User UID
            file: Uploaded file object
            upload_params: Validation parameters

        Returns:
            Upload result with validation status
        """
        # Validate ownership
        project = self.get_project_with_validation(project_id, owner_uid)
        if not project:
            raise PermissionError("Not authorized to upload to this project")

        # Update project status to processing
        self.firestore.update_project(project_id, {'status': 'processing'})

        try:
            # Save file based on project settings
            if project['save_files_on_server']:
                file_path = self.storage.save_uploaded_file(
                    project_id,
                    file,
                    'original.csv'
                )
            else:
                # Save to temp
                file_path = self.storage.save_temp_file(
                    project_id,
                    file,
                    'original.csv'
                )

            # Get file size
            file_size = os.path.getsize(file_path)

            # Return file info (validation will be done separately)
            return {
                'success': True,
                'file_path': file_path,
                'file_size': file_size,
                'filename': file.filename
            }

        except Exception as e:
            # Update project status to error
            self.firestore.update_project(project_id, {'status': 'error'})
            raise

    def update_validation_results(
        self,
        project_id: str,
        validation_status: bool,
        error_count: int = 0,
        file_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update project with validation results

        Args:
            project_id: Project ID
            validation_status: Whether validation passed
            error_count: Number of errors
            file_metadata: Additional file metadata

        Returns:
            Updated project
        """
        updates = {
            'validation_status': validation_status,
            'error_count': error_count,
            'status': 'completed' if validation_status else 'error'
        }

        if file_metadata:
            updates['file_metadata'] = file_metadata

        return self.firestore.update_project(project_id, updates)

    # ========================================================================
    # Project Listing and Search
    # ========================================================================

    def list_user_projects(
        self,
        owner_uid: str,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List all projects for a user

        Args:
            owner_uid: User UID
            status: Filter by status (optional)
            limit: Maximum results

        Returns:
            List of projects
        """
        return self.firestore.get_user_projects(owner_uid, limit, status)

    def search_projects(
        self,
        owner_uid: str,
        search_term: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search user's projects

        Args:
            owner_uid: User UID
            search_term: Search term
            limit: Maximum results

        Returns:
            List of matching projects
        """
        return self.firestore.search_projects(owner_uid, search_term, limit)

    # ========================================================================
    # Project Statistics
    # ========================================================================

    def get_project_stats(self, owner_uid: str) -> Dict[str, Any]:
        """
        Get statistics for user's projects

        Args:
            owner_uid: User UID

        Returns:
            Statistics dict
        """
        projects = self.list_user_projects(owner_uid)

        total = len(projects)
        active = len([p for p in projects if p.get('status') == 'active'])
        processing = len([p for p in projects if p.get('status') == 'processing'])
        completed = len([p for p in projects if p.get('status') == 'completed'])
        error = len([p for p in projects if p.get('status') == 'error'])

        ai_chat_enabled = len([p for p in projects if p.get('ai_chat_enabled')])
        files_on_server = len([p for p in projects if p.get('save_files_on_server')])

        return {
            'total_projects': total,
            'by_status': {
                'active': active,
                'processing': processing,
                'completed': completed,
                'error': error
            },
            'features': {
                'ai_chat_enabled': ai_chat_enabled,
                'files_on_server': files_on_server
            }
        }

    # ========================================================================
    # Cleanup Operations
    # ========================================================================

    def cleanup_old_projects(
        self,
        owner_uid: str,
        days_old: int = 30
    ) -> int:
        """
        Clean up old inactive projects

        Args:
            owner_uid: User UID
            days_old: Projects older than this many days

        Returns:
            Number of projects deleted
        """
        from datetime import datetime, timedelta

        projects = self.list_user_projects(owner_uid)
        cutoff_date = datetime.now() - timedelta(days=days_old)

        old_projects = [
            p for p in projects
            if p.get('created_at') and p['created_at'] < cutoff_date
            and p.get('status') in ['active', 'error']
        ]

        deleted_count = 0
        for project in old_projects:
            if self.delete_project(project['id'], owner_uid):
                deleted_count += 1

        return deleted_count
