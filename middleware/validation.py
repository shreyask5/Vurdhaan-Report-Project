"""
Request Validation Middleware using Pydantic
Provides schema validation for API requests
"""

from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List, Any, Dict
from datetime import datetime
from flask import request, jsonify
from functools import wraps
import json


# ============================================================================
# Pydantic Schemas for Request Validation
# ============================================================================

class CreateProjectSchema(BaseModel):
    """Schema for creating a new project"""
    name: str = Field(
        min_length=1,
        max_length=100,
        description="Project name"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Project description"
    )
    ai_chat_enabled: bool = Field(
        default=False,
        description="Enable AI chat functionality"
    )
    save_files_on_server: bool = Field(
        default=False,
        description="Save uploaded files on server"
    )

    @validator('name')
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty or whitespace only')
        return v.strip()

    class Config:
        extra = 'forbid'  # Reject unknown fields


class UpdateProjectSchema(BaseModel):
    """Schema for updating a project"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    ai_chat_enabled: Optional[bool] = None
    save_files_on_server: Optional[bool] = None
    status: Optional[str] = Field(None, pattern='^(active|processing|error|completed)$')

    @validator('name')
    def name_not_empty_if_provided(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty or whitespace only')
        return v.strip() if v else None

    class Config:
        extra = 'forbid'


class CSVUploadSchema(BaseModel):
    """Schema for CSV upload parameters"""
    start_date: str = Field(
        description="Start date in YYYY-MM-DD format"
    )
    end_date: str = Field(
        description="End date in YYYY-MM-DD format"
    )
    date_format: str = Field(
        default="DMY",
        pattern='^(DMY|MDY|YMD)$',
        description="Date format"
    )
    flight_starts_with: str = Field(
        default="",
        max_length=10,
        description="Flight number prefix filter"
    )
    fuel_method: str = Field(
        default="Block Off - Block On",
        description="Fuel calculation method"
    )
    column_mapping: Optional[List[str]] = Field(
        None,
        description="CSV column mapping"
    )

    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')

    @validator('end_date')
    def end_after_start(cls, v, values):
        if 'start_date' in values:
            start = datetime.strptime(values['start_date'], '%Y-%m-%d')
            end = datetime.strptime(v, '%Y-%m-%d')
            if end < start:
                raise ValueError('end_date must be after start_date')
        return v

    class Config:
        extra = 'forbid'


class ChatQuerySchema(BaseModel):
    """Schema for chat query"""
    query: str = Field(
        min_length=1,
        max_length=1000,
        description="Natural language query"
    )
    session_id: Optional[str] = Field(
        None,
        description="Chat session ID (optional for continuation)"
    )

    @validator('query')
    def query_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()

    class Config:
        extra = 'forbid'


class SchemeSelectionSchema(BaseModel):
    """Schema for scheme selection"""
    scheme: str = Field(
        description="Scheme type",
        pattern='^(CORSIA|EU ETS|UK ETS|CH ETS|ReFuelEU)$'
    )
    airline_size: str = Field(
        description="Airline size category",
        pattern='^(small|medium|large)$'
    )

    class Config:
        extra = 'forbid'


class CSVCorrectionSchema(BaseModel):
    """Schema for CSV corrections"""
    row: int = Field(ge=0, description="Row index")
    column: str = Field(min_length=1, description="Column name")
    new_value: Any = Field(description="New value")

    class Config:
        extra = 'forbid'


class BulkCorrectionSchema(BaseModel):
    """Schema for bulk CSV corrections"""
    corrections: List[CSVCorrectionSchema] = Field(
        min_items=1,
        max_items=1000,
        description="List of corrections"
    )
    revalidate: bool = Field(
        default=True,
        description="Re-run validation after corrections"
    )

    class Config:
        extra = 'forbid'


# ============================================================================
# Validation Decorators
# ============================================================================

def validate_json(schema: BaseModel):
    """
    Decorator to validate JSON request body against Pydantic schema

    Usage:
        @app.post('/api/projects')
        @require_auth
        @validate_json(CreateProjectSchema)
        def create_project():
            validated_data = g.validated_data
            return {'project': validated_data}

    Args:
        schema: Pydantic model class for validation
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                # Get JSON data from request
                if not request.is_json:
                    return jsonify({
                        'error': 'Content-Type must be application/json'
                    }), 400

                data = request.get_json()

                if data is None:
                    return jsonify({
                        'error': 'Invalid or empty JSON body'
                    }), 400

                # Validate with Pydantic
                validated = schema(**data)

                # Store validated data in Flask g object
                from flask import g
                g.validated_data = validated.dict()

                # Execute the route
                return f(*args, **kwargs)

            except json.JSONDecodeError as e:
                return jsonify({
                    'error': 'Invalid JSON',
                    'details': str(e)
                }), 400

            except Exception as e:
                # Pydantic validation error
                if hasattr(e, 'errors'):
                    # Pydantic V2 format
                    errors = e.errors()
                    return jsonify({
                        'error': 'Validation failed',
                        'details': errors
                    }), 400
                else:
                    return jsonify({
                        'error': 'Validation failed',
                        'details': str(e)
                    }), 400

        return wrapper
    return decorator


