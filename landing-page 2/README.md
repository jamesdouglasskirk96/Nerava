# Nerava Landing Page

Marketing landing page for Nerava - "Cut EV Charging Costs & Reward Your Drivers Automatically"

## Overview

This is a standalone Next.js marketing site targeting charger owners (apartments, hotels, gyms, offices, universities, retail centers, etc.). It explains how Nerava shifts EV charging to off-peak hours and turns savings into driver perks.

## Technology Stack

- **Next.js 14+** with App Router
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **React 18** for UI components

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- (Optional) Image assets in `public/landing/` directory

### Installation

```bash
cd landing-page
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build for Production

```bash
npm run build
npm start
```

### Type Checking

```bash
npm run type-check
```

### Linting

```bash
npm run lint
```

## Project Structure

```
landing-page/
├── app/
│   ├── components/          # React components for each section
│   │   ├── Header.tsx      # Site header with navigation
│   │   ├── SiteFooter.tsx  # Site footer with links
│   │   ├── Button.tsx      # Reusable button components
│   │   ├── Hero.tsx        # Hero section
│   │   ├── ValueProps.tsx  # "Ready to Reduce EV Charging Costs?"
│   │   ├── HowItWorks.tsx  # Three-step process
│   │   ├── DriverExperience.tsx  # Driver journey (4 steps)
│   │   ├── TrustedBy.tsx   # Social proof section
│   │   ├── HighTrafficVenues.tsx  # Venue examples
│   │   ├── PropertyTypes.tsx      # Property type cards
│   │   ├── NovaEconomy.tsx        # Nova economy loop diagram
│   │   ├── WhyNerava.tsx          # Three benefit cards
│   │   └── ImpactCalculator.tsx   # Interactive savings calculator
│   ├── globals.css         # Global styles with Tailwind
│   ├── layout.tsx          # Root layout with header/footer
│   └── page.tsx            # Main landing page (all sections)
├── public/
│   └── landing/            # Marketing images (to be added)
│       ├── hero-charger.png
│       ├── driver-experience.png
│       ├── high-traffic.png
│       └── why-nerava.png
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.mjs
```

## Component Mapping

Each section component corresponds to a specific part of the landing page:

1. **Hero** - "Cut EV Charging Costs & Reward Your Drivers Automatically"
   - Two-column layout with headline and CTA buttons
   - Right side: Hero charger image placeholder

2. **ValueProps** - "Ready to Reduce EV Charging Costs?"
   - Three value cards: No Hardware, Immediate ROI, Universal Appeal
   - Two CTA buttons

3. **HowItWorks** - Three-step process
   - Upload Usage Report (with file upload widget)
   - Nerava Rewards Behavior
   - Cycle Savings into Perks

4. **DriverExperience** - "The Complete Driver Experience"
   - Four-step driver journey
   - Left: Driver experience image placeholder

5. **TrustedBy** - "Trusted by Modern Properties"
   - Property type icons
   - Testimonial quote

6. **HighTrafficVenues** - "Perfect for High-Traffic Venues"
   - Four venue cards (Grocery, Co-Working, Universities, Retail)
   - Right: High-traffic image placeholder

7. **PropertyTypes** - "Tailored for Every Property Type"
   - Four property type cards with example perks

8. **NovaEconomy** - "The Nova Economy"
   - Circular diagram showing Nova flow
   - Left: Description text

9. **WhyNerava** - "Why Charger Owners Choose Nerava"
   - Three benefit cards
   - Right: Analytics dashboard image placeholder

10. **ImpactCalculator** - "Calculate Your Potential Impact"
    - Interactive form (chargers, sessions/month)
    - Real-time savings calculation (placeholder formula)
    - Two big numbers: Monthly Savings, Driver Perk Value

## Features

- ✅ Fully responsive (mobile-first design)
- ✅ Smooth scrolling navigation
- ✅ Interactive savings calculator (front-end only)
- ✅ File upload widget for usage reports (UI only, no backend)
- ✅ Email CTAs (mailto: links)
- ✅ SEO-friendly metadata
- ✅ Accessible semantic HTML

## Image Assets

Place marketing images in `public/landing/` directory:

- `hero-charger.png` - Hero section image
- `driver-experience.png` - Driver experience illustration
- `high-traffic.png` - High-traffic venues image
- `why-nerava.png` - Analytics dashboard image
- (Additional images as needed)

Currently, components show placeholder gradients where images should be. Uncomment the `<Image />` components in each file once images are added.

## Notes

- **No Backend Integration**: This is a pure marketing site. All forms (calculator, file upload) are front-end only. No API calls are made.
- **Placeholder Formulas**: The impact calculator uses a simple deterministic formula. It's clearly marked as a placeholder and should not be used for real billing.
- **Email Links**: CTAs like "Talk to Sales" use `mailto:` links. Update email addresses as needed.
- **Smooth Scrolling**: All section navigation uses smooth scroll behavior.

## Future Enhancements

- [ ] Add actual marketing images
- [ ] Connect file upload to backend API
- [ ] Connect calculator to backend for real savings estimates
- [ ] Add contact form modal
- [ ] Add analytics tracking
- [ ] Add A/B testing capability

## CTA Environment Variables

The landing page uses environment variables to configure call-to-action (CTA) button URLs. These are **required in production** to ensure CTAs link to the correct applications.

### Required Variables

- `NEXT_PUBLIC_DRIVER_APP_URL` - URL for driver app (e.g., `https://app.nerava.com`)
- `NEXT_PUBLIC_MERCHANT_APP_URL` - URL for merchant portal (e.g., `https://merchant.nerava.com`)

### Optional Variables

- `NEXT_PUBLIC_CHARGER_PORTAL_URL` - URL for charger owner portal (falls back to Google Form if not set)

### How It Works

- **Development**: If env vars are not set, CTAs fall back to Google Forms for testing
- **Production**: Missing required env vars will cause console errors and CTAs will redirect to `/#final-cta`
- **Tracking**: All CTA URLs automatically include tracking parameters (`?src=landing&cta={driver|merchant|charger-owner}`)

### Setting Environment Variables

1. Copy `.env.example` to `.env.local` for local development
2. In production deployments (Vercel, Netlify, etc.), set these variables in your platform's environment settings
3. Never commit `.env.local` or production `.env` files to version control

See `.env.example` for example values and documentation.

## Deployment

This is a standalone Next.js app that can be deployed to:

- Vercel (recommended for Next.js)
- Netlify
- Any Node.js hosting platform

**Important**: Make sure to set the CTA environment variables (see above) in your production deployment configuration.

## License

Part of the Nerava monorepo. All rights reserved.

