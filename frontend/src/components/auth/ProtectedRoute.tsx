import { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { authApi } from '@/services/api';
import { Loader2 } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

/**
 * ProtectedRoute wrapper component
 * Handles authentication flow:
 * 1. Check if user is authenticated
 * 2. Check if email is verified
 * 3. Check if profile is completed
 * 4. Redirect to appropriate page if any check fails
 */
export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, firebaseUser, isLoading: authLoading } = useAuth();
  const location = useLocation();
  const [profileLoading, setProfileLoading] = useState(true);
  const [profileCompleted, setProfileCompleted] = useState(false);

  useEffect(() => {
    const checkProfile = async () => {
      if (!firebaseUser || !user) {
        setProfileLoading(false);
        return;
      }

      // Skip profile check if on verification or welcome pages
      if (location.pathname === '/verification' || location.pathname === '/welcome') {
        setProfileLoading(false);
        return;
      }

      try {
        const profile = await authApi.getProfile();
        setProfileCompleted(profile.profile_completed === true);
      } catch (error) {
        console.error('Error checking profile:', error);
        // If backend error, assume profile not completed
        setProfileCompleted(false);
      } finally {
        setProfileLoading(false);
      }
    };

    if (!authLoading) {
      checkProfile();
    }
  }, [firebaseUser, user, authLoading, location.pathname]);

  // Show loading spinner while checking auth and profile
  if (authLoading || profileLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // Redirect to home if not authenticated
  if (!user || !firebaseUser) {
    return <Navigate to="/" state={{ from: location }} replace />;
  }

  // Redirect to verification if email not verified
  // (except if already on verification page)
  if (!firebaseUser.emailVerified && location.pathname !== '/verification') {
    return <Navigate to="/verification" replace />;
  }

  // Redirect to welcome if profile not completed
  // (except if already on welcome or verification page)
  if (
    !profileCompleted &&
    location.pathname !== '/welcome' &&
    location.pathname !== '/verification'
  ) {
    return <Navigate to="/welcome" replace />;
  }

  // All checks passed, render children
  return <>{children}</>;
}
