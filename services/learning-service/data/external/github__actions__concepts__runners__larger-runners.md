<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/concepts/runners/larger-runners -->
# Larger runners

Organize and govern your workflows with GitHub-hosted larger runners using runner groups, concurrency policies, and granular access controls.

To learn about larger runners, see the GitHub documentation.

## About GitHub

## What you can do with larger runners

All GitHub support the following capabilities:

* **Runner groups**: Organize runners and control which repositories can use them
* **Autoscaling**: Scale runners up or down based on workload demand
* **Concurrency controls**: Limit how many jobs can run at the same time

The following capabilities are available only on Linux and Windows runners:

* **Static IP addresses**: Assign static IP addresses from a specific range to runners, allowing you to configure firewall allowlists.
* **Custom images**: Use custom runner images to pre-install dependencies and reduce setup time.
* **Azure private networking**: Connect your runners to Azure private networks.

## About GitHub for GitHub default setup

Consider configuring GitHub for GitHub default setup if:

* Your scans with standard GitHub-hosted runners are taking too long.
* Your scans with standard GitHub-hosted runners are returning memory or disk errors.
* You want to customize aspects of your GitHub runner, such as the runner size, runner image, and job concurrency, without using self-hosted runners.

For more information on configuring GitHub for GitHub default setup, see AUTOTITLE.

## Billing

> [!NOTE]
> GitHubs are not eligible for the use of included minutes on private repositories. For both private and public repositories, when GitHub are in use, they will always be billed at the per-minute rate.

Compared to standard GitHub-hosted runners, GitHub are billed differently.  For more information, see AUTOTITLE.

## Next steps

To start using larger runners, see AUTOTITLE.

To find reference information about using GitHub, see AUTOTITLE.
