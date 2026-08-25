# Müller-Brockmann design system for the web

Use this reference when defining the visual system. The objective is clear, objective communication through a rational structure—not nostalgic surface styling.

## Source-grounded principles

Authoritative summaries of the International Typographic Style emphasize precision, typographic grids, sans-serif type, simple typography, rational composition without ornament, objective photography, and restrained color. Museum für Gestaltung describes Müller-Brockmann’s industrial work through objective photography, grid-based layout, sans-serif type, and functional color. His own writing frames the grid as an organizing system for typography, photography, illustration, and color.

Primary research links:

- [Swiss National Library: The International Style, 1950–1970](https://www.nb.admin.ch/en/the-international-style-1950-1970)
- [Museum für Gestaltung: Atelier Müller-Brockmann](https://www.eguide.ch/en/ausstellungstexte/atelier-muller-brockmann-industrial-graphic-design/)
- [Museum für Gestaltung collection: Josef Müller-Brockmann](https://www.emuseum.ch/people/36401/josef-mullerbrockmann/objects)
- [Swiss Federal Department of Foreign Affairs: Swiss Style forever](https://www.aboutswitzerland.eda.admin.ch/en/swiss-style-forever)
- [Cooper Hewitt: A Harmony of Contrasts](https://www.cooperhewitt.org/2018/08/05/aharmonyofcontrasts/)

## Grid construction

Start from content relationships, then choose the smallest useful grid that supports them.

- Use one centered page container and a consistent outer margin.
- Define columns and gutters explicitly with CSS custom properties. A strong default is 12 columns on wide screens, 6 on tablets, and 2 or 4 on phones; change these counts when the content requires it.
- Define a baseline unit, normally 4 or 8 px, and derive vertical spacing from integer multiples of it.
- Give every major module a declared start line and span. Repeated modules must share the same geometry.
- Align headings, copy, imagery, metadata, dividers, navigation, and controls to common grid lines.
- Keep text line length roughly 45–75 characters for sustained reading.
- Expose a development-only overlay using the exact production grid variables. A useful trigger is a `data-grid` attribute or keyboard-toggleable debug class.
- At breakpoints, recompose: declare new starts and spans. Do not merely shrink the desktop composition.

Prefer CSS Grid for page geometry and Flexbox for one-dimensional alignment within a grid cell. Avoid absolute positioning for primary layout.

## Typography

- Prefer Helvetica Neue when it is legitimately available; otherwise use a carefully chosen neo-grotesk such as Inter, Arial, or a project-supplied equivalent.
- Use no more typefaces or weights than the hierarchy needs. A single family often suffices.
- Define semantic tokens for navigation, metadata, section labels, headlines, metrics, controls, figure annotations, map labels, body copy, and footer text before styling individual components. Reuse these roles across selectors and breakpoints.
- Set body copy for calm reading and use strong size, weight, and spatial contrast for headings.
- Default to sentence case and flush-left/ragged-right setting. Reserve uppercase for short functional labels.
- Tune line height, tracking, and measure together. Never compress text merely to force a grid fit.
- Use tabular numerals where columns of numbers must align.
- Do not use the grid to justify tiny functional text. Navigation, kickers, methods labels, dataset links, annotations, and footers must remain comfortably readable at 320–430 CSS px and 200% zoom.
- Inspect large bold metrics at representative phone device-pixel ratios. Negative tracking can create apparent glyph collisions even when element boxes do not overlap; prefer natural spacing when in doubt.

## Composition, color, and imagery

- Create tension with asymmetric but balanced spans, scale shifts, cropping, and negative space.
- Keep the palette small: usually a neutral field, high-contrast text, and one functional accent. Assign each color a semantic role.
- Define accents by meaning, not component. If red denotes primary findings, expose one shared metric-value role; keep data-series colors distinct from interface, status, and identity roles.
- Meet WCAG contrast requirements even when historic references do not.
- Prefer relevant black-and-white or restrained-color photography over decorative illustration. Preserve focal meaning across responsive crops.
- Use rules, circles, blocks, and other geometry only when they organize, label, sequence, or explain.
- Let content remain legible and operable without motion.

## Contemporary web translation

Current Swiss-influenced sites commonly retain explicit grids, assertive sans-serif type, generous whitespace, restrained palettes, and understated transitions. Study examples to understand systems across multiple pages, not to copy a hero layout. Useful discovery venues include Swiss cultural institutions, design studios, SiteInspire’s typographic/grid collections, and curated Swiss-style galleries. Verify that a live example actually demonstrates the principles above before treating it as precedent.
