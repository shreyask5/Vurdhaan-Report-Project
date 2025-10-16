// Firebase Authentication Context
import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  sendEmailVerification,
  User as FirebaseUser,
} from 'firebase/auth';
import { auth } from '../services/firebase';
import { authApi } from '../services/api';
import { isBusinessEmail, getBusinessEmailError } from '../utils/emailValidation';

type UserRole = 'user' | 'admin' | null;

interface AuthUser {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  emailVerified: boolean;
}

interface AuthContextType {
  user: AuthUser | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  resendVerificationEmail: () => Promise<void>;
  checkEmailVerified: () => Promise<boolean>;
  isAuthenticated: boolean;
  isAdmin: boolean;
  firebaseUser: FirebaseUser | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Listen to Firebase auth state changes
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        // User is signed in
        try {
          // Verify with backend and get user data
          const { user: backendUser } = await authApi.verify();

          setFirebaseUser(firebaseUser);
          setUser({
            id: firebaseUser.uid,
            email: firebaseUser.email || '',
            name: firebaseUser.displayName || backendUser.name || firebaseUser.email?.split('@')[0] || 'User',
            role: 'user',
            emailVerified: firebaseUser.emailVerified,
          });
        } catch (error) {
          console.error('Failed to verify with backend:', error);
          // Still set user from Firebase data
          setFirebaseUser(firebaseUser);
          setUser({
            id: firebaseUser.uid,
            email: firebaseUser.email || '',
            name: firebaseUser.displayName || firebaseUser.email?.split('@')[0] || 'User',
            role: 'user',
            emailVerified: firebaseUser.emailVerified,
          });
        }
      } else {
        // User is signed out
        setFirebaseUser(null);
        setUser(null);
      }
      setIsLoading(false);
    });

    // Cleanup subscription on unmount
    return () => unsubscribe();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      // User state will be updated by onAuthStateChanged listener
      console.log('Login successful:', userCredential.user.email);
    } catch (error: any) {
      console.error('Login error:', error);

      // Provide user-friendly error messages based on Firebase error codes
      if (error.code === 'auth/user-not-found') {
        throw new Error('No account found with this email. Did you mean to sign up?');
      } else if (error.code === 'auth/wrong-password') {
        throw new Error('Incorrect password. Please try again.');
      } else if (error.code === 'auth/invalid-email') {
        throw new Error('Invalid email address format.');
      } else if (error.code === 'auth/user-disabled') {
        throw new Error('This account has been disabled. Please contact support.');
      } else if (error.code === 'auth/invalid-credential') {
        throw new Error('Invalid email or password. Please check your credentials.');
      } else if (error.code === 'auth/too-many-requests') {
        throw new Error('Too many failed login attempts. Please try again later.');
      }

      throw new Error(error.message || 'Failed to login');
    }
  };

  const signup = async (name: string, email: string, password: string) => {
    try {
      // Validate business email before signup
      if (!isBusinessEmail(email)) {
        throw new Error(getBusinessEmailError(email));
      }

      const userCredential = await createUserWithEmailAndPassword(auth, email, password);

      // Update display name
      // Note: updateProfile is async but we don't await it to avoid delays
      import('firebase/auth').then(({ updateProfile }) => {
        updateProfile(userCredential.user, { displayName: name });
      });

      // Send email verification
      await sendEmailVerification(userCredential.user);

      // Verify with backend to create user record
      await authApi.verify();

      console.log('Signup successful:', userCredential.user.email);
    } catch (error: any) {
      console.error('Signup error:', error);

      // Provide user-friendly error messages for signup
      if (error.code === 'auth/email-already-in-use') {
        throw new Error('An account with this email already exists. Did you mean to login?');
      } else if (error.code === 'auth/invalid-email') {
        throw new Error('Invalid email address format.');
      } else if (error.code === 'auth/weak-password') {
        throw new Error('Password is too weak. Please use a stronger password.');
      } else if (error.code === 'auth/operation-not-allowed') {
        throw new Error('Email/password accounts are not enabled. Please contact support.');
      }

      throw new Error(error.message || 'Failed to create account');
    }
  };

  const resendVerificationEmail = async () => {
    const currentUser = auth.currentUser;
    if (!currentUser) {
      throw new Error('No user logged in');
    }

    try {
      await sendEmailVerification(currentUser);
      console.log('Verification email sent');
    } catch (error: any) {
      console.error('Resend verification error:', error);

      if (error.code === 'auth/too-many-requests') {
        throw new Error('Too many requests. Please wait a few minutes before trying again.');
      }

      throw new Error(error.message || 'Failed to send verification email');
    }
  };

  const checkEmailVerified = async (): Promise<boolean> => {
    const currentUser = auth.currentUser;
    if (!currentUser) {
      return false;
    }

    try {
      await currentUser.reload();
      return currentUser.emailVerified;
    } catch (error) {
      console.error('Error checking email verification:', error);
      return false;
    }
  };

  const logout = async () => {
    try {
      await signOut(auth);
      setUser(null);
      setFirebaseUser(null);
    } catch (error) {
      console.error('Logout error:', error);
      throw error;
    }
  };

  const value = {
    user,
    firebaseUser,
    isLoading,
    login,
    signup,
    logout,
    resendVerificationEmail,
    checkEmailVerified,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin',
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
