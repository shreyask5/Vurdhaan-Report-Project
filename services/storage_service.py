"""
Storage Service
Handles file storage operations for projects
"""

import os
import shutil
from typing import Optional
from werkzeug.utils import secure_filename
from datetime import datetime
import tempfile


class StorageService:
    """Service for managing file storage"""

    def __init__(self, base_upload_folder: str = None):
        """
        Initialize storage service

        Args:
            base_upload_folder: Base directory for file uploads
                              If None, uses environment variable or default
        """
        self.base_folder = base_upload_folder or os.getenv(
            'UPLOAD_FOLDER',
            '/home/ubuntu/project/uploads'  # Default to Ubuntu server path
        )
        self.temp_folder = os.path.join(self.base_folder, 'temp')

        # Ensure base directories exist
        os.makedirs(self.base_folder, exist_ok=True)
        os.makedirs(self.temp_folder, exist_ok=True)

        print(f"✅ Storage service initialized: {self.base_folder}")

    # ========================================================================
    # Project Directory Management
    # ========================================================================

    def get_project_path(self, project_id: str) -> str:
        """
        Get path to project directory

        Args:
            project_id: Project ID

        Returns:
            Absolute path to project directory
        """
        return os.path.join(self.base_folder, project_id)

    def get_temp_path(self, project_id: str) -> str:
        """
        Get path to temporary project directory

        Args:
            project_id: Project ID

        Returns:
            Absolute path to temp project directory
        """
        return os.path.join(self.temp_folder, project_id)

    def create_project_directory(self, project_id: str) -> str:
        """
        Create directory for project files

        Args:
            project_id: Project ID

        Returns:
            Path to created directory
        """
        project_path = self.get_project_path(project_id)
        os.makedirs(project_path, exist_ok=True)
        print(f"📁 Created project directory: {project_path}")
        return project_path

    def create_temp_directory(self, project_id: str) -> str:
        """
        Create temporary directory for project files

        Args:
            project_id: Project ID

        Returns:
            Path to created temp directory
        """
        temp_path = self.get_temp_path(project_id)
        os.makedirs(temp_path, exist_ok=True)
        return temp_path

    def delete_project_files(self, project_id: str) -> bool:
        """
        Delete all files for a project

        Args:
            project_id: Project ID

        Returns:
            True if deleted successfully
        """
        project_path = self.get_project_path(project_id)
        temp_path = self.get_temp_path(project_id)

        # Delete permanent storage
        if os.path.exists(project_path):
            shutil.rmtree(project_path, ignore_errors=True)
            print(f"🗑️ Deleted project files: {project_path}")

        # Delete temp storage
        if os.path.exists(temp_path):
            shutil.rmtree(temp_path, ignore_errors=True)
            print(f"🗑️ Deleted temp files: {temp_path}")

        return True

    # ========================================================================
    # File Upload Operations
    # ========================================================================

    def save_uploaded_file(
        self,
        project_id: str,
        file,
        filename: Optional[str] = None
    ) -> str:
        """
        Save uploaded file to project directory (permanent storage)

        Args:
            project_id: Project ID
            file: File object from request
            filename: Custom filename (optional, uses original if None)

        Returns:
            Absolute path to saved file
        """
        # Create project directory if it doesn't exist
        project_path = self.create_project_directory(project_id)

        # Secure the filename
        if filename is None:
            filename = secure_filename(file.filename)
        else:
            filename = secure_filename(filename)

        # Full file path
        file_path = os.path.join(project_path, filename)

        # Save file
        file.save(file_path)
        print(f"💾 Saved file: {file_path}")

        return file_path

    def save_temp_file(
        self,
        project_id: str,
        file,
        filename: Optional[str] = None
    ) -> str:
        """
        Save uploaded file to temporary directory

        Args:
            project_id: Project ID
            file: File object from request
            filename: Custom filename (optional)

        Returns:
            Absolute path to saved temp file
        """
        # Create temp directory
        temp_path = self.create_temp_directory(project_id)

        # Secure filename
        if filename is None:
            filename = secure_filename(file.filename)
        else:
            filename = secure_filename(filename)

        # Full file path
        file_path = os.path.join(temp_path, filename)

        # Save file
        file.save(file_path)
        print(f"💾 Saved temp file: {file_path}")

        return file_path

    # ========================================================================
    # File Retrieval Operations
    # ========================================================================

    def get_file_path(
        self,
        project_id: str,
        filename: str,
        temp: bool = False
    ) -> Optional[str]:
        """
        Get path to a specific file in project

        Args:
            project_id: Project ID
            filename: Filename
            temp: Whether to look in temp directory

        Returns:
            Absolute path to file if exists, None otherwise
        """
        base_path = self.get_temp_path(project_id) if temp else self.get_project_path(project_id)
        file_path = os.path.join(base_path, secure_filename(filename))

        if os.path.exists(file_path):
            return file_path
        return None

    def get_all_project_files(self, project_id: str) -> list:
        """
        Get list of all files in project directory

        Args:
            project_id: Project ID

        Returns:
            List of filenames
        """
        project_path = self.get_project_path(project_id)

        if not os.path.exists(project_path):
            return []

        return [f for f in os.listdir(project_path) if os.path.isfile(os.path.join(project_path, f))]

    def file_exists(
        self,
        project_id: str,
        filename: str,
        temp: bool = False
    ) -> bool:
        """
        Check if file exists in project

        Args:
            project_id: Project ID
            filename: Filename
            temp: Whether to check temp directory

        Returns:
            True if file exists
        """
        file_path = self.get_file_path(project_id, filename, temp)
        return file_path is not None

    # ========================================================================
    # File Management Operations
    # ========================================================================

    def copy_file(
        self,
        project_id: str,
        source_filename: str,
        dest_filename: str,
        from_temp: bool = False,
        to_temp: bool = False
    ) -> str:
        """
        Copy file within project or between temp and permanent

        Args:
            project_id: Project ID
            source_filename: Source filename
            dest_filename: Destination filename
            from_temp: Copy from temp directory
            to_temp: Copy to temp directory

        Returns:
            Path to destination file
        """
        source_path = self.get_file_path(project_id, source_filename, from_temp)
        if not source_path:
            raise FileNotFoundError(f"Source file not found: {source_filename}")

        dest_base = self.get_temp_path(project_id) if to_temp else self.get_project_path(project_id)
        dest_path = os.path.join(dest_base, secure_filename(dest_filename))

        shutil.copy2(source_path, dest_path)
        print(f"📋 Copied file: {source_filename} -> {dest_filename}")

        return dest_path

    def move_file(
        self,
        project_id: str,
        source_filename: str,
        dest_filename: str,
        from_temp: bool = False,
        to_temp: bool = False
    ) -> str:
        """
        Move file within project or between temp and permanent

        Args:
            project_id: Project ID
            source_filename: Source filename
            dest_filename: Destination filename
            from_temp: Move from temp directory
            to_temp: Move to temp directory

        Returns:
            Path to destination file
        """
        source_path = self.get_file_path(project_id, source_filename, from_temp)
        if not source_path:
            raise FileNotFoundError(f"Source file not found: {source_filename}")

        dest_base = self.get_temp_path(project_id) if to_temp else self.get_project_path(project_id)
        os.makedirs(dest_base, exist_ok=True)
        dest_path = os.path.join(dest_base, secure_filename(dest_filename))

        shutil.move(source_path, dest_path)
        print(f"📦 Moved file: {source_filename} -> {dest_filename}")

        return dest_path

    def delete_file(
        self,
        project_id: str,
        filename: str,
        temp: bool = False
    ) -> bool:
        """
        Delete a specific file

        Args:
            project_id: Project ID
            filename: Filename
            temp: Whether file is in temp directory

        Returns:
            True if deleted successfully
        """
        file_path = self.get_file_path(project_id, filename, temp)

        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ Deleted file: {file_path}")
            return True

        return False

    # ========================================================================
    # Cleanup Operations
    # ========================================================================

    def cleanup_temp_files(self, older_than_hours: int = 24) -> int:
        """
        Clean up temporary files older than specified hours

        Args:
            older_than_hours: Delete files older than this many hours

        Returns:
            Number of directories cleaned up
        """
        import time

        current_time = time.time()
        cutoff_time = current_time - (older_than_hours * 3600)
        cleaned_count = 0

        if not os.path.exists(self.temp_folder):
            return 0

        for project_dir in os.listdir(self.temp_folder):
            project_path = os.path.join(self.temp_folder, project_dir)

            if os.path.isdir(project_path):
                # Check directory age
                dir_mtime = os.path.getmtime(project_path)

                if dir_mtime < cutoff_time:
                    shutil.rmtree(project_path, ignore_errors=True)
                    cleaned_count += 1
                    print(f"🧹 Cleaned up temp directory: {project_dir}")

        print(f"✅ Cleanup complete: {cleaned_count} temp directories removed")
        return cleaned_count

    def get_storage_stats(self) -> dict:
        """
        Get storage statistics

        Returns:
            Dict with storage stats
        """
        def get_dir_size(path):
            total = 0
            if os.path.exists(path):
                for dirpath, dirnames, filenames in os.walk(path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if os.path.exists(fp):
                            total += os.path.getsize(fp)
            return total

        permanent_size = get_dir_size(self.base_folder)
        temp_size = get_dir_size(self.temp_folder)

        project_count = len([d for d in os.listdir(self.base_folder)
                           if os.path.isdir(os.path.join(self.base_folder, d))
                           and d != 'temp'])

        return {
            'permanent_storage_bytes': permanent_size,
            'temp_storage_bytes': temp_size,
            'total_storage_bytes': permanent_size + temp_size,
            'project_count': project_count
        }
