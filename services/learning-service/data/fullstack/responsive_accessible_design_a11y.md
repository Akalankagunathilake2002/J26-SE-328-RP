# Web Accessibility (a11y) and Inclusive Design Engineering

## Why Web Accessibility Matters
Web accessibility ensures that websites and interactive web applications are usable by everyone, including people with visual, auditory, motor, or cognitive disabilities. Meeting WCAG 2.1 AA (Web Content Accessibility Guidelines) is both an ethical responsibility and a strict legal requirement for modern software platforms.

## Core WCAG Principles (POUR)
1. **Perceivable**: Information and user interface components must be presentable to users in ways they can perceive.
   - Text alternatives for non-text content (`alt` attributes on `<img>`, transcripts for video/audio).
   - High color contrast ratio: Minimum 4.5:1 for normal text, 3:1 for large text.
2. **Operable**: User interface components and navigation must be operable.
   - Keyboard accessibility: Every action achievable with a mouse must be executable solely via `Tab`, `Enter`, `Space`, and arrow keys.
   - Focus management: Visual focus indicators (`:focus-visible`) must never be suppressed with `outline: none` without providing an accessible custom alternative.
   - Focus traps in modals: When a dialog opens, focus must be trapped within the modal and restored to the trigger element when closed via `Escape`.
3. **Understandable**: Information and operation of the user interface must be understandable.
   - Consistent navigation, clear input error messages, and form labels explicitly associated with inputs via `htmlFor` / `id`.
4. **Robust**: Content must be robust enough that it can be interpreted reliably by a wide variety of user agents, including assistive screen readers (NVDA, VoiceOver, JAWS).

## Semantic HTML vs WAI-ARIA
- **First Rule of ARIA**: Use native semantic HTML elements (`<button>`, `<nav>`, `<main>`, `<dialog>`, `<article>`) instead of custom `<div>` tags before resorting to ARIA.
- **ARIA Attributes**: Used only when native HTML does not provide equivalent semantics:
  - `aria-expanded="true"` for collapsible accordions.
  - `aria-live="polite"` for dynamic content regions (e.g. AI interviewer status or toast notifications) so screen readers announce changes without interrupting speech.
  - `aria-describedby` to associate validation error messages with form inputs.
