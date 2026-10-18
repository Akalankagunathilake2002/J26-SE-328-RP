<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/concepts/billing-and-usage -->
# Billing and usage

There are usage limits for GitHub Actions workflows. Usage charges apply to repositories that go beyond the amount of free minutes and storage for a repository.

## About billing for GitHub Actions

 For more information, see AUTOTITLE.

GitHub Actions usage is free for GitHub Enterprise Server instances that use self-hosted runners. For more information, see AUTOTITLE.

## Availability

GitHub Actions is available on all GitHub products, but GitHub Actions is not available for private repositories owned by accounts using legacy per-repository plans.

## Usage limits and policy

There are several limits on GitHub Actions usage when using GitHub-hosted runners. See AUTOTITLE.

In addition to the usage limits, you must ensure that you use GitHub Actions within the GitHub Terms of Service. For more information on GitHub Actions-specific terms, see the GitHub Additional Product Terms.

## GitHub Actions usage metrics

Organization owners and users with the "View organization Actions metrics" permission can view GitHub Actions usage metrics for their organization. These metrics can help you understand how and where your Actions minutes are being used. For more information, see AUTOTITLE.

When you view usage metrics, it is important to remember that

## Billing for reusable workflows

If you reuse a workflow, billing is always associated with the caller workflow. Assignment of GitHub-hosted runners is always evaluated using only the caller's context. The caller cannot use GitHub-hosted runners from the called repository.

For more information see, AUTOTITLE.

## Next steps

You can manage your GitHub Actions usage and retention policies for your repository, organization, or enterprise account. For more information, see:
* AUTOTITLE
* AUTOTITLE
* AUTOTITLE
* AUTOTITLE
