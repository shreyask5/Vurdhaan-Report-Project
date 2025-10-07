import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { HeroSection } from '@/components/home/HeroSection';
import { FeaturesSection } from '@/components/home/FeaturesSection';
import { PricingSection } from '@/components/home/PricingSection';
import { TestimonialsSection } from '@/components/home/TestimonialsSection';
import { DemoSection } from '@/components/home/DemoSection';
import { FAQSection } from '@/components/home/FAQSection';

const Index = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1">
        <HeroSection />
        <FeaturesSection />
        <TestimonialsSection />
        <PricingSection />
        <DemoSection />
        <FAQSection />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
