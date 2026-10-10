# Web Vitals Optimization and Frontend Performance Engineering

## Google Core Web Vitals
Core Web Vitals represent user-centric performance metrics governing user experience and search engine ranking:
1. **Largest Contentful Paint (LCP)**:
   - Measures perceived loading speed. Marks the point in the page load timeline when the main content (hero image, heading text block, video poster) has likely rendered.
   - *Target*: $\le 2.5\text{ seconds}$.
   - *Optimization*: Preload hero images (`<link rel="preload" as="image">`), use modern image formats (AVIF/WebP), optimize server TTFB, and eliminate render-blocking CSS/fonts.

2. **Interaction to Next Paint (INP)**:
   - Replaced First Input Delay (FID). Assesses page responsiveness by measuring the latency of all user interactions (clicks, key presses, taps) and reporting the worst-case interaction latency.
   - *Target*: $\le 200\text{ ms}$.
   - *Optimization*: Break up long JavaScript tasks (> 50ms) using `requestIdleCallback`, `scheduler.yield()`, or Web Workers; avoid heavy synchronous React state updates during high-frequency typing/scrolling events (`useDeferredValue`, `useTransition`).

3. **Cumulative Layout Shift (CLS)**:
   - Measures visual stability. Quantifies unexpected layout shifts occurring when visible page elements shift position without user interaction.
   - *Target*: $\le 0.1$.
   - *Optimization*: Always include explicit `width` and `height` dimensions on images and videos; reserve aspect-ratio placeholders for dynamic ads and embeds; avoid inserting dynamic banners above existing rendered content.

## Modern Code Splitting and Asset Loading Strategies
- **Dynamic Imports (`next/dynamic` / `React.lazy`)**: Defers downloading heavy interactive modules (e.g. Monaco code editors, charting engines, rich text editors) until the user navigates to the specific tab.
- **Critical CSS Inlining**: Inlines above-the-fold styles directly inside `<head>`, while deferring secondary stylesheet loading asynchronously.
- **Resource Hints**: `dns-prefetch`, `preconnect`, and `preload` pre-negotiate network connections with critical third-party API and CDN origins.
