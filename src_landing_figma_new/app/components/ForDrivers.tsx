import { Button } from './Button';
import { Card } from './Card';

export function ForDrivers() {
  const benefits = [
    {
      title: 'Works quietly in the background',
      description: "Nerava detects when you're charging, so you don't have to open anything. Just plug in and discover."
    },
    {
      title: 'Discover walkable places',
      description: 'See coffee shops, restaurants, gyms, and stores within walking distance—no scrolling, no searching.'
    },
    {
      title: 'Instant decisions',
      description: 'Get the information you need to decide quickly. No guessing, no wasting time thinking "what should I do?"'
    }
  ];

  return (
    <section className="w-full py-20 md:py-24 bg-white">
      <div className="max-w-7xl mx-auto px-6 md:px-8">
        <div className="max-w-3xl mx-auto text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            For drivers
          </h2>
          <p className="text-lg text-muted-foreground">
            Nerava works quietly in the background, surfacing nearby businesses exactly when you need them most: during your charging session.
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
          <Button variant="primary">Join the driver waitlist</Button>
        </div>
      </div>
    </section>
  );
}