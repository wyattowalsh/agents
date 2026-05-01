# LCP Fixes

## Resource Load Delay

- Ensure the LCP resource is present in initial HTML.
- Do not lazy-load the LCP image.
- Add `fetchpriority="high"` to the LCP image when appropriate.
- Use preload for resources not otherwise discoverable early.

## Element Render Delay

- Inline critical CSS and defer non-critical CSS.
- Defer or async non-critical scripts.
- Break up long tasks before LCP.
- Use server rendering when client rendering hides the LCP element until hydration.

## Resource Load Duration

- Serve responsive images in modern formats.
- Use a CDN and cache effectively.
- Reduce competing critical-path resources.

## TTFB

- Remove redirects.
- Cache HTML at the edge when safe.
- Optimize origin work and database access.
- Preserve back/forward cache eligibility.
