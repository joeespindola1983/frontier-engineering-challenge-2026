import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';


test('session review renders adapter findings without case-002-only narration', async () => {
  const page = await readFile(
    new URL('../app/page.tsx', import.meta.url),
    'utf8',
  );

  assert.match(page, /review\.currentReconstruction/);
  assert.doesNotMatch(page, /Six work intervals are supported/);
  assert.doesNotMatch(page, /interval\.index === 4/);
  assert.doesNotMatch(page, /selected case remains fully synthetic/);
});

test('selected evidence uses the prepared live bundle path before review', async () => {
  const page = await readFile(
    new URL('../app/page.tsx', import.meta.url),
    'utf8',
  );

  assert.match(page, /client\.analyzeSourceBundle\(\{\s*sourceIds,/);
  assert.match(page, /configuredRuntimeMode === 'live'/);
  assert.match(page, /authorizedCostUsd: configuredCostAuthorizationUsd/);
  assert.match(page, /setCheckpointId\(result\.checkpointId\)/);
});

test('session row opens the investigation without forwarding the click event as files', async () => {
  const page = await readFile(
    new URL('../app/page.tsx', import.meta.url),
    'utf8',
  );

  assert.match(page, /onClick=\{\(\) => onReview\(\)\}/);
  assert.doesNotMatch(page, /onClick=\{onReview\}/);
});

test('live review discloses approximate usage cost without calling it a hard cap', async () => {
  const page = await readFile(
    new URL('../app/page.tsx', import.meta.url),
    'utf8',
  );

  assert.match(page, /NEXT_PUBLIC_WAKE_COST_AUTHORIZATION_USD/);
  assert.match(page, /Approx\. agent cost/);
  assert.match(page, /executionCost\.approximate_cost_usd/);
  assert.match(page, /Exceeded operational authorization/);
  assert.match(page, /Operational authorization/);
  assert.match(page, /not a provider billing cap/);
  assert.doesNotMatch(page, /Guaranteed cost cap/);
});

test('page asks the athlete checkpoint without describing every answer as coach context', async () => {
  const page = await readFile(
    new URL('../app/page.tsx', import.meta.url),
    'utf8',
  );

  assert.match(page, /Question for \{formatRole\(review\.checkpoint\.expectedRespondentRole\)\}/);
  assert.match(page, /Athlete answered directly/);
  assert.match(page, /Athlete answer recorded by coach/);
  assert.match(page, /Coach observed directly/);
  assert.doesNotMatch(page, /A coach answer is stored as human context/);
});

test('intake distinguishes source origin from the current uploader', async () => {
  const page = await readFile(
    new URL('../app/page.tsx', import.meta.url),
    'utf8',
  );

  assert.match(page, /Origin: \{formatRole\(source\.originRole \?\? contributorRole\)\}/);
  assert.match(page, /uploader: \{formatRole\(contributorRole\)\}/);
});

test('review adapter has no coach-only fallback for unattributed uploads', async () => {
  const adapter = await readFile(
    new URL('../app/lib/replay-adapter.mjs', import.meta.url),
    'utf8',
  );

  assert.match(adapter, /Locally uploaded evidence/);
  assert.doesNotMatch(adapter, /Coach-uploaded local evidence/);
});

test('weather intake makes consent, timezone, provenance, and no-model preparation visible', async () => {
  const page = await readFile(
    new URL('../app/page.tsx', import.meta.url),
    'utf8',
  );

  assert.match(page, /Historical conditions/);
  assert.match(page, /approximate session location/i);
  assert.match(page, /authorizedLocationLookup/);
  assert.match(page, /sessionTimezone/);
  assert.match(page, /<select/);
  assert.match(page, /value=\{sessionTimezone\}/);
  assert.match(page, /America\/Sao_Paulo/);
  assert.doesNotMatch(page, /placeholder="America\/Sao_Paulo"/);
  assert.match(page, /uploadEvidenceBundleWithWeather/);
  assert.match(page, /prepareSourceBundle/);
  assert.match(page, /No agent call/i);
  assert.match(page, /mode: 'replay'/);
  assert.doesNotMatch(page, /weather explains/i);
});

test('session inbox exposes analysis, view, answer, and club-memory milestones', async () => {
  const page = await readFile(
    new URL('../app/page.tsx', import.meta.url),
    'utf8',
  );

  assert.match(page, /Awaiting analysis/);
  assert.match(page, /Viewed by coach/);
  assert.match(page, /Awaiting answer/);
  assert.match(page, /In club memory/);
  assert.match(page, /Saved locally/);
  assert.match(page, /StorageContextIndicator/);
  assert.doesNotMatch(page, /className="storage-note"/);
});

test('session workflow summary uses equal cards and shared metric rows', async () => {
  const css = await readFile(
    new URL('../app/globals.css', import.meta.url),
    'utf8',
  );

  assert.match(css, /\.summary-strip \{[^}]*gap: 1px;[^}]*background: var\(--line\);[^}]*border: 1px solid var\(--line\);/s);
  assert.match(css, /\.summary-strip > div \{[^}]*padding: 20px;[^}]*grid-row: span 3;[^}]*grid-template-rows: subgrid;[^}]*background: var\(--surface\);/s);
  assert.doesNotMatch(css, /\.summary-strip > div:not\(:first-child\) \{[^}]*padding-left:/s);
  assert.match(css, /@media \(max-width: 620px\) \{[\s\S]*\.summary-strip > div \{[^}]*min-height: 134px;[^}]*padding: 16px;[^}]*grid-row: auto;[^}]*grid-template-rows: auto auto 1fr;/s);
});

