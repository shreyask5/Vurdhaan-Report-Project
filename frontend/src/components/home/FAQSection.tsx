import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';

const faqs = [
  {
    question: 'Which carbon schemes does Vurdhaan Reports support?',
    answer:
      'Vurdhaan Reports supports all major aviation carbon compliance schemes including CORSIA (Carbon Offsetting and Reduction Scheme for International Aviation), EU ETS (European Union Emissions Trading System), UK ETS, CH ETS (Swiss ETS), and ReFuelEU Aviation. Each scheme has customized validation rules and reporting templates.',
  },
  {
    question: 'How does the automated validation work?',
    answer:
      'Our platform includes built-in validation rules specific to each compliance scheme. As you enter data or upload documents, the system automatically checks for completeness, accuracy, and compliance with scheme requirements. Any errors or warnings are flagged immediately with clear guidance on how to resolve them.',
  },
  {
    question: 'Can multiple team members collaborate on reports?',
    answer:
      'Yes! Vurdhaan Reports is designed for team collaboration. Multiple users can work on the same project simultaneously, with role-based access controls. You can also use our AI-powered chat feature to get instant answers to compliance questions without leaving the platform.',
  },
  {
    question: 'Is my emissions data secure?',
    answer:
      'Absolutely. We use enterprise-grade AES-256 encryption for all data at rest and in transit. The platform includes comprehensive audit trails, role-based access controls, and regular security audits. Your sensitive emissions data is stored in secure, geo-redundant data centers with daily backups.',
  },
  {
    question: 'How does the monitoring plan review process work?',
    answer:
      'The platform guides you through creating compliant monitoring plans with scheme-specific templates and requirements. You can collaborate with your team, track review status, and receive feedback all within the system. The AI assistant can help answer questions about specific monitoring plan requirements.',
  },
  {
    question: 'Can I export my data and reports?',
    answer:
      'Yes! All reports and data can be exported in multiple formats suitable for submission to regulatory authorities. The platform maintains version control of all documents and submissions, ensuring you have a complete audit trail of your compliance activities.',
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
              Everything you need to know about Vurdhaan Reports
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
              Our compliance experts are here to help. Reach out anytime.
            </p>
            <a
              href="mailto:support@vurdhaan.com"
              className="text-primary hover:underline font-semibold"
            >
              support@vurdhaan.com
            </a>
          </div>
        </div>
      </div>
    </section>
  );
};
