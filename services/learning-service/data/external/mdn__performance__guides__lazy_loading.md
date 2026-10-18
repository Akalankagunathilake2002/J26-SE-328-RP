<!-- role: Full-Stack Developer -->
<!-- topic: Web Performance -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Lazy_loading -->
# Lazy loading

**Lazy loading** is a strategy to identify resources as non-blocking (non-critical) and load these only when needed. It's a way to shorten the length of the critical rendering path, which translates into reduced page load times.

Lazy loading can occur on different moments in the application, but it typically happens on some user interactions such as scrolling and navigation.

## Overview

As the web has evolved, we have come to see huge increases in the number and size of assets sent to users.
Between 2011 and 2019, the median resource weight increased from **\~100KB** to **\~400KB** for desktop and **\~50KB** to **\~350KB** for mobile. While Image size has increased from **\~250KB** to **\~900KB** on desktop and **\~100KB** to **\~850KB** on mobile.

One of the methods we can use to tackle this problem is to shorten the Critical Rendering Path length by lazy loading resources that are not critical for the first render to happen.
A practical example would be when you land on the home page of an e-commerce site with a link to a cart page/section, and none of the cart page's resources (such as JavaScript, CSS, and images) are downloaded **until** you navigate there.

## Strategies

Lazy loading can be applied to multiple resources and through multiple strategies.

### General

#### Code splitting

JavaScript, CSS and HTML can be split into smaller chunks. This enables sending the minimal code required to provide value upfront, improving page-load times. The rest can be loaded on demand.

- Entry point splitting: separates code by entry point(s) in the app
- Dynamic splitting: separates code where dynamic import() expressions are used

### JavaScript

#### Script type module

Any script tag with `type="module"` is treated as a JavaScript module and is deferred by default.

### CSS

By default, CSS is treated as a render blocking resource, so the browser won't render any processed content until the CSSOM is constructed. CSS must be thin, delivered as quickly as possible, and the usage media types and queries are advised to unblock rendering.

```html

```

It is possible to perform some CSS optimizations to achieve that.

### Fonts

By default, font requests are delayed until the render tree is constructed, which can result in delayed text rendering.

It is possible to override the default behavior and preload web font resources using ``, the CSS `font-display` descriptor, and the Font Loading API.

See also: Element Link.

### Images, iframes, videos and audio

Very often, webpages contain many images that contribute to data-usage and how fast a page can load. Most of those images are off-screen (non-critical), requiring a user interaction, like scrolling, in order to view them. Similarly, many iframes, videos, and audio may be offscreen initially.

#### Loading attribute

The `loading` attribute on an img, iframe, video, or audio element can be used to instruct the browser to defer loading of linked resources when elements are off-screen until the user scrolls near them.
This allows non-critical resources to load only if needed, potentially speeding up initial page loads and reducing network usage.

```html

```

The `load` event fires when the eagerly-loaded content has all been loaded. At that time, it's entirely possible (or even likely) that there may be lazily-loaded images, iframes, videos, or audio within the visual viewport that haven't yet loaded.

You can determine if a given image has finished loading by examining the value of its Boolean complete property.

#### Intersection Observer API

Intersection Observers allow the user to know when an observed element enters or exits the browser's viewport.

#### Event handlers

When browser compatibility is crucial, there are a few options:

- polyfill intersection observer
- fallback to scroll, resize or orientation change event handlers to determine if a specific element is in viewport
