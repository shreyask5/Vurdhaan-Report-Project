/**
 * Firebase Action Code Utilities
 * Handles email verification, password reset, and other action code operations
 */

import {
  applyActionCode,
  checkActionCode,
  verifyPasswordResetCode,
  confirmPasswordReset,
  ActionCodeInfo,
} from 'firebase/auth';
import { auth } from '@/services/firebase';

export interface ActionCodeResult {
  success: boolean;
  message: string;
  error?: string;
  email?: string;
}

/**
 * Verify email using action code from verification link
 * @param oobCode - The action code from the email link
 * @returns Result object with success status and message
 */
export async function verifyEmailWithCode(oobCode: string): Promise<ActionCodeResult> {
  try {
    // First check if the code is valid
    const info: ActionCodeInfo = await checkActionCode(auth, oobCode);

    // Apply the action code to verify the email
    await applyActionCode(auth, oobCode);

    return {
      success: true,
      message: 'Email verified successfully!',
      email: info.data.email || undefined,
    };
  } catch (error: any) {
    console.error('Email verification error:', error);

    let errorMessage = 'Failed to verify email';

    // Handle specific Firebase error codes
    switch (error.code) {
      case 'auth/expired-action-code':
        errorMessage = 'Verification link has expired. Please request a new one.';
        break;
      case 'auth/invalid-action-code':
        errorMessage = 'Invalid or already used verification link.';
        break;
      case 'auth/user-disabled':
        errorMessage = 'This account has been disabled.';
        break;
      case 'auth/user-not-found':
        errorMessage = 'User account not found.';
        break;
      default:
        errorMessage = error.message || 'An error occurred during verification';
    }

    return {
      success: false,
      message: errorMessage,
      error: error.code,
    };
  }
}

/**
 * Check if an action code is valid without applying it
 * @param oobCode - The action code to check
 * @returns Action code information
 */
export async function validateActionCode(oobCode: string): Promise<ActionCodeInfo | null> {
  try {
    const info = await checkActionCode(auth, oobCode);
    return info;
  } catch (error) {
    console.error('Action code validation error:', error);
    return null;
  }
}

/**
 * Verify password reset code and get user email
 * @param oobCode - The action code from password reset link
 * @returns User email if code is valid
 */
export async function verifyPasswordReset(oobCode: string): Promise<string | null> {
  try {
    const email = await verifyPasswordResetCode(auth, oobCode);
    return email;
  } catch (error) {
    console.error('Password reset verification error:', error);
    return null;
  }
}

/**
 * Confirm password reset with new password
 * @param oobCode - The action code from password reset link
 * @param newPassword - The new password
 * @returns Success status
 */
export async function resetPassword(oobCode: string, newPassword: string): Promise<boolean> {
  try {
    await confirmPasswordReset(auth, oobCode, newPassword);
    return true;
  } catch (error) {
    console.error('Password reset error:', error);
    return false;
  }
}

/**
 * Parse action code URL parameters
 * @param url - The full URL or search params string
 * @returns Object containing mode and oobCode
 */
export function parseActionCodeURL(url: string): {
  mode: string | null;
  oobCode: string | null;
  continueUrl: string | null;
} {
  try {
    const urlObj = new URL(url);
    const params = new URLSearchParams(urlObj.search);

    return {
      mode: params.get('mode'),
      oobCode: params.get('oobCode'),
      continueUrl: params.get('continueUrl'),
    };
  } catch {
    // If URL parsing fails, try parsing as search params directly
    const params = new URLSearchParams(url.includes('?') ? url.split('?')[1] : url);

    return {
      mode: params.get('mode'),
      oobCode: params.get('oobCode'),
      continueUrl: params.get('continueUrl'),
    };
  }
}

/**
 * Get action code settings for custom email links
 * @param actionUrl - The URL to redirect to after action
 * @returns ActionCodeSettings object for Firebase
 */
export function getActionCodeSettings(actionUrl: string) {
  const currentDomain = window.location.origin;

  return {
    // URL to redirect to after email verification
    url: actionUrl || `${currentDomain}/email-verification`,
    // This must be true for custom domains
    handleCodeInApp: true,
  };
}
