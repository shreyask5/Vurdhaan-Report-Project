import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';

const faqs = [
  {
    question: 'How does the free trial work?',
    answer:
      'You get full access to all Pro features for 14 days, no credit card required. If you decide to continue after the trial, simply choose a plan and add your payment information.',
  },
  {
    question: 'Can I change plans later?',
    answer:
      'Absolutely! You can upgrade, downgrade, or cancel your plan at any time. Changes take effect immediately, and we will prorate any charges or credits.',
  },
  {
    question: 'What kind of support do you offer?',
    answer:
      'All plans include email support with response times under 24 hours. Pro and Business plans get priority support, and Business customers get dedicated phone support and a customer success manager.',
  },
  {
    question: 'Is my data secure?',
    answer:
      'Yes. We use bank-level AES-256 encryption, are SOC 2 Type II certified, and comply with GDPR and other major privacy regulations. Your data is backed up daily and stored in secure, geo-redundant data centers.',
  },
  {
    question: 'Do you offer custom enterprise plans?',
    answer:
      'Yes! For organizations with more than 100 users or specific requirements, we offer custom enterprise plans with dedicated infrastructure, custom SLAs, and personalized onboarding. Contact our sales team to learn more.',
  },
  {
    question: 'Can I integrate ServicePro with other tools?',
    answer:
      'ServicePro integrates with 100+ popular business tools including Slack, Microsoft Teams, Google Workspace, Salesforce, and more. Pro and Business plans also include API access for custom integrations.',
  },
];

export const FAQSection = () => {
  return (
    <section className="py-24 bg-muted/30">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          {/* Header */}
          <div className="text-center mb-16 space-y-4">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold">
              Frequently Asked{' '}
              <span className="bg-gradient-primary bg-clip-text text-transparent">Questions</span>
            </h2>
            <p className="text-lg text-muted-foreground">
              Everything you need to know about ServicePro
            </p>
          </div>

          {/* FAQ Accordion */}
          <Accordion type="single" collapsible className="space-y-4">
            {faqs.map((faq, index) => (
              <AccordionItem
                key={index}
                value={`item-${index}`}
                className="bg-card border border-border/50 rounded-lg px-6 hover:border-primary/50 transition-colors"
              >
                <AccordionTrigger className="text-left text-base font-semibold hover:no-underline">
                  {faq.question}
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground leading-relaxed">
                  {faq.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>

          {/* Contact CTA */}
          <div className="mt-12 text-center p-8 bg-gradient-card rounded-2xl border border-border/50">
            <p className="text-lg font-medium mb-2">Still have questions?</p>
            <p className="text-muted-foreground mb-4">
              Our team is here to help. Reach out anytime.
            </p>
            <a
              href="mailto:support@servicepro.com"
              className="text-primary hover:underline font-semibold"
            >
              support@servicepro.com
            </a>
          </div>
        </div>
      </div>
    </section>
  );
};
