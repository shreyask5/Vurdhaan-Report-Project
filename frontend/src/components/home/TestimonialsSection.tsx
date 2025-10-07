import { Card, CardContent } from '@/components/ui/card';
import { Star, Quote } from 'lucide-react';

const testimonials = [
  {
    name: 'Sarah Johnson',
    role: 'CEO at TechCorp',
    company: 'TechCorp Inc.',
    content:
      'ServicePro transformed how our team collaborates. The automation features alone saved us 20 hours per week. Absolutely game-changing.',
    rating: 5,
  },
  {
    name: 'Michael Chen',
    role: 'Operations Director',
    company: 'GrowthLabs',
    content:
      'The analytics dashboard gives us insights we never had before. We can now make data-driven decisions in real-time. Highly recommended!',
    rating: 5,
  },
  {
    name: 'Emily Rodriguez',
    role: 'Product Manager',
    company: 'InnovateCo',
    content:
      'Implementation was seamless, and the support team is exceptional. Our productivity increased by 40% within the first month.',
    rating: 5,
  },
  {
    name: 'David Park',
    role: 'CTO',
    company: 'ScaleUp Systems',
    content:
      'Best investment we made this year. The platform scales effortlessly with our growing team, and the security features give us complete peace of mind.',
    rating: 5,
  },
  {
    name: 'Lisa Anderson',
    role: 'VP of Customer Success',
    company: 'CustomerFirst',
    content:
      'Our customer satisfaction scores improved dramatically after implementing ServicePro. The real-time collaboration features are unmatched.',
    rating: 5,
  },
];

// Mock company logos
const companies = [
  'TechCorp',
  'GrowthLabs',
  'InnovateCo',
  'ScaleUp',
  'CustomerFirst',
  'DataFlow',
];

export const TestimonialsSection = () => {
  return (
    <section className="py-24 bg-background">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        {/* Company Logos */}
        <div className="mb-16">
          <p className="text-center text-sm text-muted-foreground mb-8">
            Trusted by thousands of companies worldwide
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
            Loved by{' '}
            <span className="bg-gradient-primary bg-clip-text text-transparent">
              Teams Everywhere
            </span>
          </h2>
          <p className="text-lg text-muted-foreground">
            See what our customers have to say about their experience with ServicePro.
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
