# Modern Frontend Rendering Patterns: SSR, SSG, ISR, and React Server Components

## Evolution of Web Rendering
The trade-offs of modern web rendering center around three competing dimensions: Time to First Byte (TTFB), First Contentful Paint (FCP), and client CPU hydration cost.

## Core Rendering Paradigms
1. **Client-Side Rendering (CSR)**:
   - The browser downloads an empty HTML shell (`<div id="root"></div>`) and a large JavaScript bundle. The browser's JS engine fetches data and mounts the DOM tree.
   - *Drawback*: Poor SEO and slow initial load on low-power mobile hardware.

2. **Static Site Generation (SSG)**:
   - HTML is compiled ahead-of-time during CI/CD build execution.
   - Pages are cached and served globally across Content Delivery Networks (CDNs) in < 50ms TTFB.
   - *Drawback*: Rebuilding large e-commerce catalogs with 50,000 product pages can take hours on build servers.

3. **Server-Side Rendering (SSR)**:
   - HTML is dynamically generated on each incoming HTTP request by a Node.js or Edge runtime worker.
   - *Advantage*: Guarantees real-time data freshness and optimal SEO.
   - *Drawback*: Server CPU overhead and susceptibility to high TTFB under database load.

4. **Incremental Static Regeneration (ISR)**:
   - Combines the global CDN speed of SSG with background revalidation.
   - Pages are statically cached. When a request arrives after `revalidate = 60` seconds, the stale page is served instantly, while a background server worker regenerates the page and updates the CDN cache (Stale-While-Revalidate pattern).

5. **React Server Components (RSC)**:
   - Server Components execute strictly on the server and are serialized into a binary stream protocol rather than bundled into client JavaScript.
   - Direct database and filesystem access with **zero bundle size overhead** on the client.
   - Interactive components are explicitly declared with `'use client'` directives, minimizing client-side hydration bloat.
