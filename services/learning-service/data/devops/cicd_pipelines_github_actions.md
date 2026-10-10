# CI/CD Automation: GitHub Actions Pipelines and Progressive Delivery

## Continuous Integration vs Continuous Delivery
- **Continuous Integration (CI)**: The engineering practice of automatically integrating code changes into a shared repository multiple times per day. Every commit triggers automated build compilation, static analysis (ESLint, SonarQube), security vulnerability scanning (Trivy, Snyk), and unit/integration test suites.
- **Continuous Delivery (CD)**: Automatically provisions environments and packages deployable artifacts (Docker images, Helm charts, serverless bundles) so that any validated commit can be promoted to production with a single click.
- **Continuous Deployment**: Eliminates human approval gates entirely; any commit passing all CI stages deploys to production automatically.

## GitHub Actions Architecture
- **Workflows (`.github/workflows/*.yml`)**: Automated declarative procedures triggered by Git events (`push`, `pull_request`, `release`, `schedule`).
- **Jobs**: Composed of sequential steps executed on the same virtual runner (Ubuntu, macOS, Windows). Jobs run in parallel by default unless explicit dependency graphs (`needs: [lint, test]`) are declared.
- **Actions**: Reusable components executing specific tasks (e.g., `actions/checkout@v4`, `actions/setup-node@v4`, `docker/build-push-action@v5`).

## Progressive Deployment Strategies
1. **Rolling Deployment**:
   - Replaces old pod versions with new versions incrementally until 100% of the fleet runs the updated code.
   - *Advantage*: No extra hardware required.
   - *Drawback*: During deployment, both old and new versions run simultaneously, requiring strict database backward compatibility.

2. **Blue-Green Deployment**:
   - Maintains two identical production environments: Blue (active live traffic) and Green (idle staging environment running new release).
   - Once Green passes end-to-end smoke tests, the load balancer switches 100% of traffic from Blue to Green instantaneously.
   - *Advantage*: Zero downtime and instant, reliable rollback.

3. **Canary Release**:
   - Routes a tiny fraction of live user traffic (e.g. 5%) to the new deployment while 95% remains on the stable baseline.
   - Automated monitoring monitors error rates (HTTP 5xx), latency, and exception logs. If metrics remain healthy over 15 minutes, traffic increases progressively (25%, 50%, 100%).
