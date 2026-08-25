# React and Vite implementation

Read this reference when creating or materially changing a website.

## Project foundation

- Use the current stable Vite React template compatible with the repository’s Node version.
- Keep dependencies lean. Add a router, animation library, icon set, or CSS framework only when the site truly benefits.
- Organize reusable page geometry and tokens centrally. Keep page-specific composition close to the page or section component.
- Prefer semantic HTML and native controls. Use landmarks, a logical heading order, useful alternative text, visible focus states, and keyboard-operable navigation.
- Keep content in structured data when repeated modules share a schema; do not duplicate large component trees.
- Use inline SVG or code-native vector marks for functional arrows, flags, and repository links. Do not rely on emoji or font glyph substitution for identity-bearing or functional icons.

Suggested token shape:

```css
:root {
  --grid-columns: 12;
  --grid-gutter: clamp(1rem, 2vw, 2rem);
  --page-margin: clamp(1rem, 4vw, 4.5rem);
  --baseline: 0.5rem;
  --color-paper: #f2f1ed;
  --color-ink: #111;
  --color-accent: #e1261c;
}

.grid {
  display: grid;
  grid-template-columns: repeat(var(--grid-columns), minmax(0, 1fr));
  gap: var(--grid-gutter);
  margin-inline: var(--page-margin);
}
```

Adapt values to the content; do not copy the sample blindly.

## Mobile rendering

Design the phone composition explicitly before considering the responsive work complete.

- Keep the viewport meta tag correct and use responsive layout primitives rather than fixed page widths.
- Define phone-specific grid columns, gutters, and edge margins. Use a 2- or 4-column grid when appropriate and declare each module’s start, span, and content order.
- Test all routes at 320, 360, 375, 390, and 430 CSS px, plus a short landscape viewport. Do not rely on a single device preset.
- Prevent accidental overflow: use `minmax(0, 1fr)` for grid tracks, `min-width: 0` on shrinkable children, safe wrapping for long URLs/labels, and responsive media bounded by their containers.
- Keep ordinary body text comfortably readable without zoom. Avoid tiny Swiss-style captions; functional labels must remain legible.
- Give interactive targets adequate touch area and separation. Do not make hover the only way to reveal information or controls.
- Ensure navigation opens, closes, traps no focus, restores focus appropriately, and does not obscure content. Account for the on-screen keyboard in forms and menus.
- Use `svh`/`dvh` deliberately where viewport-height layouts are necessary; avoid brittle `100vh` hero sections on mobile browsers.
- Respect display cutouts and browser chrome where edge-to-edge fixed UI is used, via `env(safe-area-inset-*)` with sensible fallbacks.
- Serve appropriately sized images with stable aspect ratios. Keep the primary content and navigation usable on slow connections even while imagery loads.
- Check sticky and fixed elements against zoom, orientation changes, long translated text, and the mobile keyboard.
- Preserve the reading order in the DOM. Visual grid rearrangement must not produce a confusing screen-reader or keyboard order.
- Use deliberate responsive copy when one string cannot compose well everywhere. A long desktop interaction note may need a concise touch-specific variant; make the active variant deterministic and accessible rather than shrinking text or accepting uncontrolled wraps.
- Treat the phone footer as an explicit grid state. Declare its semantic rows and alignment at each target width instead of relying on natural wrapping.

Mobile Swiss design should retain rigor through fewer relationships, not miniaturization: reduce columns, shorten measures, simplify secondary metadata, and preserve the strongest alignment and hierarchy.

## Tablet composition

Treat tablets as a separate responsive state rather than assuming desktop or phone rules will interpolate successfully.

- Inspect representative widths at 768, 834, 1024, and 1366 CSS px in relevant orientations.
- Reassign grid starts and spans deliberately for tablet reading order, navigation, metrics, figures, and footers.
- Check large metrics with units, multi-column figure captions, navigation density, and mixed text/media modules for awkward intermediate wrapping.
- When specific hardware is in scope, include iPad Pro portrait and its realistic device-pixel ratio in screenshot inspection.

## Scientific measurements

- Use one project-wide formatter for signs, decimal precision, spacing, degree symbols, units, and anomalies across prose, cards, tables, and plots.
- Keep a value and its unit in one non-wrapping semantic group, such as `+5.64 °C`. Make the surrounding grid and responsive type role accommodate the group without clipping.
- Preserve typographic spacing intentionally; do not allow isolated selectors or manual strings to alternate between forms such as `2m` and `2 m`.
- Inspect large bold numerals in screenshots at realistic device-pixel ratios, especially on iOS. Avoid negative tracking when glyphs appear to collide.

## Fade-in on scroll

Implement one reusable reveal primitive with `IntersectionObserver`. Apply it consistently to meaningful sections and stagger repeated children sparingly. A typical transition is opacity `0 → 1` with a small upward translation over roughly 350–650 ms. Content must remain in normal document flow.

Progressive enhancement requirements:

- Render content visible by default.
- Add the hidden initial state only after JavaScript marks the document as reveal-enabled.
- Reveal once unless the user explicitly asks for replay.
- Observe at a modest threshold and unobserve revealed elements.
- Under `prefers-reduced-motion: reduce`, remove transforms and transitions and show content immediately.
- Never implement scroll-jacking, forced snapping, long entrance delays, or blanket transitions on every DOM node.

## Documentation

Add or update repository documentation with:

- prerequisites and exact install/dev/build commands;
- route and component overview;
- grid column counts, margins, gutters, baseline unit, and breakpoint logic;
- mobile navigation, content order, safe-area behavior, and tested viewport widths;
- typography and color tokens;
- reveal behavior and reduced-motion handling;
- asset credits and licenses;
- validation commands and any deliberate grid exceptions.

Use comments for non-obvious implementation reasoning, not narration of self-evident JSX or CSS.

## CSS maintainability

- Keep styles readable and normally formatted; do not retain compressed one-line source stylesheets.
- After clusters of visual revisions, consolidate values into semantic tokens and breakpoint rules.
- Remove repeated selectors, obsolete declarations, and late override layers once the intended state is known.
- Prefer one authoritative definition per role or component state. Document intentional exceptions.

## Browser-validation fallback

If the preferred browser runtime cannot launch in CI, a container, or an HPC environment, record the exact command, error, and checks that could not run. Complete source validation and any available nonvisual assertions, but explicitly defer visual/device approval. Never present source inspection, a successful build, or synthetic DOM measurements as a completed browser screenshot review.
