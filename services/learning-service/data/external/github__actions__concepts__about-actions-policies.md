<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/concepts/about-actions-policies -->
# About Actions policies

Govern how GitHub Actions workflows run within your repository, organization, or enterprise.

## About Actions policies

Actions policies let you govern how GitHub Actions workflows run. You can configure them in the **Policies** section of your GitHub Actions settings (separate from the **General** settings).

Actions policies are available at the enterprise, organization, and repository levels. They currently contain one type of policy: workflow execution protections. GitHub plans to add more policies over time.

## About workflow execution protections

 These protections can disrupt several real-world attack patterns:

* **Poisoned pipeline execution from pull requests.** Restrict or prohibit `pull_request_target`, including in public repositories where it is most often exploited.
* **Manual-trigger abuse.** Limit `workflow_dispatch` so untrusted identities cannot start workflows.
* **Untrusted-actor execution.** Block low-trust identities from triggering workflows entirely.
* **Misconfiguration exploitation.** Apply central policy that overrides any single misconfigured workflow file.

When enforced, disallowed workflow runs will fail with an error. For example:

``` text
Event 'workflow_dispatch' is not allowed to trigger Actions workflows. Workflow file: '.github/workflows/0-welcome.yml'.
```

> [!NOTE]

### Available rules

* **Actor rules** control who can trigger workflows, including individual users, repository roles, GitHub, GitHub, and GitHub. By default, every user with write access to a repository can trigger workflows. Actor rules let you separate who contributes code from who runs your CI, so you can grant a contributor write access without granting them the ability to execute workflows.
* **Event rules** control which events are permitted, such as `push`, `pull_request`, `pull_request_target`, and `workflow_dispatch`.

GitHub plans to add more rules over time.

## Next steps

To configure workflow execution protections, see AUTOTITLE.

To manage policies programmatically, see AUTOTITLE.
