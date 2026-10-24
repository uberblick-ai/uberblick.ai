// Records the document-history walkthrough against a running, isolated `ub open`.
// usage: node record-v2.mjs <playwright index.mjs> <storageState.json> <outDir> [light|dark]
// The app follows the system colour scheme unless a stored appearance setting pins it,
// and a fresh storage state has none, so `colorScheme` alone picks the theme.
const [pwPath, storage, outDir, scheme = 'light'] = process.argv.slice(2);
if (!['light', 'dark'].includes(scheme)) throw new Error(`colour scheme must be light or dark, got ${scheme}`);
const { chromium } = await import(pwPath);
import fs from 'node:fs';

const BASE = 'http://127.0.0.1:5199';
const WS = '722007fa-8921-45ee-a580-e20311030fef';
const DOC = 'Web UI system';
const size = { width: 1440, height: 900 };

const browser = await chromium.launch();
const context = await browser.newContext({
  storageState: storage, viewport: size, colorScheme: scheme, reducedMotion: 'no-preference',
  recordVideo: { dir: outDir, size },
});
// A visible cursor dot that follows the mouse and dips on press; the white ring keeps it readable on dark.
await context.addInitScript(() => {
  const install = () => {
    const dot = document.createElement('div');
    dot.id = 'rec-cursor';
    Object.assign(dot.style, {
      position: 'fixed', left: '0', top: '0', width: '22px', height: '22px', margin: '-11px 0 0 -11px',
      borderRadius: '50%', background: 'rgba(230, 120, 20, 0.55)', border: '2px solid rgba(160, 70, 0, 0.9)',
      boxShadow: '0 0 0 2px rgba(255,255,255,0.85), 0 1px 6px rgba(0,0,0,0.35)', pointerEvents: 'none', zIndex: '2147483647',
      transform: 'translate(-100px,-100px)', transition: 'width 120ms, height 120ms, margin 120ms',
    });
    document.documentElement.appendChild(dot);
    addEventListener('mousemove', e => { dot.style.transform = `translate(${e.clientX}px, ${e.clientY}px)`; }, true);
    addEventListener('mousedown', () => Object.assign(dot.style, { width: '14px', height: '14px', margin: '-7px 0 0 -7px' }), true);
    addEventListener('mouseup', () => Object.assign(dot.style, { width: '22px', height: '22px', margin: '-11px 0 0 -11px' }), true);
  };
  if (document.readyState === 'loading') addEventListener('DOMContentLoaded', install); else install();
});

const page = await context.newPage();
const t0 = Date.now();
const log = [];
const mark = (what) => { const s = ((Date.now() - t0) / 1000).toFixed(1); log.push(`${s}s ${what}`); console.log(s, what); };
const wait = (ms) => page.waitForTimeout(ms);
let mouse = { x: 720, y: 450 };
async function moveTo(x, y, steps = 40) { await page.mouse.move(x, y, { steps }); mouse = { x, y }; }
async function moveToLocator(loc) {
  await loc.waitFor({ state: 'visible' });
  const box = await loc.boundingBox();
  await moveTo(box.x + box.width / 2, box.y + box.height / 2);
}
async function click(loc, after = 1800) { await moveToLocator(loc); await wait(350); await page.mouse.down(); await wait(90); await page.mouse.up(); await wait(after); }
const historyGroup = () => page.getByRole('group', { name: 'Document history', exact: true });
const prevRevision = () => historyGroup().getByRole('button', { name: 'Previous revision', exact: true }).first();

await page.goto(`${BASE}/${WS}`);
await page.getByRole('button', { name: DOC, exact: true }).first().waitFor();
await wait(1500);
const start = (Date.now() - t0) / 1000;
await page.mouse.move(mouse.x, mouse.y);
mark('All documents (start)');
await wait(1800);

// Open the document.
await click(page.getByRole('button', { name: DOC, exact: true }).first(), 2600);
mark('Opened Web UI system');
await moveTo(700, 420, 25); await wait(1200);

// Open history from the live status line.
await click(prevRevision(), 3000);
mark('History open: 1 of 9');

// Further back, one revision at a time.
await click(prevRevision(), 3000);
mark('2 of 9');
await click(prevRevision(), 2400);
mark('3 of 9');

// Expand the run of unchanged blocks, then scroll gently to the change.
const fold = page.locator('.ub-revision-fold-button').filter({ hasText: /^18 unchanged blocks/ }).last();
await click(fold, 2200);
mark('Expanded 18 unchanged blocks');
const firstChange = page.locator('.ub-revision-pane [data-revision-change]').first();
await moveTo(1150, 520, 25);
// 18 expanded blocks push the change well past one screen, so allow enough steps to reach it.
for (let i = 0; i < 40; i++) {
  const box = await firstChange.boundingBox();
  if (!box || box.y < 560) break;
  await page.mouse.wheel(0, Math.min(240, box.y - 380));
  await wait(110);
}
await wait(2600);
mark('Scrolled to the change');

// Further back.
await click(prevRevision(), 3000);
mark('4 of 9');
await moveTo(1150, 560, 25); await wait(2800);

// Back to the current version and rest.
await click(page.getByRole('button', { name: 'Back to now', exact: true }).first(), 2600);
mark('Back to now');
await moveTo(1150, 760, 40);
await wait(3000);
mark('End');
const video = page.video();
await context.close();
await browser.close();
const raw = await video.path();
fs.writeFileSync(`${outDir}/timing.json`, JSON.stringify({ raw, start, log }, null, 1));
console.log('raw', raw, 'start', start);
