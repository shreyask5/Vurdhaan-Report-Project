import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle2, XCircle, Loader2, Mail } from 'lucide-react';
import { toast } from 'sonner';

type VerificationStatus = 'loading' | 'success' | 'error' | 'invalid';

export default function EmailVerificationHandler() {
  const { verifyEmailLink, firebaseUser } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState<VerificationStatus>('loading');
  const [errorMessage, setErrorMessage] = useState('');
  const [countdown, setCountdown] = useState(5);

  useEffect(() => {
    const mode = searchParams.get('mode');
    const oobCode = searchParams.get('oobCode');

    // Validate that we have the correct parameters
    if (mode !== 'verifyEmail' || !oobCode) {
      console.error('Invalid verification link parameters:', { mode, oobCode });
      setStatus('invalid');
      setErrorMessage('Invalid verification link. Please check your email for the correct link.');

      // Redirect to home after 3 seconds
      setTimeout(() => {
        navigate('/');
      }, 3000);
      return;
    }

    // Process the verification
    handleVerification(oobCode);
  }, [searchParams]);

  // Countdown timer for successful verification
  useEffect(() => {
    if (status === 'success' && countdown > 0) {
      const timer = setTimeout(() => {
        setCountdown(countdown - 1);
      }, 1000);

      return () => clearTimeout(timer);
    } else if (status === 'success' && countdown === 0) {
      // Redirect to dashboard
      navigate('/dashboard');
    }
  }, [status, countdown, navigate]);

  const handleVerification = async (oobCode: string) => {
    try {
      console.log('[EMAIL VERIFICATION] Starting verification process...');

      // Verify the email using the action code
      const result = await verifyEmailLink(oobCode);

      if (result.success) {
        console.log('[EMAIL VERIFICATION] Success:', result.message);
        setStatus('success');
        toast.success('Email verified successfully!', {
          description: 'Redirecting to your dashboard...',
        });

        // Start countdown
        setCountdown(5);
      } else {
        console.error('[EMAIL VERIFICATION] Failed:', result.message);
        setStatus('error');
        setErrorMessage(result.message);

        // Show appropriate toast based on error
        if (result.error === 'auth/expired-action-code') {
          toast.error('Verification link expired', {
            description: 'Please request a new verification email.',
          });

          // Redirect to verification page after 3 seconds
          setTimeout(() => {
            navigate('/verification');
          }, 3000);
        } else if (result.error === 'auth/invalid-action-code') {
          toast.error('Invalid verification link', {
            description: 'This link may have already been used.',
          });

          // Check if user is already verified
          if (firebaseUser?.emailVerified) {
            setTimeout(() => {
              navigate('/dashboard');
            }, 2000);
          } else {
            setTimeout(() => {
              navigate('/');
            }, 3000);
          }
        } else {
          toast.error('Verification failed', {
            description: result.message,
          });

          setTimeout(() => {
            navigate('/');
          }, 3000);
        }
      }
    } catch (error: any) {
      console.error('[EMAIL VERIFICATION] Unexpected error:', error);
      setStatus('error');
      setErrorMessage(error.message || 'An unexpected error occurred');

      toast.error('Verification failed', {
        description: 'Please try again or contact support.',
      });

      setTimeout(() => {
        navigate('/');
      }, 3000);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/5 via-background to-secondary/5 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center space-y-4">
          {/* Loading State */}
          {status === 'loading' && (
            <>
              <div className="mx-auto w-16 h-16 rounded-full bg-blue-100 dark:bg-blue-950 flex items-center justify-center">
                <Loader2 className="h-8 w-8 text-blue-600 dark:text-blue-400 animate-spin" />
              </div>
              <CardTitle className="text-2xl">Verifying Your Email</CardTitle>
              <CardDescription className="text-base">
                Please wait while we verify your email address...
              </CardDescription>
            </>
          )}

          {/* Success State */}
          {status === 'success' && (
            <>
              <div className="mx-auto w-16 h-16 rounded-full bg-green-100 dark:bg-green-950 flex items-center justify-center">
                <CheckCircle2 className="h-8 w-8 text-green-600 dark:text-green-400" />
              </div>
              <CardTitle className="text-2xl text-green-600 dark:text-green-400">
                Email Verified!
              </CardTitle>
              <CardDescription className="text-base">
                Your email has been successfully verified.
              </CardDescription>
            </>
          )}

          {/* Error State */}
          {(status === 'error' || status === 'invalid') && (
            <>
              <div className="mx-auto w-16 h-16 rounded-full bg-red-100 dark:bg-red-950 flex items-center justify-center">
                <XCircle className="h-8 w-8 text-red-600 dark:text-red-400" />
              </div>
              <CardTitle className="text-2xl text-red-600 dark:text-red-400">
                Verification Failed
              </CardTitle>
              <CardDescription className="text-base text-red-600 dark:text-red-400">
                {errorMessage}
              </CardDescription>
            </>
          )}
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Success Message with Countdown */}
          {status === 'success' && (
            <div className="bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 rounded-lg p-6">
              <div className="text-center space-y-4">
                <p className="text-sm text-green-900 dark:text-green-100">
                  Welcome to Vurdhaan! Your account is now active.
                </p>

                <div className="flex flex-col items-center space-y-2">
                  <p className="text-xs text-green-700 dark:text-green-300">
                    Redirecting to dashboard in
                  </p>
                  <div className="text-4xl font-bold text-green-600 dark:text-green-400 tabular-nums">
                    {countdown}
                  </div>
                  <p className="text-xs text-green-700 dark:text-green-300">
                    {countdown === 1 ? 'second' : 'seconds'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Error Messages */}
          {status === 'error' && (
            <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <Mail className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" />
                <div className="space-y-1">
                  <p className="text-sm font-medium text-red-900 dark:text-red-100">
                    What went wrong?
                  </p>
                  <p className="text-sm text-red-700 dark:text-red-300">
                    {errorMessage}
                  </p>
                  <p className="text-xs text-red-600 dark:text-red-400 mt-2">
                    Redirecting you shortly...
                  </p>
                </div>
              </div>
            </div>
          )}

          {status === 'invalid' && (
            <div className="bg-yellow-50 dark:bg-yellow-950/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
              <div className="text-center space-y-2">
                <p className="text-sm text-yellow-900 dark:text-yellow-100">
                  The verification link appears to be invalid or incomplete.
                </p>
                <p className="text-xs text-yellow-700 dark:text-yellow-300">
                  Please check your email and click the verification link again.
                </p>
              </div>
            </div>
          )}

          {/* Loading Info */}
          {status === 'loading' && (
            <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <p className="text-sm text-blue-900 dark:text-blue-100 text-center">
                This should only take a moment...
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
