import puppeteer from 'puppeteer';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const browser = await puppeteer.launch({
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  args: ['--no-sandbox', '--disable-setuid-sandbox']
});

// Profile picture — 800x800
{
  const page = await browser.newPage();
  await page.setViewport({ width: 800, height: 800, deviceScaleFactor: 2 });
  await page.goto('file://' + path.join(__dirname, 'profile-picture.html'), { waitUntil: 'networkidle0' });
  // Find and screenshot just the SVG element
  const svg = await page.$('svg');
  await svg.screenshot({ path: path.join(__dirname, 'profile-picture-800x800.png') });
  console.log('✓ profile-picture-800x800.png');
  await page.close();
}

// Channel banner — 2560x1440
{
  const page = await browser.newPage();
  await page.setViewport({ width: 2560, height: 1440, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(__dirname, 'channel-banner.html'), { waitUntil: 'networkidle0' });
  const svg = await page.$('svg');
  await svg.screenshot({ path: path.join(__dirname, 'channel-banner-2560x1440.png') });
  console.log('✓ channel-banner-2560x1440.png');
  await page.close();
}

await browser.close();
console.log('\nDone. Files saved to youtube-assets/');
