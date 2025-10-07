"""
Data Models for Projects
Using Pydantic for data validation and serialization
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ProjectStatus(str, Enum):
    """Project status enumeration"""
    ACTIVE = "active"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class FileMetadata(BaseModel):
    """File metadata model"""
    original_name: str = Field(description="Original filename")
    file_size: int = Field(ge=0, description="File size in bytes")
    upload_time: datetime = Field(description="Upload timestamp")
    validation_status: bool = Field(description="Whether file passed validation")
    error_count: int = Field(ge=0, default=0, description="Number of errors found")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Project(BaseModel):
    """Project data model"""
    id: str = Field(description="Unique project ID (UUID)")
    owner_uid: str = Field(description="Firebase user ID of owner")
    name: str = Field(min_length=1, max_length=100, description="Project name")
    description: str = Field(default="", max_length=500, description="Project description")
    ai_chat_enabled: bool = Field(default=False, description="Enable AI chat functionality")
    save_files_on_server: bool = Field(default=False, description="Save files on server")
    status: ProjectStatus = Field(default=ProjectStatus.ACTIVE, description="Project status")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    file_metadata: Optional[FileMetadata] = Field(None, description="Uploaded file metadata")
    validation_status: Optional[bool] = Field(None, description="Validation status")
    error_count: int = Field(default=0, ge=0, description="Number of errors")
    session_id: Optional[str] = Field(None, description="Associated chat session ID")

    @validator('name')
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty or whitespace only')
        return v.strip()

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.dict(exclude_none=True)

    def to_api_response(self) -> Dict[str, Any]:
        """Convert to API response format"""
        data = self.to_dict()
        # Format timestamps
        if 'created_at' in data:
            data['created_at'] = data['created_at'].isoformat() if isinstance(data['created_at'], datetime) else data['created_at']
        if 'updated_at' in data:
            data['updated_at'] = data['updated_at'].isoformat() if isinstance(data['updated_at'], datetime) else data['updated_at']
        return data


class ProjectListItem(BaseModel):
    """Simplified project model for list views"""
    id: str
    name: str
    status: ProjectStatus
    ai_chat_enabled: bool
    save_files_on_server: bool
    created_at: datetime
    updated_at: datetime
    error_count: int = 0
    has_file: bool = Field(default=False, description="Whether file has been uploaded")

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @classmethod
    def from_project(cls, project: Project):
        """Create from full Project model"""
        return cls(
            id=project.id,
            name=project.name,
            status=project.status,
            ai_chat_enabled=project.ai_chat_enabled,
            save_files_on_server=project.save_files_on_server,
            created_at=project.created_at,
            updated_at=project.updated_at,
            error_count=project.error_count,
            has_file=project.file_metadata is not None
        )


class User(BaseModel):
    """User data model"""
    uid: str = Field(description="Firebase user ID")
    email: str = Field(description="User email")
    name: str = Field(description="Display name")
    created_at: datetime = Field(description="Account creation timestamp")
    last_login: datetime = Field(description="Last login timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    project_count: int = Field(default=0, ge=0, description="Number of projects")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProjectStats(BaseModel):
    """Project statistics model"""
    total_projects: int = Field(ge=0)
    by_status: Dict[str, int] = Field(default_factory=dict)
    features: Dict[str, int] = Field(default_factory=dict)


class UploadResult(BaseModel):
    """File upload result model"""
    success: bool
    file_path: str
    file_size: int
    filename: str
    validation_required: bool = True


class ValidationResult(BaseModel):
    """Validation result model"""
    is_valid: bool
    error_count: int = 0
    processed_path: Optional[str] = None
    error_json_path: Optional[str] = None
    message: Optional[str] = None


class ChatSession(BaseModel):
    """Chat session model"""
    session_id: str
    project_id: str
    owner_uid: str
    created_at: datetime
    last_activity: datetime
    message_count: int = 0
    status: str = Field(default="active", pattern="^(active|inactive|expired)$")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorDetail(BaseModel):
    """Error detail model for validation errors"""
    row: int
    column: str
    error_type: str
    error_message: str
    current_value: Any
    expected_format: Optional[str] = None


class ErrorSummary(BaseModel):
    """Error summary model"""
    total_errors: int
    error_rows: int
    categories: Dict[str, int]
    details: List[ErrorDetail] = []

    class Config:
        extra = 'allow'