test('starting another review resets the intake and prevents duplicate preparation', async () => {
  const page = await readFile(
    new URL('../app/page.tsx', import.meta.url),
    'utf8',
  );

  assert.match(page, /intakeRevision/);
  assert.match(page, /startNewReview/);
  assert.match(page, /key=\{intakeRevision\}/);
  assert.match(page, /Preparation complete/);
  assert.match(page, /Start another session review/);
  assert.match(page, /disabled=\{processing \|\| Boolean\(preparedBundle\)\}/);
  assert.match(page, /Prepared · Saved locally/);
});

test('mobile layout preserves primary navigation instead of hiding it', async () => {
  const css = await readFile(
    new URL('../app/globals.css', import.meta.url),
    'utf8',
  );

  assert.doesNotMatch(css, /\.primary-nav \{ display: none; \}/);
  assert.match(css, /\.primary-nav \{[^}]*grid-column: 1 \/ -1;[^}]*grid-row: 2;[^}]*overflow-x: auto;/s);
  assert.match(css, /\.topbar-actions \{[^}]*grid-column: 2;[^}]*grid-row: 1;/s);
});

test('mobile session review contains wide interval content inside its own scroller', async () => {
  const css = await readFile(
    new URL('../app/globals.css', import.meta.url),
    'utf8',
  );

  assert.match(css, /\.review-layout > \* \{ min-width: 0; \}/);
  assert.match(css, /\.interval-bars \{[^}]*max-width: 100%;[^}]*overflow-x: auto;/s);
});

test('current reconstruction is presented as readable evidence-linked bullets', async () => {
  const page = await readFile(
    new URL('../app/page.tsx', import.meta.url),
    'utf8',
  );

  assert.match(page, /buildReconstructionDisplay\(review\.currentReconstruction\)/);
  assert.match(page, /reconstruction-list/);
  assert.match(page, /Evidence used/);
});

test('verified findings use coach-readable evidence names instead of filenames', async () => {
  const page = await readFile(
    new URL('../app/page.tsx', import.meta.url),
    'utf8',
  );

  assert.match(page, /formatEvidenceReference\(ref\)/);
  assert.doesNotMatch(page, /ref\.replace\('input\/', ''\)/);
});

