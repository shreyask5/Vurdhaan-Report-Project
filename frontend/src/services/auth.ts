// Auth Service - Firebase Token Management
// Provides authentication token for API requests

import { auth } from './firebase';

/**
 * Get Firebase authentication token for API requests
 * @returns Promise<string> Firebase ID token
 * @throws Error if user is not authenticated
 */
export async function getAuthToken(): Promise<string> {
  const user = auth.currentUser;

  if (!user) {
    throw new Error('User not authenticated. Please sign in to continue.');
  }

  try {
    // Get fresh ID token (force refresh if expired)
    const token = await user.getIdToken(true);
    return token;
  } catch (error) {
    console.error('Failed to get authentication token:', error);
    throw new Error('Failed to retrieve authentication token. Please try signing in again.');
  }
}

/**
 * Get current user ID
 * @returns string | null User ID if authenticated, null otherwise
 */
export function getCurrentUserId(): string | null {
  return auth.currentUser?.uid || null;
}

/**
 * Get current user email
 * @returns string | null User email if authenticated, null otherwise
 */
export function getCurrentUserEmail(): string | null {
  return auth.currentUser?.email || null;
}

/**
 * Check if user is authenticated
 * @returns boolean True if user is authenticated
 */
export function isAuthenticated(): boolean {
  return auth.currentUser !== null;
}