def validate_form(schema: BaseModel):
    """
    Decorator to validate form data against Pydantic schema

    Usage:
        @app.post('/api/upload')
        @require_auth
        @validate_form(CSVUploadSchema)
        def upload_csv():
            validated_data = g.validated_data
            return {'upload': validated_data}
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                # Get form data
                data = request.form.to_dict()

                # Handle JSON fields in form data
                for key, value in data.items():
                    if value.startswith('[') or value.startswith('{'):
                        try:
                            data[key] = json.loads(value)
                        except:
                            pass

                # Validate with Pydantic
                validated = schema(**data)

                # Store validated data in Flask g object
                from flask import g
                g.validated_data = validated.dict()

                return f(*args, **kwargs)

            except Exception as e:
                if hasattr(e, 'errors'):
                    errors = e.errors()
                    return jsonify({
                        'error': 'Validation failed',
                        'details': errors
                    }), 400
                else:
                    return jsonify({
                        'error': 'Validation failed',
                        'details': str(e)
                    }), 400

        return wrapper
    return decorator


def validate_monitoring_plan_file(
    field_name: str = 'file',
    max_size_mb: int = 50
):
    """
    Decorator to validate monitoring plan file uploads
    Accepts: PDF, Excel, CSV, and image formats

    Usage:
        @app.post('/api/upload-monitoring-plan')
        @validate_monitoring_plan_file('file', max_size_mb=50)
        def upload():
            file = g.validated_file
            return {'filename': file.filename}

    Args:
        field_name: Name of the file field in request
        max_size_mb: Maximum file size in MB
    """
    allowed_extensions = ['pdf', 'xlsx', 'xls', 'csv', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp']
    return validate_file(field_name, allowed_extensions, max_size_mb)


def validate_file(
    field_name: str = 'file',
    allowed_extensions: Optional[List[str]] = None,
    max_size_mb: int = 10
):
    """
    Decorator to validate file uploads

    Usage:
        @app.post('/api/upload')
        @validate_file('file', ['csv'], max_size_mb=50)
        def upload():
            file = g.validated_file
            return {'filename': file.filename}

    Args:
        field_name: Name of the file field in request
        allowed_extensions: List of allowed file extensions (without dot)
        max_size_mb: Maximum file size in MB
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Check if file is in request
            if field_name not in request.files:
                return jsonify({
                    'error': f'No file provided in field: {field_name}'
                }), 400

            file = request.files[field_name]

            # Check if filename is empty
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400

            # Check file extension
            if allowed_extensions:
                ext = file.filename.rsplit('.', 1)[-1].lower()
                if ext not in allowed_extensions:
                    return jsonify({
                        'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'
                    }), 400

            # Check file size (read first chunk to get size estimate)
            file.seek(0, 2)  # Seek to end
            size = file.tell()
            file.seek(0)  # Reset to beginning

            max_size_bytes = max_size_mb * 1024 * 1024
            if size > max_size_bytes:
                return jsonify({
                    'error': f'File too large. Maximum: {max_size_mb}MB'
                }), 400

            # Store file in Flask g object
            from flask import g
            g.validated_file = file

            return f(*args, **kwargs)

        return wrapper
    return decorator


# ============================================================================
# Utility Functions
# ============================================================================

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    import re
    from werkzeug.utils import secure_filename

    # Use werkzeug's secure_filename as base
    safe_name = secure_filename(filename)

    # Additional sanitization: remove any remaining special chars
    safe_name = re.sub(r'[^\w\s.-]', '', safe_name)

    # Limit length
    if len(safe_name) > 200:
        name, ext = safe_name.rsplit('.', 1) if '.' in safe_name else (safe_name, '')
        safe_name = name[:200 - len(ext) - 1] + '.' + ext if ext else name[:200]

    return safe_name


def validate_project_id(project_id: str) -> bool:
    """
    Validate project ID format (UUID)

    Args:
        project_id: Project ID to validate

    Returns:
        True if valid UUID format
    """
    import re
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(project_id))
