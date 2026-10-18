<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/tutorials/migrate-to-github-actions/automated-migrations/use-github-actions-importer -->
# Automating migration with GitHub Actions Importer

Use GitHub to plan and automate your migration to GitHub Actions.

## About GitHub

You can use GitHub to plan and automatically migrate your CI/CD supported pipelines to GitHub Actions.

GitHub is distributed as a Docker container, and uses a GitHub CLI extension to interact with the container.

Any workflow that is converted by the GitHub should be inspected for correctness before using it as a production workload. The goal is to achieve an 80% conversion rate for every workflow, however, the actual conversion rate will depend on the makeup of each individual pipeline that is converted.

## Supported CI platforms

You can use GitHub to migrate from the following platforms:

* Azure DevOps
* Bamboo
* Bitbucket Pipelines
* CircleCI
* GitLab (both cloud and self-hosted)
* Jenkins
* Travis CI

## Prerequisites

GitHub has the following requirements:

### Installing the GitHub CLI extension

### Updating the GitHub CLI

To ensure you're running the latest version of GitHub, you should regularly run the `update` command:

```bash
gh actions-importer update
```

### Authenticating at the command line

You must configure credentials that allow GitHub to communicate with GitHub and your current CI server. You can configure these credentials using environment variables or a `.env.local` file. The environment variables can be configured in an interactive prompt, by running the following command:

```bash
gh actions-importer configure
```

## Using the GitHub CLI

Use the subcommands of `gh actions-importer` to begin your migration to GitHub Actions, including `audit`, `forecast`, `dry-run`, and `migrate`.

### Auditing your existing CI pipelines

The `audit` subcommand can be used to plan your CI/CD migration by analyzing your current CI/CD footprint. This analysis can be used to plan a timeline for migrating to GitHub Actions.

To run an audit, use the following command to determine your available options:

```bash
$ gh actions-importer audit -h
Description:
  Plan your CI/CD migration by analyzing your current CI/CD footprint.

[...]

Commands:
  azure-devops  An audit will output a list of data used in an Azure DevOps instance.
  bamboo        An audit will output a list of data used in a Bamboo instance.
  circle-ci     An audit will output a list of data used in a CircleCI instance.
  gitlab        An audit will output a list of data used in a GitLab instance.
  jenkins       An audit will output a list of data used in a Jenkins instance.
  travis-ci     An audit will output a list of data used in a Travis CI instance.
```

### Forecasting usage

The `forecast` subcommand reviews historical pipeline usage to create a forecast of GitHub Actions usage.

To run a forecast, use the following command to determine your available options:

```bash
$ gh actions-importer forecast -h
Description:
  Forecasts GitHub Actions usage from historical pipeline utilization.

[...]

Commands:
  azure-devops  Forecasts GitHub Actions usage from historical Azure DevOps pipeline utilization.
  bamboo        Forecasts GitHub Actions usage from historical Bamboo pipeline utilization.
  jenkins       Forecasts GitHub Actions usage from historical Jenkins pipeline utilization.
  gitlab        Forecasts GitHub Actions usage from historical GitLab pipeline utilization.
  circle-ci     Forecasts GitHub Actions usage from historical CircleCI pipeline utilization.
  travis-ci     Forecasts GitHub Actions usage from historical Travis CI pipeline utilization.
  github        Forecasts GitHub Actions usage from historical GitHub pipeline utilization.
```

### Testing the migration process

The `dry-run` subcommand can be used to convert a pipeline to its GitHub Actions equivalent, and then write the workflow to your local filesystem.

To perform a dry run, use the following command to determine your available options:

```bash
$ gh actions-importer dry-run -h
Description:
  Convert a pipeline to a GitHub Actions workflow and output its yaml file.

[...]

Commands:
  azure-devops  Convert an Azure DevOps pipeline to a GitHub Actions workflow and output its yaml file.
  bamboo        Convert a Bamboo pipeline to GitHub Actions workflows and output its yaml file.
  circle-ci     Convert a CircleCI pipeline to GitHub Actions workflows and output the yaml file(s).
  gitlab        Convert a GitLab pipeline to a GitHub Actions workflow and output the yaml file.
  jenkins       Convert a Jenkins job to a GitHub Actions workflow and output its yaml file.
  travis-ci     Convert a Travis CI pipeline to a GitHub Actions workflow and output its yaml file.
```

### Migrating a pipeline to GitHub Actions

The `migrate` subcommand can be used to convert a pipeline to its GitHub Actions equivalent and then create a pull request with the contents.

To run a migration, use the following command to determine your available options:

```bash
$ gh actions-importer migrate -h
Description:
  Convert a pipeline to a GitHub Actions workflow and open a pull request with the changes.

[...]

Commands:
  azure-devops  Convert an Azure DevOps pipeline to a GitHub Actions workflow and open a pull request with the changes.
  bamboo        Convert a Bamboo pipeline to GitHub Actions workflows and open a pull request with the changes.
  circle-ci     Convert a CircleCI pipeline to GitHub Actions workflows and open a pull request with the changes.
  gitlab        Convert a GitLab pipeline to a GitHub Actions workflow and open a pull request with the changes.
  jenkins       Convert a Jenkins job to a GitHub Actions workflow and open a pull request with the changes.
  travis-ci     Convert a Travis CI pipeline to a GitHub Actions workflow and open a pull request with the changes.
```

## Performing self-serve migrations using IssueOps

You can use GitHub Actions and GitHub to run CLI commands for GitHub. This allows you to migrate your CI/CD workflows without installing software on your local machine. This approach is especially useful for organizations that want to enable self-service migrations to GitHub Actions. Once IssueOps is configured, users can open an issue with the relevant template to migrate pipelines to GitHub Actions.

For more information about setting up self-serve migrations with IssueOps, see the `actions/importer-issue-ops` template repository.

## Using the GitHub labs repository

The GitHub labs repository contains platform-specific learning paths that teach you how to use GitHub and how to approach migrations to GitHub Actions. You can use this repository to learn how to use GitHub to help plan, forecast, and automate your migration to GitHub Actions.

To learn more, see the GitHub Actions Importer labs repository.

## Legal notice
