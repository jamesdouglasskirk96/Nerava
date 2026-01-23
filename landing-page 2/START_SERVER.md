# Starting the Landing Page Server

## Quick Start

Run these commands in your terminal:

```bash
cd "/Users/jameskirk/Desktop/Nerava/landing-page 2"
npm run dev
```

Wait for the output:
```
▲ Next.js 14.2.5
- Local:        http://localhost:3000
✓ Ready in X.Xs
```

Then open http://localhost:3000 in your browser.

## If You See Permission Errors

If you get "Operation not permitted" errors, run:

```bash
cd "/Users/jameskirk/Desktop/Nerava/landing-page 2"
rm -rf .next node_modules
npm install
npm run dev
```

## Verification Checklist

✅ All code files are updated with Figma design
✅ TypeScript type checking passes
✅ No linter errors
✅ CTA helper functions implemented
✅ Environment variables configured
✅ All components match Figma reference

## What You Should See

- Hero section with light blue background (#E8F0FF)
- "Nerava" heading and "What to do while you charge" subtitle
- Two primary buttons: "Open Nerava" and "For Businesses"
- All sections rendered correctly
- Responsive design working

## Troubleshooting

**Blank page**: Check browser console (F12) for JavaScript errors
**Port already in use**: Use `PORT=3001 npm run dev` to use a different port
**Build errors**: Clear `.next` folder and restart: `rm -rf .next && npm run dev`




