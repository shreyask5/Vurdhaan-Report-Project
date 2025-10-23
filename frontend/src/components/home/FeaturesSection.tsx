import { Zap, Users, Shield, BarChart, Clock, Sparkles } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import feature1 from '@/assets/feature-1.jpg';
import feature2 from '@/assets/feature-2.jpg';
import feature3 from '@/assets/feature-3.jpg';

const features = [
  {
    icon: Zap,
    title: 'Multi-Scheme Support',
    description: 'CORSIA, EU ETS, UK ETS, CH ETS, and ReFuelEU reporting in one platform.',
  },
  {
    icon: Users,
    title: 'Team Collaboration',
    description: 'Real-time collaboration with AI assistance for complex compliance queries.',
  },
  {
    icon: Shield,
    title: 'Data Validation',
    description: 'Automated validation ensures compliance with scheme requirements.',
  },
  {
    icon: BarChart,
    title: 'Monitoring Plans',
    description: 'Comprehensive monitoring plan creation and review workflow.',
  },
  {
    icon: Clock,
    title: 'Document Management',
    description: 'Centralized document upload, storage, and version control.',
  },
  {
    icon: Sparkles,
    title: 'AI-Powered Insights',
    description: 'Intelligent analysis of emissions data and compliance requirements.',
  },
];

const detailedFeatures = [
  {
    image: feature1,
    title: 'Comprehensive Scheme Coverage',
    description:
      'Support for all major aviation carbon schemes including CORSIA, EU ETS, UK ETS, CH ETS, and ReFuelEU. Manage multiple compliance requirements from a single platform with scheme-specific validation rules.',
    features: ['CORSIA reporting', 'EU ETS compliance', 'UK & CH ETS', 'ReFuelEU ready'],
  },
  {
    image: feature2,
    title: 'Automated Data Validation',
    description:
      'Built-in validation rules ensure your data meets scheme requirements before submission. Catch errors early with intelligent checks and receive actionable feedback on compliance gaps.',
    features: ['Real-time validation', 'Error detection', 'Data quality checks', 'Compliance scoring'],
  },
  {
    image: feature3,
    title: 'AI-Powered Collaboration',
    description:
      'Work together seamlessly with your team and get instant answers to complex compliance questions. Our AI assistant helps navigate regulations and provides guidance throughout the reporting process.',
    features: ['Real-time chat', 'AI assistance', 'Document sharing', 'Audit trails'],
  },
];

export const FeaturesSection = () => {
  return (
    <section id="features" className="py-24 bg-background">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-4 animate-fade-in-up">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold">
            Everything You Need for{' '}
            <span className="bg-gradient-primary bg-clip-text text-transparent">Carbon Compliance</span>
          </h2>
          <p className="text-lg text-muted-foreground">
            Powerful features designed to streamline your aviation emissions reporting and ensure regulatory compliance.
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
