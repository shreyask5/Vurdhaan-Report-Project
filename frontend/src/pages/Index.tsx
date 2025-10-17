import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { HeroSection } from '@/components/home/HeroSection';
import { FeaturesSection } from '@/components/home/FeaturesSection';
import { PricingSection } from '@/components/home/PricingSection';
import { TestimonialsSection } from '@/components/home/TestimonialsSection';
import { DemoSection } from '@/components/home/DemoSection';
import { FAQSection } from '@/components/home/FAQSection';

const Index = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Check if this is a Firebase action link (email verification, password reset, etc.)
  useEffect(() => {
    const mode = searchParams.get('mode');
    const oobCode = searchParams.get('oobCode');

    // If we have Firebase action parameters, redirect to the handler page
    if (mode && oobCode) {
      console.log('[INDEX] Detected Firebase action link, redirecting to handler...');
      // Preserve all query parameters
      navigate(`/email-verification?${searchParams.toString()}`);
    }
  }, [searchParams, navigate]);

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
