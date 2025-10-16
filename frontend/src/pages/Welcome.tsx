import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Loader2, Building2, Plane } from 'lucide-react';
import { toast } from 'sonner';
import { authApi } from '@/services/api';
import type { AirlineSize } from '@/types/validation';

const AIRLINE_SIZES: { value: AirlineSize; label: string; range: string; description: string }[] = [
  {
    value: 'small',
    label: 'Small Operator',
    range: '1-30',
    description: 'Small operators with 1-30 aircraft'
  },
  {
    value: 'medium',
    label: 'Medium Operator',
    range: '30-80',
    description: 'Medium operators with 30-80 aircraft'
  },
  {
    value: 'large',
    label: 'Large Operator',
    range: '80+',
    description: 'Large operators with 80 or more aircraft'
  }
];

export default function Welcome() {
  const { user, firebaseUser } = useAuth();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  const [formData, setFormData] = useState({
    designation: '',
    airlineName: '',
    airlineSize: '' as AirlineSize | ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.designation.trim()) {
      toast.error('Please enter your designation');
      return;
    }

    if (!formData.airlineName.trim()) {
      toast.error('Please enter your airline name');
      return;
    }

    if (!formData.airlineSize) {
      toast.error('Please select your airline size');
      return;
    }

    setIsLoading(true);

    try {
      await authApi.updateProfile({
        designation: formData.designation.trim(),
        airline_name: formData.airlineName.trim(),
        airline_size: formData.airlineSize,
        profile_completed: true
      });

      toast.success('Welcome to Vurdhaan!', {
        description: 'Your profile has been set up successfully.',
      });

      navigate('/dashboard');
    } catch (error: any) {
      console.error('Error saving profile:', error);
      toast.error('Failed to save profile', {
        description: error.message || 'Please try again.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Redirect if not authenticated or email not verified
  if (!firebaseUser) {
    navigate('/');
    return null;
  }

  if (!firebaseUser.emailVerified) {
    navigate('/verification');
    return null;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/5 via-background to-secondary/5 p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader className="text-center space-y-4">
          <div className="mx-auto w-16 h-16 rounded-full bg-gradient-primary flex items-center justify-center">
            <Plane className="h-8 w-8 text-white" />
          </div>
          <CardTitle className="text-3xl">Welcome to Vurdhaan!</CardTitle>
          <CardDescription className="text-base">
            Let's set up your profile to get started
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Designation */}
            <div className="space-y-2">
              <Label htmlFor="designation">
                Designation / Job Title <span className="text-destructive">*</span>
              </Label>
              <Input
                id="designation"
                type="text"
                placeholder="e.g., Environmental Manager, Compliance Officer"
                value={formData.designation}
                onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
                required
              />
            </div>

            {/* Airline Name */}
            <div className="space-y-2">
              <Label htmlFor="airlineName">
                Airline / Company Name <span className="text-destructive">*</span>
              </Label>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="airlineName"
                  type="text"
                  placeholder="e.g., Acme Airlines"
                  className="pl-10"
                  value={formData.airlineName}
                  onChange={(e) => setFormData({ ...formData, airlineName: e.target.value })}
                  required
                />
              </div>
            </div>

            {/* Airline Size */}
            <div className="space-y-3">
              <Label>
                Airline Size <span className="text-destructive">*</span>
              </Label>
              <p className="text-sm text-muted-foreground">
                Choose the category that best describes your airline's fleet size
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {AIRLINE_SIZES.map((size) => (
                  <button
                    key={size.value}
                    type="button"
                    onClick={() => setFormData({ ...formData, airlineSize: size.value })}
                    className={`p-6 rounded-lg border-2 text-center transition-all ${\
                      formData.airlineSize === size.value
                        ? 'border-primary bg-primary bg-opacity-10 shadow-md'
                        : 'border-gray-200 hover:border-primary hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800'
                    }`}
                  >
                    <div className="text-3xl font-bold text-primary mb-2">{size.range}</div>
                    <div className="font-semibold text-base text-gray-800 dark:text-gray-200 mb-1">
                      {size.label}
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">
                      {size.description}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Submit Button */}
            <div className="pt-4">
              <Button
                type="submit"
                className="w-full bg-gradient-primary hover:opacity-90"
                disabled={isLoading}
                size="lg"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Setting up your profile...
                  </>
                ) : (
                  'Continue to Dashboard'
                )}
              </Button>
            </div>

            {/* Info note */}
            <p className="text-xs text-center text-muted-foreground">
              You can update these details later from your profile settings
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
