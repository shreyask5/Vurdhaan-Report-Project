import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Mail, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

export default function EmailVerification() {
  const { user, firebaseUser, logout } = useAuth();
  const navigate = useNavigate();
  const [isChecking, setIsChecking] = useState(false);
  const [canResend, setCanResend] = useState(true);
  const [resendCooldown, setResendCooldown] = useState(0);
  const [autoCheckInterval, setAutoCheckInterval] = useState<NodeJS.Timeout | null>(null);

  // Check if email is already verified on mount
  useEffect(() => {
    if (!firebaseUser) {
      navigate('/');
      return;
    }

    // If already verified, redirect to welcome page
    if (firebaseUser.emailVerified) {
      navigate('/welcome');
      return;
    }

    // Auto-check verification status every 5 seconds
    const interval = setInterval(() => {
      checkVerificationStatus();
    }, 5000);

    setAutoCheckInterval(interval);

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [firebaseUser, navigate]);

  // Cooldown timer
  useEffect(() => {
    if (resendCooldown > 0) {
      const timer = setTimeout(() => {
        setResendCooldown(resendCooldown - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else if (resendCooldown === 0 && !canResend) {
      setCanResend(true);
    }
  }, [resendCooldown, canResend]);

  const checkVerificationStatus = async () => {
    if (!firebaseUser || isChecking) return;

    setIsChecking(true);
    try {
      await firebaseUser.reload();
      if (firebaseUser.emailVerified) {
        if (autoCheckInterval) {
          clearInterval(autoCheckInterval);
        }
        toast.success('Email verified successfully!');
        navigate('/welcome');
      }
    } catch (error) {
      console.error('Error checking verification status:', error);
    } finally {
      setIsChecking(false);
    }
  };

  const handleResendVerification = async () => {
    if (!firebaseUser || !canResend) return;

    try {
      const { sendEmailVerification } = await import('firebase/auth');
      await sendEmailVerification(firebaseUser);

      toast.success('Verification email sent!', {
        description: 'Please check your inbox and spam folder.',
      });

      // Set cooldown for 60 seconds
      setCanResend(false);
      setResendCooldown(60);
    } catch (error: any) {
      console.error('Error sending verification email:', error);

      if (error.code === 'auth/too-many-requests') {
        toast.error('Too many requests', {
          description: 'Please wait a few minutes before trying again.',
        });
      } else {
        toast.error('Failed to send verification email', {
          description: error.message || 'Please try again later.',
        });
      }
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  if (!firebaseUser) {
    return null;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/5 via-background to-secondary/5 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center space-y-4">
          <div className="mx-auto w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
            <Mail className="h-8 w-8 text-primary" />
          </div>
          <CardTitle className="text-2xl">Verify Your Email</CardTitle>
          <CardDescription className="text-base">
            We've sent a verification email to:
            <div className="font-semibold text-foreground mt-2 break-all">
              {firebaseUser.email}
            </div>
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Instructions */}
          <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 space-y-2">
            <div className="flex items-start space-x-2">
              <CheckCircle2 className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-blue-900 dark:text-blue-100">
                Click the verification link in the email
              </p>
            </div>
            <div className="flex items-start space-x-2">
              <CheckCircle2 className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-blue-900 dark:text-blue-100">
                Return to this page (it will auto-update)
              </p>
            </div>
            <div className="flex items-start space-x-2">
              <AlertCircle className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-blue-900 dark:text-blue-100">
                Check your spam folder if you don't see the email
              </p>
            </div>
          </div>

          {/* Auto-checking indicator */}
          {isChecking && (
            <div className="flex items-center justify-center space-x-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Checking verification status...</span>
            </div>
          )}

          {/* Resend button */}
          <div className="space-y-2">
            <Button
              onClick={handleResendVerification}
              disabled={!canResend}
              variant="outline"
              className="w-full"
            >
              {!canResend && resendCooldown > 0 ? (
                `Resend available in ${resendCooldown}s`
              ) : (
                'Resend Verification Email'
              )}
            </Button>

            <Button
              onClick={checkVerificationStatus}
              disabled={isChecking}
              className="w-full"
            >
              {isChecking ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Checking...
                </>
              ) : (
                'I\'ve Verified My Email'
              )}
            </Button>
          </div>

          {/* Logout option */}
          <div className="pt-4 border-t">
            <Button
              onClick={handleLogout}
              variant="ghost"
              className="w-full text-muted-foreground"
            >
              Logout
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
