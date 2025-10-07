import { Zap, Users, Shield, BarChart, Clock, Sparkles } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import feature1 from '@/assets/feature-1.jpg';
import feature2 from '@/assets/feature-2.jpg';
import feature3 from '@/assets/feature-3.jpg';

const features = [
  {
    icon: Zap,
    title: 'Lightning Fast',
    description: 'Automated workflows that execute in milliseconds, not hours.',
  },
  {
    icon: Users,
    title: 'Team Collaboration',
    description: 'Real-time updates and seamless communication across your team.',
  },
  {
    icon: Shield,
    title: 'Enterprise Security',
    description: 'Bank-level encryption with SOC 2 Type II compliance.',
  },
  {
    icon: BarChart,
    title: 'Advanced Analytics',
    description: 'Deep insights into performance metrics and customer behavior.',
  },
  {
    icon: Clock,
    title: '24/7 Monitoring',
    description: 'Around-the-clock system monitoring with instant alerts.',
  },
  {
    icon: Sparkles,
    title: 'AI-Powered',
    description: 'Smart automation and predictive intelligence built-in.',
  },
];

const detailedFeatures = [
  {
    image: feature1,
    title: 'Real-Time Collaboration',
    description:
      'Connect your entire team with live updates, shared workspaces, and instant messaging. See changes as they happen and collaborate without friction.',
    features: ['Live editing', 'Team chat', 'Activity feeds', '@mentions'],
  },
  {
    image: feature2,
    title: 'Automated Workflows',
    description:
      'Set up intelligent automation rules that handle repetitive tasks. From routing to notifications, let the system do the heavy lifting.',
    features: ['Smart routing', 'Auto-assignments', 'Trigger actions', 'Custom rules'],
  },
  {
    image: feature3,
    title: 'Enterprise-Grade Security',
    description:
      'Your data is protected with military-grade encryption, role-based access control, and comprehensive audit logs for complete peace of mind.',
    features: ['AES-256 encryption', 'SSO support', 'Audit trails', '2FA authentication'],
  },
];

export const FeaturesSection = () => {
  return (
    <section id="features" className="py-24 bg-background">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-4 animate-fade-in-up">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold">
            Everything You Need to{' '}
            <span className="bg-gradient-primary bg-clip-text text-transparent">Scale</span>
          </h2>
          <p className="text-lg text-muted-foreground">
            Powerful features designed to help your team work smarter, faster, and more efficiently.
          </p>
        </div>

        {/* Feature Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-8 mb-24">
          {features.map((feature, index) => (
            <Card
              key={index}
              className="group hover:shadow-lg transition-all duration-300 border-border/50 hover:border-primary/50 animate-fade-in"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <CardContent className="p-6 space-y-4">
                <div className="w-12 h-12 rounded-lg bg-gradient-primary flex items-center justify-center group-hover:scale-110 transition-transform">
                  <feature.icon className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Detailed Features */}
        <div className="space-y-32">
          {detailedFeatures.map((feature, index) => (
            <div
              key={index}
              className={`grid lg:grid-cols-2 gap-12 items-center ${
                index % 2 === 1 ? 'lg:flex-row-reverse' : ''
              }`}
            >
              <div className={`${index % 2 === 1 ? 'lg:order-2' : ''}`}>
                <img
                  src={feature.image}
                  alt={feature.title}
                  className="rounded-2xl shadow-xl w-full h-auto"
                />
              </div>
              <div className={`space-y-6 ${index % 2 === 1 ? 'lg:order-1' : ''}`}>
                <h3 className="text-3xl sm:text-4xl font-bold">{feature.title}</h3>
                <p className="text-lg text-muted-foreground">{feature.description}</p>
                <ul className="grid grid-cols-2 gap-3">
                  {feature.features.map((item, i) => (
                    <li key={i} className="flex items-center space-x-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                      <span className="text-sm font-medium">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
