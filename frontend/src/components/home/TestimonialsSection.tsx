import { Card, CardContent } from '@/components/ui/card';
import { Star, Quote } from 'lucide-react';

const testimonials = [
  {
    name: 'Sarah Mitchell',
    role: 'Head of Sustainability',
    company: 'Global Airways',
    content:
      'Vurdhaan Reports simplified our CORSIA compliance process dramatically. The automated validation caught errors we would have missed, saving us from costly resubmissions.',
    rating: 5,
  },
  {
    name: 'James Thompson',
    role: 'Environmental Compliance Manager',
    company: 'European Air Cargo',
    content:
      'Managing EU ETS and UK ETS reporting simultaneously was a nightmare until we found this platform. The multi-scheme support is exactly what we needed.',
    rating: 5,
  },
  {
    name: 'Maria Rodriguez',
    role: 'Carbon Reporting Lead',
    company: 'Atlantic Aviation',
    content:
      'The AI assistant is incredibly helpful for navigating complex regulations. Our team can get instant answers without waiting for external consultants.',
    rating: 5,
  },
  {
    name: 'David Chen',
    role: 'Director of Operations',
    company: 'Intercontinental Airlines',
    content:
      'Vurdhaan Reports reduced our reporting time by 60%. The monitoring plan workflow is intuitive and the validation features give us confidence in our submissions.',
    rating: 5,
  },
  {
    name: 'Emma Williams',
    role: 'Sustainability Director',
    company: 'Regional Express',
    content:
      'Outstanding platform for carbon compliance. The team collaboration features and document management have streamlined our entire reporting process across multiple schemes.',
    rating: 5,
  },
];

// Mock company logos
const companies = [
  'Global Airways',
  'Air Cargo International',
  'Atlantic Aviation',
  'Regional Express',
  'Continental Airlines',
  'Pacific Flights',
];

export const TestimonialsSection = () => {
  return (
    <section className="py-24 bg-background">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        {/* Company Logos */}
        <div className="mb-16">
          <p className="text-center text-sm text-muted-foreground mb-8">
            Trusted by airlines and aviation companies worldwide
          </p>
          <div className="flex flex-wrap justify-center items-center gap-8 md:gap-12 opacity-60">
            {companies.map((company, index) => (
              <div
                key={index}
                className="text-xl font-bold text-muted-foreground hover:text-foreground transition-colors"
              >
                {company}
              </div>
            ))}
          </div>
        </div>

        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold">
            Trusted by{' '}
            <span className="bg-gradient-primary bg-clip-text text-transparent">
              Aviation Leaders
            </span>
          </h2>
          <p className="text-lg text-muted-foreground">
            See what compliance teams have to say about their experience with Vurdhaan Reports.
          </p>
        </div>

        {/* Testimonials Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {testimonials.map((testimonial, index) => (
            <Card
              key={index}
              className="hover:shadow-lg transition-all duration-300 animate-fade-in"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <CardContent className="p-6 space-y-4">
                <Quote className="h-8 w-8 text-primary/20" />
                
                {/* Rating */}
                <div className="flex space-x-1">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <Star key={i} className="h-4 w-4 fill-warning text-warning" />
                  ))}
                </div>

                {/* Content */}
                <p className="text-muted-foreground leading-relaxed">{testimonial.content}</p>

                {/* Author */}
                <div className="pt-4 border-t border-border">
                  <p className="font-semibold">{testimonial.name}</p>
                  <p className="text-sm text-muted-foreground">{testimonial.role}</p>
                  <p className="text-sm text-primary">{testimonial.company}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};
