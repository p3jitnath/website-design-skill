# Final review checklist

## Grid

- The design specification records columns, gutters, margins, baseline, and breakpoints.
- A development overlay matches the production grid exactly.
- Major edges and repeated modules align at representative desktop, tablet, and mobile widths.
- No unexplained magic offsets undermine the grid.
- Responsive layouts are recomposed rather than squeezed.

## Tablet acceptance gate

- Every route has been inspected at 768, 834, 1024, and 1366 CSS px where relevant.
- Tablet states have deliberate grid spans and content ordering rather than accidental interpolation.
- Metrics retain their units, navigation remains balanced, figures and captions compose cleanly, and intermediate line wraps do not weaken hierarchy.
- When named devices are in scope, screenshots use realistic CSS viewports and device-pixel ratios, including iPad Pro portrait.

## Mobile acceptance gate

- Every route has been inspected at 320, 360, 375, 390, and 430 CSS px and in a short landscape viewport.
- When named devices are in scope, include iPhone 15 Pro portrait at a realistic device-pixel ratio rather than relying only on a generic viewport preset.
- Capture screenshots at the target widths and visually inspect wrapping, centring, line count, text collisions, touch-target spacing, and safe-area padding; absence of overflow alone is not sufficient.
- There is no unintended horizontal scrolling, clipped text, overlapping content, or off-screen control.
- Phone layouts use declared grid starts and spans rather than a stack of arbitrary margins.
- Navigation, dialogs, forms, filters, carousels, and other interactions work with touch and keyboard input.
- Touch targets are adequately sized and separated; hover is never required.
- Body copy and functional labels remain readable without zoom.
- Responsive copy variants show exactly where intended and preserve the same meaning.
- Images preserve aspect ratio, load at appropriate sizes, and do not cause disruptive layout shifts.
- Fixed or sticky UI accounts for browser chrome, safe areas, orientation changes, and the on-screen keyboard.
- The visual order agrees with the semantic DOM reading order.
- Reveal animations do not leave mobile content invisible during fast scrolling or slow script execution.
- Footer content occupies the intended semantic rows and baselines at each target width.
- Scientific values and units remain an indivisible, correctly formatted group without clipping or unwanted wraps.

## Communication and form

- Content hierarchy is understandable before decoration or motion.
- Typography is predominantly sans-serif, flush-left/ragged-right, restrained in weights, and readable in measure.
- Asymmetry feels balanced and intentional.
- Color and geometry have defined functions.
- Photography is relevant, decisively cropped, credited, and licensed.
- The site does not rely on Swiss-style clichés.

## Interaction and accessibility

- Sections fade in during normal scrolling without scroll hijacking.
- Content is visible if JavaScript fails and immediate under reduced motion.
- Keyboard navigation, focus visibility, landmarks, headings, labels, and alternative text are sound.
- Text and controls meet appropriate contrast and target-size expectations.
- Layout remains usable at 200% zoom and without horizontal overflow at narrow widths.
- Content remains usable under text enlargement and with long words, URLs, and realistic content lengths.

## Engineering and documentation

- The project is React on Vite.
- Console output is clean during key journeys.
- Lint, tests when present, and production build pass.
- CSS has no accidental repeated selectors, obsolete late overrides, or compressed one-line source files; tokens and breakpoint rules reflect the final design.
- No placeholder content, broken links, nonfunctional controls, or missing route states remain.
- Repository documentation explains setup, architecture, design tokens, grid logic, motion, accessibility, and asset provenance.
- Browser assertions supplement screenshots: no document overflow, intended footer row count, exact responsive copy visibility, expected element coordinates where centring matters, reduced-motion visibility, clean console output, and successful asset responses.
- Visualization assertions verify ordered animation delays, intended data-change restarts, no ordinary-scroll replay, and fully visible reduced-motion states.
- Link behavior distinguishes in-page navigation, internal routes/downloads, and external sources. Internal actions preserve the current page; external new-tab behavior and `rel` values are consistent with project policy.
- Favicon, theme color, document title, description, asset MIME types, and production subdirectory paths are correct.
- When deployment is in scope, CI and hosting finish successfully; the live HTTP response, bundle copy, styles, fonts, and assets match the intended release.
- If browser automation cannot run, the report states the exact limitation and defers visual approval; source checks and builds are not described as device validation.
