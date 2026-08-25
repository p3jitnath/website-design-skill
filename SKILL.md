---
name: swiss-website-design
description: Design, build, revise, and audit websites in Josef Müller-Brockmann’s rigorous Swiss International Typographic Style. Use for grid-led web design, typographic editorial sites, portfolios, institutional sites, and React frontends that require disciplined hierarchy, restrained color, objective imagery, and purposeful motion.
metadata:
  short-description: Build rigorous Swiss-style React websites
---

# Swiss Website Design

Build functional websites whose structure, typography, and behavior translate Josef Müller-Brockmann’s design principles to the web. Do not merely imitate a poster aesthetic: derive every composition from content, an explicit grid, and a clear communication hierarchy.

## Non-negotiable requirements

- Use React with Vite. If starting from nothing, scaffold a Vite React application; do not substitute static HTML, Next.js, a page builder, or another framework unless the user explicitly overrides this requirement.
- Make the grid mathematically explicit before styling components. Define container margins, columns, gutters, vertical rhythm, component spans, and breakpoint transformations as shared CSS tokens.
- Align every major edge to the grid. Avoid arbitrary offsets, decorative misalignment, and one-off magic numbers.
- Use flush-left, ragged-right typography by default, with a restrained sans-serif family, few weights, strong scale contrast, and readable measures.
- Define named semantic type roles before tuning components: navigation, metadata, section labels, headlines and metrics, controls, figure annotations, map labels, body copy, and footer text. Do not accumulate selector-specific font-size overrides.
- Prefer asymmetry, objective photography, geometric form, generous negative space, functional color, and zero gratuitous ornament.
- Make phone and tablet layouts first-class compositions, not scaled desktop fallbacks. Every page must render cleanly from 320 CSS px upward, use deliberate grid spans at each state, preserve hierarchy and rhythm, avoid horizontal overflow, and remain fully operable by touch.
- Apply reveal-on-scroll fades to page sections and repeated content. The reveal must be subtle, must not delay access to content, and must become immediate when `prefers-reduced-motion: reduce` is active. Do not hijack scroll, add fake inertia, or hide essential content when JavaScript fails.
- Produce a polished, accessible, content-complete result. Do not leave placeholder copy, fake controls, broken routes, or decorative interactions without a purpose.
- Document the generated website in its repository: include setup/run/build commands, design tokens, grid logic, component structure, content/image sources, and important accessibility decisions.

## Workflow

1. Inspect the repository, existing design system, content, routes, assets, and project instructions before editing. Preserve working conventions unless they conflict with the request.
2. Clarify or infer the site’s communication objective and rank its content. The most important information receives the strongest typographic and spatial emphasis.
3. Read [references/swiss-design-system.md](references/swiss-design-system.md) before designing and [references/react-vite-implementation.md](references/react-vite-implementation.md) before implementation. When the site contains charts or maps, read [references/data-visualization.md](references/data-visualization.md). When it includes custom fonts, favicons, deployment, or social previews, read [references/production-identity.md](references/production-identity.md).
4. Write a compact design specification before implementation: grid geometry at each breakpoint, baseline unit, type scale, palette roles, image treatment, interaction states, reveal behavior, and the mobile navigation/content order.
5. Build semantic components from the design tokens. Establish the grid and page shell first, then typography, content modules, imagery, and motion.
6. Inspect every route at 320, 360, 375, 390, and 430 CSS px; 768, 834, 1024, and 1366 px tablet states; and desktop widths. Also check a short landscape phone viewport. When named devices are in scope, test their CSS viewport and realistic device-pixel ratio. Use the development grid overlay and screenshots to verify alignment and visual quality rather than judging from source or overflow checks alone.
7. During a long revision session, periodically consolidate new values into semantic tokens, remove superseded CSS, and rerun the viewport matrix rather than layering overrides indefinitely.
8. Run the project’s lint, tests, and production build. Review the result with [references/review-checklist.md](references/review-checklist.md), fix material failures, and report what was verified.

## Design judgment

The grid is an ordering principle, not a cage. Use it to create clarity and meaningful contrast. Controlled exceptions are allowed only when they reinforce the content and remain visibly related to grid lines. Record intentional exceptions in the design documentation.

Avoid the common false signals of “Swiss style”: random red rectangles, excessive rules, tiny unreadable labels, gratuitous all-caps, generic black-and-white minimalism, poster layouts pasted onto every screen, and animation that competes with information.

Use actual content whenever available. Choose images for documentary or conceptual relevance, crop them decisively, and record their source and license. Do not browse for visual references or assets unless the user permits or requests internet research.

## Completion standard

A website is complete only when it runs as a React/Vite project, its production build succeeds, every route passes the documented mobile viewport checks without clipping or horizontal overflow, key layouts align to the documented grid, touch targets and navigation work, responsive states are coherent, scroll reveals work with a reduced-motion fallback, keyboard focus is visible, and repository documentation explains how to maintain the system. When deployment is in scope, completion also requires successful CI/deployment and inspection of the live site—not only a local build.
