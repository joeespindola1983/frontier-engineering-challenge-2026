import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';


test('design system defines an accessible, bounded type scale', async () => {
  const css = await readFile(new URL('../app/globals.css', import.meta.url), 'utf8');

  assert.match(css, /--type-label: 0\.6875rem;/);
  assert.match(css, /--type-caption: 0\.75rem;/);
  assert.match(css, /--type-body: 0\.875rem;/);
  assert.match(css, /--type-copy: 0\.9375rem;/);
  assert.match(css, /--type-lede: 1\.0625rem;/);
  assert.match(css, /--type-display: clamp\(2\.25rem, 5vw, 3\.625rem\);/);
  assert.match(css, /--type-page-title: clamp\(2rem, 4vw, 3rem\);/);
  assert.match(css, /\.page-header h1 \{[^}]*font-size: var\(--type-display\);/s);
  assert.match(css, /\.evaluation-header h1 \{[^}]*font-size: var\(--type-display\);/s);
});


test('readable copy and metadata use semantic typography tokens', async () => {
  const css = await readFile(new URL('../app/globals.css', import.meta.url), 'utf8');

  assert.match(css, /\.page\.page p \{[^}]*font-size: var\(--type-body\);[^}]*line-height: var\(--leading-copy\);/s);
  assert.match(css, /\.page\.page small \{[^}]*font-size: var\(--type-caption\);/s);
  assert.match(css, /:is\([\s\S]*?\.summary-strip span,[\s\S]*?\.competition-result-head,[\s\S]*?\) \{ font-size: var\(--type-label\);/);
  assert.match(css, /\.finding-intro \{[^}]*font-size: var\(--type-lede\);/s);
  assert.match(css, /\.club-boundary p,[^}]*font-size: var\(--type-copy\);/s);
  assert.match(css, /\.crew-card > div:first-child > small \{ font-size: var\(--type-caption\); \}/);
  assert.match(css, /\.training-day-activity > div:first-child > small \{ font-size: var\(--type-caption\); \}/);
});


test('prominent cards share surface, radius and elevation tokens', async () => {
  const css = await readFile(new URL('../app/globals.css', import.meta.url), 'utf8');

  assert.match(css, /--radius-card: 0\.5rem;/);
  assert.match(css, /--shadow-card: 0 10px 30px rgba\(17, 23, 21, 0\.07\);/);
  assert.match(css, /--shadow-card-hover: 0 14px 36px rgba\(17, 23, 21, 0\.11\);/);
  assert.match(css, /:is\(\s*\.club-boundary,[^}]+\) \{[^}]*border-radius: var\(--radius-card\);[^}]*box-shadow: var\(--shadow-card\);/s);
  assert.match(css, /:is\(\s*\.crew-card,[^}]+\):hover \{[^}]*box-shadow: var\(--shadow-card-hover\);/s);
});


test('primary navigation exposes and visually emphasizes the current location', async () => {
  const css = await readFile(new URL('../app/globals.css', import.meta.url), 'utf8');
  const page = await readFile(new URL('../app/page.tsx', import.meta.url), 'utf8');

  assert.equal((page.match(/aria-current=/g) ?? []).length, 6);
  assert.match(page, /aria-current=\{sessionActive \? 'page' : undefined\}/);
  assert.match(page, /aria-current=\{screen === 'evaluation' \? 'page' : undefined\}/);
  assert.match(css, /\.primary-nav button\.active \{[^}]*background: var\(--accent-soft\);[^}]*font-weight: 700;[^}]*border-bottom-color: var\(--accent\);/s);
  assert.match(css, /\.primary-nav button:focus-visible \{[^}]*outline: 2px solid var\(--accent\);/s);
});
