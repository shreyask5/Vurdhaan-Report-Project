import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Check, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

const plans = [
  {
    name: 'Starter',
    monthlyPrice: 29,
    yearlyPrice: 290,
    description: 'Perfect for small teams getting started',
    features: [
      'Up to 5 team members',
      '10 GB storage',
      'Basic analytics',
      'Email support',
      'Core features',
      'Mobile apps',
    ],
    cta: 'Start Free Trial',
    popular: false,
  },
  {
    name: 'Pro',
    monthlyPrice: 99,
    yearlyPrice: 990,
    description: 'Best for growing businesses',
    features: [
      'Up to 25 team members',
      '100 GB storage',
      'Advanced analytics',
      'Priority support',
      'All features',
      'API access',
      'Custom integrations',
      'Advanced security',
    ],
    cta: 'Start Free Trial',
    popular: true,
  },
  {
    name: 'Business',
    monthlyPrice: 299,
    yearlyPrice: 2990,
    description: 'For large teams and enterprises',
    features: [
      'Unlimited team members',
      'Unlimited storage',
      'Custom analytics',
      '24/7 phone support',
      'Enterprise features',
      'Dedicated account manager',
      'Custom SLA',
      'SSO & advanced security',
      'Custom training',
    ],
    cta: 'Contact Sales',
    popular: false,
  },
];

export const PricingSection = () => {
  const [isYearly, setIsYearly] = useState(false);

  const handleSubscribe = (planName: string) => {
    // FRONTEND ONLY: Show a demo modal explaining this is UI only
    toast.info(`Demo Only`, {
      description: `In production, clicking "${planName}" would redirect to checkout. This is a frontend-only demo.`,
    });
  };

  return (
    <section id="pricing" className="py-24 bg-muted/30">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold">
            Simple,{' '}
            <span className="bg-gradient-primary bg-clip-text text-transparent">
              Transparent Pricing
            </span>
          </h2>
          <p className="text-lg text-muted-foreground">
            Choose the perfect plan for your team. All plans include a 14-day free trial.
          </p>
        </div>

        {/* Billing Toggle */}
        <div className="flex items-center justify-center mb-12 space-x-4">
          <span className={`text-sm font-medium ${!isYearly ? 'text-foreground' : 'text-muted-foreground'}`}>
            Monthly
          </span>
          <button
            onClick={() => setIsYearly(!isYearly)}
            className={`relative w-14 h-7 rounded-full transition-colors ${
              isYearly ? 'bg-gradient-primary' : 'bg-muted'
            }`}
          >
            <span
              className={`absolute top-1 left-1 w-5 h-5 bg-white rounded-full transition-transform ${
                isYearly ? 'translate-x-7' : 'translate-x-0'
              }`}
            />
          </button>
          <span className={`text-sm font-medium ${isYearly ? 'text-foreground' : 'text-muted-foreground'}`}>
            Yearly
          </span>
          {isYearly && (
            <span className="px-3 py-1 rounded-full bg-success/10 text-success text-xs font-semibold">
              Save 17%
            </span>
          )}
        </div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {plans.map((plan, index) => (
            <Card
              key={index}
              className={`relative ${
                plan.popular
                  ? 'border-primary shadow-xl scale-105 animate-scale-in'
                  : 'border-border/50 animate-fade-in'
              }`}
              style={{ animationDelay: `${index * 100}ms` }}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <span className="px-4 py-1 rounded-full bg-gradient-primary text-white text-xs font-semibold flex items-center space-x-1">
                    <Sparkles className="h-3 w-3" />
                    <span>Most Popular</span>
                  </span>
                </div>
              )}

              <CardHeader className="text-center pb-8 pt-8">
                <CardTitle className="text-2xl mb-2">{plan.name}</CardTitle>
                <CardDescription className="text-sm">{plan.description}</CardDescription>
                <div className="mt-4">
                  <span className="text-4xl font-bold">
                    ${isYearly ? Math.floor(plan.yearlyPrice / 12) : plan.monthlyPrice}
                  </span>
                  <span className="text-muted-foreground">/month</span>
                  {isYearly && (
                    <div className="text-sm text-muted-foreground mt-1">
                      Billed ${plan.yearlyPrice} annually
                    </div>
                  )}
                </div>
              </CardHeader>

              <CardContent className="space-y-6">
                <Button
                  className={`w-full ${
                    plan.popular
                      ? 'bg-gradient-primary hover:opacity-90'
                      : 'bg-secondary hover:opacity-90'
                  }`}
                  onClick={() => handleSubscribe(plan.name)}
                >
                  {plan.cta}
                </Button>

                <ul className="space-y-3">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex items-start space-x-3">
                      <Check className="h-5 w-5 text-success flex-shrink-0 mt-0.5" />
                      <span className="text-sm text-muted-foreground">{feature}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Trust Footer */}
        <div className="mt-16 text-center">
          <p className="text-sm text-muted-foreground mb-4">
            All plans include 14-day free trial • No credit card required • Cancel anytime
          </p>
          <p className="text-xs text-muted-foreground">
            🔒 Your data is protected with enterprise-grade security. 30-day money-back guarantee.
          </p>
        </div>
      </div>
    </section>
  );
};
