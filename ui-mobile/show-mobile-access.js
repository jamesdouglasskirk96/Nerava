#!/usr/bin/env node

const { execSync } = require('child_process');
const qrcode = require('qrcode-terminal');

// Get local IP address
function getLocalIP() {
  try {
    // Try en0 first (usually WiFi on Mac)
    const en0 = execSync('ipconfig getifaddr en0', { encoding: 'utf8' }).trim();
    if (en0) return en0;
  } catch (e) {
    // Fallback to en1
    try {
      const en1 = execSync('ipconfig getifaddr en1', { encoding: 'utf8' }).trim();
      if (en1) return en1;
    } catch (e2) {
      // Fallback to ifconfig
      try {
        const ifconfig = execSync('ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1', { encoding: 'utf8' });
        const match = ifconfig.match(/inet (\d+\.\d+\.\d+\.\d+)/);
        if (match) return match[1];
      } catch (e3) {
        return '192.168.1.1'; // fallback
      }
    }
  }
  return '192.168.1.1'; // fallback
}

const ip = getLocalIP();
const port = process.argv[2] || '5173';
const url = `http://${ip}:${port}`;

console.log('\n🚀 NERAVA MOBILE ACCESS');
console.log('========================');
console.log(`📱 Local IP: ${ip}`);
console.log(`🌐 URL: ${url}`);
console.log('\n📱 Scan this QR code on your phone:');
console.log('=====================================');

qrcode.generate(url, { small: true }, (qr) => {
  console.log(qr);
  console.log('\n✅ Instructions:');
  console.log('1. Make sure your phone is on the same WiFi network');
  console.log('2. Scan the QR code above or manually type the URL');
  console.log('3. Allow location access when prompted');
  console.log('4. Test all features: Explore → Earn → Wallet → Me');
  console.log('\n🎯 The app should now work perfectly on your mobile device!');
});
