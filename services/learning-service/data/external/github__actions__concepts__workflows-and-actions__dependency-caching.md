<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/concepts/workflows-and-actions/dependency-caching -->
# Dependency caching

Learn about dependency caching for workflow speed and efficiency.

## About workflow dependency caching

Workflow runs often reuse the same outputs or downloaded dependencies from one run to another. For example, package and dependency management tools such as Maven, Gradle, npm, and Yarn keep a local cache of downloaded dependencies.

 Jobs on GitHub-hosted runners start in a clean runner image and must download dependencies each time, causing increased network utilization, longer runtime, and increased cost. To help speed up the time it takes to recreate files like dependencies, GitHub can cache files you frequently use in workflows.

> [!NOTE]
> When using self-hosted runners, caches from workflow runs are stored on GitHub-owned cloud storage. A customer-owned storage solution is only available with GitHub Enterprise Server.

For more information on workflow run artifacts, see AUTOTITLE.

## Cache security

Caches are shared based on the branch or tag a workflow run uses, not on the identity of the workflow or job. See AUTOTITLE and the `GITHUB_REF` for the branch used for various workflow triggers. Any run that can read a cache restores its contents as-is, so you should treat restored files as untrusted input and never store secrets or other sensitive data in a cache.

Untrusted workflows can read sensitive cache contents, such as when a `pull_request` from a fork restores a cache. Poisoned caches can lead to code execution in trusted workflows. To limit the risk of cache poisoning, GitHub gives workflows that run in response to low-trust triggers read-only access to caches in the default branch's scope. A workflow or job can override this read-only restriction by explicitly declaring a write-capable `cache-mode`, which reintroduces the cache-poisoning risk for that workflow.

For the trusted-versus-low-trust trigger breakdown and default cache behavior, see AUTOTITLE. For cache-specific security guidance, see AUTOTITLE.

## Next steps

To implement dependency caching in your workflows, see AUTOTITLE.
