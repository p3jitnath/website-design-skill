# Production identity, fonts, social previews, and deployment

Read this reference when the site uses custom fonts, identity marks, Open Graph artwork, GitHub Pages or another subdirectory deployment, or when publishing is part of the request.

## Browser identity and production paths

- Set and verify the favicon, theme color, document title, and meta description.
- Confirm SVG and raster assets return correct MIME types.
- Resolve assets through the Vite base path so routes, fonts, metadata images, and downloads work beneath a GitHub Pages or other subdirectory prefix.
- Audit links by kind: in-page, internal route, local download, or external source. Preserve the current page for internal actions; if project policy opens external destinations separately, apply that behavior and safe `rel` values consistently.

## Font decisions and delivery

A declared family name is not proof of identical rendered glyphs across Linux, iOS, browsers, and social-card renderers.

- If exact rendering matters, bundle the actual permitted font file and verify it loads in both the website and preview renderer.
- Make font licensing an explicit decision. Do not redistribute proprietary Helvetica or Arial files. Do not add a copyleft font casually to an MIT-licensed repository. Inter under the SIL Open Font License is a suitable option when its design fits; include the license and preserve any user-requested system-font ordering.
- In production, verify the built font URL, response status, MIME type, computed family, fallback order, and subdirectory path. A successful local CSS parse is insufficient.

## Social preview workflow

- Render the final Open Graph image at 1200 × 630 and inspect the raster for fallback fonts, clipping, antialiasing, geometry, and perceived balance. Do not approve from SVG source alone.
- Obtain explicit user approval of the rendered preview before committing social artwork.
- Judge identity marks relationally against the wordmark, map or imagery, title, and whitespace. A mathematically valid mark may still dominate through perceived area.
- Where appropriate, carry meaningful report context—such as the authoritative map, station markers, restrained palette, and site hierarchy—rather than making a generic logo-and-title card.
- For generated marks, add geometric assertions. For a Swiss flag, verify that the cross and red square share a center and that the cross follows official arm proportions; also inspect the rendered result.

Open Graph consumers such as messaging clients may cache images aggressively. After an approved image changes, version the absolute image URL with a query parameter and verify the live URL returns the new raster and correct MIME type. A query version is not a separate asset and must not lead to duplicate raster files.

## Deployment gate

When publishing is in scope:

1. Run the local lint, tests, and production build.
2. Push only after required approvals, including social artwork approval.
3. Wait for CI and hosting deployment to finish.
4. Request the live URL and verify its HTTP response.
5. Confirm the deployed bundle contains the intended copy, styles, fonts, icons, metadata, and assets at their production paths.
6. Recheck the critical viewport matrix against the deployed site.
