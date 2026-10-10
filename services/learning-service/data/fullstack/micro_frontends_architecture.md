# Micro-Frontends Architecture: Module Federation and Independent Deployments

## Architectural Motivation
As engineering organizations scale to dozens of cross-functional feature teams, a monolithic frontend SPA creates severe bottlenecks:
- Long CI/CD build and testing cycles (> 45 minutes).
- High risk of unintended regression across unrelated product modules.
- Forced monolithic release coordination and rigid technology lock-in.

Micro-frontends decompose web applications into autonomous, independently deployable client applications owned by dedicated domain teams (e.g., Search, Checkout, User Settings).

## Composition Techniques
1. **Webpack 5 / Vite Module Federation**:
   - Allows a Host container application to dynamically load remote JavaScript bundles at runtime over HTTP.
   - Remote components are imported just like native ESM modules:
     ```javascript
     const CheckoutModule = React.lazy(() => import('checkoutApp/PaymentButton'));
     ```
   - **Shared Dependencies**: Configures singleton sharing for core libraries (`react`, `react-dom`, `@tanstack/react-query`) to prevent loading duplicate runtime copies into the browser.

2. **Web Components (Custom Elements)**:
   - Framework-agnostic composition leveraging standard browser APIs (`customElements.define('user-profile-widget', ProfileWidget)`).
   - Encapsulates CSS styling and DOM trees via Shadow DOM, preventing CSS class collisions across teams.

3. **Iframe Isolation**:
   - Strongest security and runtime fault isolation.
   - *Trade-off*: Clunky cross-frame navigation, difficulty sharing authentication state, and poor responsive styling coordination.

## Cross-Application Communication
- **Event-Driven Custom Events**: Host and remotes communicate via loosely-coupled browser events (`window.dispatchEvent(new CustomEvent('auth:token-refreshed', { detail: token }))`).
- **Shared Event Bus**: Lightweight Pub/Sub event emitter shared across modules without direct component coupling.
