import { Button } from '@/components/ui/button';
import { Calendar, ArrowRight } from 'lucide-react';

// FRONTEND ONLY: Replace with your actual Calendly URL
const CALENDLY_URL = 'https://calendly.com/your-handle/demo';

export const DemoSection = () => {
  return (
    <section id="demo" className="py-24 bg-gradient-hero">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-card rounded-3xl shadow-xl p-8 md:p-12 text-center space-y-8 border border-border/50">
            <div className="inline-block p-4 rounded-full bg-gradient-primary">
              <Calendar className="h-8 w-8 text-white" />
            </div>

            <div className="space-y-4">
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold">
                See Vurdhaan Reports in Action
              </h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Book a personalized demo with our compliance experts. We'll show you how Vurdhaan Reports
                can streamline your carbon reporting and answer all your questions about CORSIA, EU ETS, and other schemes.
              </p>
            </div>

            <div className="grid sm:grid-cols-3 gap-6 py-8">
              <div className="space-y-2">
                <div className="text-2xl font-bold text-primary">30 min</div>
                <div className="text-sm text-muted-foreground">Personalized demo</div>
              </div>
              <div className="space-y-2">
                <div className="text-2xl font-bold text-primary">No commitment</div>
                <div className="text-sm text-muted-foreground">Free consultation</div>
              </div>
              <div className="space-y-2">
                <div className="text-2xl font-bold text-primary">Get answers</div>
                <div className="text-sm text-muted-foreground">Ask anything</div>
              </div>
            </div>

            <a
              href={CALENDLY_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block"
            >
              <Button
                size="lg"
                className="bg-gradient-primary hover:opacity-90 transition-all shadow-glow group"
              >
                Schedule Your Demo
                <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Button>
            </a>

            <p className="text-sm text-muted-foreground">
              Available Monday-Friday, 9 AM - 6 PM EST
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};
