import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';


test('sessions separates club work into five reachable workspace areas', async () => {
  const page = await readFile(new URL('../app/page.tsx', import.meta.url), 'utf8');

  assert.match(page, /type SessionsView = 'overview' \| 'attention' \| 'team' \| 'intelligence' \| 'reviews'/);
  assert.match(page, /aria-label="Sessions workspace"/);
  assert.match(page, /label: 'Overview'/);
  assert.match(page, /label: 'Attention'/);
  assert.match(page, /label: 'Team'/);
  assert.match(page, /label: 'Intelligence'/);
  assert.match(page, /label: 'Session reviews'/);
  assert.match(page, /activeView === 'overview'/);
  assert.match(page, /activeView === 'attention'/);
  assert.match(page, /activeView === 'team'/);
  assert.match(page, /activeView === 'intelligence'/);
  assert.match(page, /activeView === 'reviews'/);
});

test('sessions workspace participates in browser history and restores the selected area', async () => {
  const page = await readFile(new URL('../app/page.tsx', import.meta.url), 'utf8');

  assert.match(page, /const \[sessionsView, setSessionsView\] = useState<SessionsView>\('overview'\)/);
  assert.match(page, /setSessionsView\(state\.sessionsView as SessionsView\)/);
  assert.match(page, /onViewChange=\{openSessionsView\}/);
  assert.match(page, /activeView=\{sessionsView\}/);
});

test('sessions areas render as secondary tabs directly below primary navigation', async () => {
  const page = await readFile(new URL('../app/page.tsx', import.meta.url), 'utf8');
  const css = await readFile(new URL('../app/globals.css', import.meta.url), 'utf8');

  assert.match(page, /function SessionsSubnavigation/);
  assert.match(page, /<AppHeader[^>]+\/>\{screen === 'sessions' \? <SessionsSubnavigation activeView=\{sessionsView\} onViewChange=\{openSessionsView\} \/> : null\}/);
  assert.match(page, /<nav aria-label="Sessions workspace" className="sessions-workspace-nav">/);
  assert.doesNotMatch(page, /function SessionsScreen[\s\S]*?<nav aria-label="Sessions workspace"/);
  assert.match(css, /\.sessions-subnav \{[^}]*border-bottom: 1px solid var\(--line-strong\);[^}]*background: var\(--surface\);/s);
  assert.match(css, /\.sessions-workspace-tab\.active \{[^}]*border-bottom-color: var\(--accent\);[^}]*color: var\(--accent\);/s);
});

test('mobile secondary tabs expose every sessions area as a visible button grid', async () => {
  const css = await readFile(new URL('../app/globals.css', import.meta.url), 'utf8');

  assert.match(css, /@media \(max-width: 620px\) \{[\s\S]*\.sessions-workspace-nav \{[^}]*display: grid;[^}]*grid-template-columns: 1fr 1fr;[^}]*overflow-x: visible;/);
  assert.match(css, /\.sessions-workspace-tab \{[^}]*min-width: 0;[^}]*flex: none;/s);
  assert.match(css, /\.sessions-workspace-tab:last-child \{[^}]*grid-column: 1 \/ -1;/s);
});

test('session pages rely on the single global review action', async () => {
  const page = await readFile(new URL('../app/page.tsx', import.meta.url), 'utf8');
  const reviewActions = page.match(/>Review a session<\/button>/g) ?? [];

  assert.equal(reviewActions.length, 1);
  assert.doesNotMatch(page, /sessions-workspace-heading[\s\S]{0,700}>Review a session<\/button>/);
});

test('overview destinations render as prominent icon shortcuts', async () => {
  const page = await readFile(new URL('../app/page.tsx', import.meta.url), 'utf8');
  const css = await readFile(new URL('../app/globals.css', import.meta.url), 'utf8');

  assert.match(page, /className="product-shortcuts"/);
  assert.equal((page.match(/className="product-shortcut /g) ?? []).length, 2);
  assert.match(page, /aria-label="View evaluation results"/);
  assert.match(page, /aria-label="Open competition review"/);
  assert.equal((page.match(/className="product-shortcut-icon"/g) ?? []).length, 2);
  assert.match(css, /\.product-shortcut \{[^}]*min-height: 76px;[^}]*border: 1px solid var\(--line-strong\);[^}]*box-shadow:/s);
  assert.match(css, /\.product-shortcut-icon \{[^}]*display: grid;[^}]*place-items: center;/s);
  assert.match(css, /@media \(max-width: 620px\) \{[\s\S]*\.product-shortcuts \{[^}]*grid-template-columns: 1fr;/s);
  assert.doesNotMatch(page, /className="page-header-actions"/);
});

test('session reviews keep storage context on demand without a repeated introduction', async () => {
  const page = await readFile(new URL('../app/page.tsx', import.meta.url), 'utf8');
  const css = await readFile(new URL('../app/globals.css', import.meta.url), 'utf8');

  assert.match(page, /function StorageContextIndicator/);
  assert.match(page, /aria-label="Show local storage details"/);
  assert.match(page, /activeView === 'reviews' \? <StorageContextIndicator \/> : null/);
  assert.doesNotMatch(page, /className="operational-inbox-heading"/);
  assert.doesNotMatch(page, /className="storage-note"/);
  assert.doesNotMatch(page, /Move between areas without scrolling through the entire club history/);
  assert.match(css, /\.storage-context-status \{[^}]*margin-left: auto;/s);
  assert.doesNotMatch(css, /\.storage-note \{/);
});
