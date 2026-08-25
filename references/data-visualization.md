# Charts, maps, and SVG interaction

Read this reference when a website contains scientific charts, geographic outlines, map labels, or animated SVG annotations.

## Horizontally scrollable charts

- Keep plots legible rather than compressing them below a useful width.
- When a chart scrolls horizontally, position axis titles relative to the visible viewport or omit them when redundant. Do not center a title inside an oversized SVG where it appears orphaned at a phone edge.
- Keep visible state clear and preserve enough context—units, active value, and scale—to interpret the current viewport.

## Touch and keyboard interaction

Hover must never be the only path to chart values. For time selection or similar ordered data, provide a direct touch control such as a range input, visible selected state, previous/next controls, keyboard operation, and accessible value text. Keep all alternatives synchronized with the same data state.

Test dragging, tapping, previous/next actions, focus order, arrow keys, value announcements, and behavior at the ends of the range. Tooltips must not obscure the active mark or become the only carrier of essential information.

## Geographic data and labels

- Prefer authoritative open vector data. Record its publisher, dataset/release, retrieval date, and license.
- Retain enough vertices for the rendered size and use topology-preserving simplification when browser performance requires it. Inspect the simplified outline at its largest and smallest rendered sizes.
- Review city labels and leader lines visually against the actual outline at every breakpoint. Bounding-box collision tests are useful but not sufficient.
- Use consistent leader elbow geometry. Keep labels outside the boundary where the design intends, avoid crossings, and verify that anchors still point to the correct places after responsive transformations.

## SVG reveal motion

- Give motion a communicative sequence. Reveal annual marks chronologically and comparative distributions in a declared series order; do not animate merely to decorate.
- Start staggered annotation motion only when the containing section enters the viewport.
- Use a short, shared duration/easing/delay system and stagger only enough to clarify sequence.
- Reveal once; do not replay on ordinary scrolling.
- When a user changes the selected dataset, season, or equivalent state, restart only the affected data-dependent figure animation by remounting or explicitly resetting it. Keep unrelated figures and page reveals stable.
- Keep annotations visible before JavaScript enhancement and reveal them immediately under `prefers-reduced-motion: reduce`.
- Verify rapid scrolling and slow script execution cannot strand marks in a hidden state.

Test animation state as well as final screenshots. Assert that the first and last chronological marks receive correctly ordered delays, an applicable dataset change restarts the intended figure, ordinary scrolling does not replay it, and reduced motion removes hidden, transformed, clipped, or dashed interim states.
