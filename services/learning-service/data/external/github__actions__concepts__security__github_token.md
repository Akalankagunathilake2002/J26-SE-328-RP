<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/concepts/security/github_token -->
# GITHUB_TOKEN

Learn what `GITHUB_TOKEN` is, how it works, and why it matters for secure automation in GitHub Actions workflows.

## About the `GITHUB_TOKEN`

At the start of each workflow job, GitHub automatically creates a unique `GITHUB_TOKEN` secret to use in your workflow. You can use the `GITHUB_TOKEN` to authenticate in the workflow job.

When you enable GitHub Actions, GitHub installs a GitHub on your repository. The `GITHUB_TOKEN` secret is a GitHub installation access token. You can use the installation access token to authenticate on behalf of the GitHub installed on your repository. The token's permissions are limited to the repository that contains your workflow. For more information, see AUTOTITLE.

Before each job begins, GitHub fetches an installation access token for the job. The `GITHUB_TOKEN` expires when the job finishes or after its effective maximum lifetime.

The effective maximum lifetime of the token depends on the type of runner:

* **GitHub-hosted runners** The maximum job execution time is 6 hours, so the `GITHUB_TOKEN` can live for a maximum of 6 hours.
* **Self-hosted runners** The maximum job execution time is 5 days. However, because the `GITHUB_TOKEN` is an installation access token, it can only be refreshed for up to 24 hours. If your job runs longer than 24 hours, use a GitHub or other authentication method instead.

The token is also available in the `github.token` context. For more information, see AUTOTITLE.

## When `GITHUB_TOKEN` triggers workflow runs

> [!NOTE]
> If you need workflow runs from workflow-created pull requests to execute without requiring approval, use a GitHub installation access token or a GitHub instead of `GITHUB_TOKEN` when creating or updating the pull request.

## Next steps

* AUTOTITLE
* AUTOTITLE
