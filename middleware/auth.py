"""
Authentication Middleware for Flask API
Uses Firebase Admin SDK to verify ID tokens
"""

import firebase_admin
from firebase_admin import auth, credentials
from flask import request, g, jsonify
from functools import wraps
import os
from typing import Optional, Dict, Any


class FirebaseAuth:
    """Firebase Authentication Handler"""

    _initialized = False

    @classmethod
    def initialize(cls, credentials_path: Optional[str] = None):
        """
        Initialize Firebase Admin SDK

        Args:
            credentials_path: Path to service account JSON file
                            If None, uses Application Default Credentials
        """
        if cls._initialized:
            return

        try:
            if credentials_path and os.path.exists(credentials_path):
                cred = credentials.Certificate(credentials_path)
                firebase_admin.initialize_app(cred)
                print(f"✅ Firebase initialized with service account: {credentials_path}")
            else:
                # Use Application Default Credentials (for production with Workload Identity)
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred)
                print("✅ Firebase initialized with Application Default Credentials")

            cls._initialized = True
        except Exception as e:
            print(f"❌ Failed to initialize Firebase: {e}")
            raise

    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """
        Verify Firebase ID token

        Args:
            token: Firebase ID token

        Returns:
            Decoded token data with uid, email, and custom claims

        Raises:
            Exception if token is invalid
        """
        return auth.verify_id_token(token, check_revoked=True)


def require_auth(f):
    """
    Decorator to require Firebase authentication on endpoints

    Usage:
        @app.get('/api/protected')
        @require_auth
        def protected_route():
            user_id = g.user['uid']
            return {'message': f'Hello {user_id}'}
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Extract Authorization header
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return jsonify({
                'error': 'Missing or invalid authorization header',
                'details': 'Expected: Authorization: Bearer <token>'
            }), 401

        # Extract token
        token = auth_header.split(' ', 1)[1].strip()

        if not token:
            return jsonify({'error': 'Empty token'}), 401

        try:
            # Verify token with Firebase
            decoded_token = FirebaseAuth.verify_token(token)

            # Store user info in Flask's g object for use in the request
            g.user = {
                'uid': decoded_token['uid'],
                'email': decoded_token.get('email'),
                'email_verified': decoded_token.get('email_verified', False),
                'claims': decoded_token,
                'custom_claims': decoded_token.get('custom_claims', {})
            }

            # Execute the protected function
            return f(*args, **kwargs)

        except auth.InvalidIdTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        except auth.ExpiredIdTokenError:
            return jsonify({'error': 'Token expired'}), 401
        except auth.RevokedIdTokenError:
            return jsonify({'error': 'Token revoked'}), 401
        except auth.CertificateFetchError:
            return jsonify({'error': 'Failed to fetch Firebase certificates'}), 503
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return jsonify({'error': 'Authentication failed', 'details': str(e)}), 401

    return wrapper


def require_claim(claim_key: str, claim_value: Any = True):
    """
    Decorator to require specific custom claim
    Must be used AFTER @require_auth

    Usage:
        @app.get('/api/admin')
        @require_auth
        @require_claim('role', 'admin')
        def admin_route():
            return {'message': 'Admin only'}

    Args:
        claim_key: Name of the custom claim
        claim_value: Expected value (default: True for boolean claims)
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not hasattr(g, 'user'):
                return jsonify({'error': 'Authentication required'}), 401

            user_claims = g.user.get('custom_claims', {})

            if user_claims.get(claim_key) != claim_value:
                return jsonify({
                    'error': 'Forbidden',
                    'details': f'Required claim: {claim_key}={claim_value}'
                }), 403

            return f(*args, **kwargs)
        return wrapper
    return decorator


def require_owner(resource_getter):
    """
    Decorator to require resource ownership
    Must be used AFTER @require_auth

    Usage:
        @app.get('/api/projects/<project_id>')
        @require_auth
        @require_owner(lambda project_id: get_project(project_id))
        def get_project_route(project_id):
            return g.resource  # Pre-fetched resource

    Args:
        resource_getter: Function that takes route params and returns resource dict
                        Resource must have 'owner_uid' field
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not hasattr(g, 'user'):
                return jsonify({'error': 'Authentication required'}), 401

            # Fetch the resource
            try:
                resource = resource_getter(**kwargs)

                if not resource:
                    return jsonify({'error': 'Resource not found'}), 404

                # Check ownership
                resource_owner = resource.get('owner_uid')
                if resource_owner != g.user['uid']:
                    # Check if user is admin (admins can access all resources)
                    if g.user.get('custom_claims', {}).get('role') != 'admin':
                        return jsonify({'error': 'Forbidden'}), 403

                # Store resource in g for use in the route
                g.resource = resource

                return f(*args, **kwargs)

            except Exception as e:
                print(f"❌ Ownership check failed: {e}")
                return jsonify({'error': 'Failed to verify ownership'}), 500

        return wrapper
    return decorator


def optional_auth(f):
    """
    Decorator for optional authentication
    Sets g.user if valid token is present, but doesn't require it

    Usage:
        @app.get('/api/public')
        @optional_auth
        def public_route():
            if hasattr(g, 'user'):
                return {'message': f'Hello {g.user["uid"]}'}
            return {'message': 'Hello anonymous'}
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')

        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1].strip()

            try:
                decoded_token = FirebaseAuth.verify_token(token)
                g.user = {
                    'uid': decoded_token['uid'],
                    'email': decoded_token.get('email'),
                    'email_verified': decoded_token.get('email_verified', False),
                    'claims': decoded_token,
                    'custom_claims': decoded_token.get('custom_claims', {})
                }
            except Exception:
                # Invalid token, but that's okay for optional auth
                pass

        return f(*args, **kwargs)

    return wrapper
