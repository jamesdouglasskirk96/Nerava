const sharp = require('sharp');

async function createIcons() {
  try {
    // Create 192x192 icon
    await sharp({
      create: {
        width: 192,
        height: 192,
        channels: 4,
        background: { r: 59, g: 130, b: 246, alpha: 1 }
      }
    })
    .composite([
      {
        input: Buffer.from(`
          <svg width="192" height="192" viewBox="0 0 192 192" xmlns="http://www.w3.org/2000/svg">
            <rect width="192" height="192" rx="24" fill="#3B82F6"/>
            <path d="M96 40 L120 40 L120 80 L140 80 L140 120 L120 120 L120 160 L96 160 L96 120 L76 120 L76 80 L96 80 Z" fill="white"/>
            <text x="96" y="180" text-anchor="middle" fill="white" font-family="Arial, sans-serif" font-size="16" font-weight="bold">NERAVA</text>
          </svg>
        `),
        top: 0,
        left: 0
      }
    ])
    .png()
    .toFile('assets/icon-192.png');

    // Create 512x512 icon
    await sharp({
      create: {
        width: 512,
        height: 512,
        channels: 4,
        background: { r: 59, g: 130, b: 246, alpha: 1 }
      }
    })
    .composite([
      {
        input: Buffer.from(`
          <svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
            <rect width="512" height="512" rx="64" fill="#3B82F6"/>
            <path d="M256 100 L320 100 L320 200 L380 200 L380 300 L320 300 L320 400 L256 400 L256 300 L196 300 L196 200 L256 200 Z" fill="white"/>
            <text x="256" y="480" text-anchor="middle" fill="white" font-family="Arial, sans-serif" font-size="42" font-weight="bold">NERAVA</text>
          </svg>
        `),
        top: 0,
        left: 0
      }
    ])
    .png()
    .toFile('assets/icon-512.png');

    console.log('✅ Icons created successfully!');
  } catch (error) {
    console.error('❌ Error creating icons:', error);
  }
}

createIcons();
