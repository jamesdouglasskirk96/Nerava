import { Button } from './Button';
import { Card } from './Card';

export function ForMerchants() {
  const benefits = [
    {
      title: 'Pay only for charging session impressions',
      description: "You only pay when drivers are actively charging nearby. No wasted ad spend on people who can't reach you."
    },
    {
      title: 'Set a daily cap—no overruns',
      description: 'Control your spend with a daily maximum. Once you hit it, your listing still appears, but you stop paying for the day.'
    },
    {
      title: 'No POS integrations required',
      description: 'Simple onboarding: no terminals, no integrations, and no commitments. You just start appearing to nearby drivers.'
    }
  ];

  return (
    <section className="w-full py-20 md:py-24 bg-secondary">
      <div className="max-w-7xl mx-auto px-6 md:px-8">
        <div className="max-w-3xl mx-auto text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            For merchants near chargers
          </h2>
          <p className="text-lg text-muted-foreground">
            Reach drivers at the perfect moment—when they're charging nearby and actively deciding what to do. Pay only during charging windows, with full control over your daily spend.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto mb-12">
          {benefits.map((benefit, index) => (
            <Card key={index}>
              <h3 className="font-bold text-foreground mb-2">{benefit.title}</h3>
              <p className="text-muted-foreground">{benefit.description}</p>
            </Card>
          ))}
        </div>
        <div className="text-center">
          <Button variant="primary">Get listed near chargers</Button>
        </div>
      </div>
    </section>
  );
}