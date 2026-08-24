# React and Vite implementation

Read this reference when creating or materially changing a website.

## Project foundation

- Use the current stable Vite React template compatible with the repository’s Node version.
- Keep dependencies lean. Add a router, animation library, icon set, or CSS framework only when the site truly benefits.
- Organize reusable page geometry and tokens centrally. Keep page-specific composition close to the page or section component.
- Prefer semantic HTML and native controls. Use landmarks, a logical heading order, useful alternative text, visible focus states, and keyboard-operable navigation.
- Keep content in structured data when repeated modules share a schema; do not duplicate large component trees.

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

Mobile Swiss design should retain rigor through fewer relationships, not miniaturization: reduce columns, shorten measures, simplify secondary metadata, and preserve the strongest alignment and hierarchy.

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