test('detail screens expose location and use internal browser history', async () => {
  const page = await readFile(
    new URL('../app/page.tsx', import.meta.url),
    'utf8',
  );

  assert.match(page, /function LocationTrail/);
  assert.match(page, /aria-label="Current location"/);
  assert.match(page, /aria-label="Back to previous WAKE screen"/);
  assert.match(page, /window\.history\.pushState/);
  assert.match(page, /window\.history\.back\(\)/);
  assert.match(page, /addEventListener\('popstate'/);
  assert.doesNotMatch(page, />Back to club</);
  assert.doesNotMatch(page, />Back to sessions</);
  assert.equal((page.match(/showSessionDetail\(detail\);/g) ?? []).length, 2, 'one call in openSession and one in replay restoration');
});

test('sessions workspace keeps its selected area while opening related detail screens', async () => {
  const page = await readFile(
    new URL('../app/page.tsx', import.meta.url),
    'utf8',
  );

  assert.match(page, /sessionsView: nextSessionsView/);
  assert.match(page, /function openSessionsView\(nextView: SessionsView\)/);
  assert.match(page, /pushScreen\('sessions', \{ sessionsView: nextView \}\)/);
});

test('runtime disclosure is a compact click-controlled status beside the primary review action', async () => {
  const page = await readFile(
    new URL('../app/page.tsx', import.meta.url),
    'utf8',
  );
  const css = await readFile(
    new URL('../app/globals.css', import.meta.url),
    'utf8',
  );

  assert.match(page, /function RuntimeStatusIndicator/);
  assert.match(page, /aria-expanded=\{open\}/);
  assert.match(page, /role="tooltip"/);
  assert.match(page, /window\.setTimeout\(\(\) => setOpen\(false\), 6000\)/);
  assert.match(page, /window\.clearTimeout\(timeout\)/);
  assert.match(page, /<RuntimeStatusIndicator \/>[\s\S]{0,240}<button className="button button-primary button-small"[\s\S]{0,180}>Review a session<\/button>/);
  assert.doesNotMatch(page, /function PrototypeNotice/);
  assert.doesNotMatch(page, /<PrototypeNotice \/>/);
  assert.doesNotMatch(page, /Hover, focus, or click/);
  assert.doesNotMatch(css, /\.runtime-status-wrap:hover \.runtime-status-popover/);
  assert.doesNotMatch(css, /\.runtime-status-wrap:focus-within \.runtime-status-popover/);
  assert.match(css, /\.runtime-status-popover\.open/);
  assert.match(css, /@media \(max-width: 620px\) \{[\s\S]*\.runtime-status-popover \{[^}]*position: fixed;[^}]*right: 14px;[^}]*left: 14px;/);
});

test('mobile intake keeps the review action legible and selected files aligned with their content', async () => {
  const css = await readFile(
    new URL('../app/globals.css', import.meta.url),
    'utf8',
  );
  const mobile = css.slice(css.indexOf('@media (max-width: 620px)'));

  assert.match(mobile, /\.topbar-inner \{[^}]*column-gap: 12px;/s);
  assert.match(mobile, /\.topbar-actions \{[^}]*gap: 8px;/s);
  assert.match(mobile, /\.topbar-actions \.button \{[^}]*width: auto;[^}]*font-size: 10px;/s);
  assert.doesNotMatch(mobile, /\.topbar-actions \.button::after \{[^}]*content: "\+";/s);
  assert.match(mobile, /\.upload-file-action \{[^}]*grid-column: 2;[^}]*justify-self: start;/s);
});

test('reinvestigating an answered sample restores its saved workflow instead of asking again', async () => {
  const page = await readFile(
    new URL('../app/page.tsx', import.meta.url),
    'utf8',
  );

  assert.match(page, /sample\.status === 'VERIFIED'/);
  assert.match(page, /client\.getSession\(sample\.sessionId\)/);
  assert.match(page, /showSessionDetail\(detail\)/);
});
