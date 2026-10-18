<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/tutorials/migrate-to-github-actions/automated-migrations/circleci-migration -->
# Migrating from CircleCI with GitHub Actions Importer

Learn how to use GitHub to automate the migration of your CircleCI pipelines to GitHub Actions.

## About migrating from CircleCI with GitHub Actions Importer

The instructions below will guide you through configuring your environment to use GitHub to migrate CircleCI pipelines to GitHub Actions.

### Prerequisites

* A CircleCI account or organization with projects and pipelines that you want to convert to GitHub Actions workflows.
* Access to create a CircleCI personal API token for your account or organization.

### Limitations

There are some limitations when migrating from CircleCI to GitHub Actions with GitHub:

* Automatic caching in between jobs of different workflows is not supported.
* The `audit` command is only supported when you use a CircleCI organization account. The `dry-run` and `migrate` commands can be used with a CircleCI organization or user account.

#### Manual tasks

Certain CircleCI constructs must be migrated manually. These include:

* Contexts
* Project-level environment variables
* Unknown job properties
* Unknown orbs

## Installing the GitHub CLI extension

## Configuring credentials

The `configure` CLI command is used to set required credentials and options for GitHub when working with CircleCI and GitHub.

1. Create a GitHub . For more information, see AUTOTITLE.

   Your token must have the `repo` and `workflow` scopes.

   After creating the token, copy it and save it in a safe location for later use.
1. Create a CircleCI personal API token. For more information, see Managing API Tokens in the CircleCI documentation.

   After creating the token, copy it and save it in a safe location for later use.
1. In your terminal, run the GitHub `configure` CLI command:

   ```shell
   gh actions-importer configure
   ```

   The `configure` command will prompt you for the following information:

   * For "Which CI providers are you configuring?", use the arrow keys to select `CircleCI`, press Space to select it, then press Enter.
   * For "GitHub for GitHub", enter the value of the  that you created earlier, and press Enter.
   * For "Base url of the GitHub instance", enter the URL for GitHub, and press Enter.press Enter to accept the default value (`https://github.com`).
   * For "GitHub for CircleCI", enter the value for the CircleCI personal API token that you created earlier, and press Enter.
   * For "Base url of the CircleCI instance", press Enter to accept the default value (`https://circleci.com`).
   * For "CircleCI organization name", enter the name for your CircleCI organization, and press Enter.

   An example of the `configure` command is shown below:

   ```shell
   $ gh actions-importer configure
   ✔ Which CI providers are you configuring?: CircleCI
   Enter the following values (leave empty to omit):
   ✔ GitHub for GitHub: ***************
   ✔ Base url of the GitHub instance: https://github.com
   ✔ GitHub for CircleCI: ********************
   ✔ Base url of the CircleCI instance: https://circleci.com
   ✔ CircleCI organization name: mycircleciorganization
   Environment variables successfully updated.
   ```

1. In your terminal, run the GitHub `update` CLI command to connect to GitHub GitHub and ensure that the container image is updated to the latest version:

   ```shell
   gh actions-importer update
   ```

   The output of the command should be similar to below:

   ```shell
   Updating ghcr.io/actions-importer/cli:latest...
   ghcr.io/actions-importer/cli:latest up-to-date
   ```

## Perform an audit of CircleCI

You can use the `audit` command to get a high-level view of all projects in a CircleCI organization.

The `audit` command performs the following steps:

1. Fetches all of the projects defined in a CircleCI organization.
1. Converts each pipeline to its equivalent GitHub Actions workflow.
1. Generates a report that summarizes how complete and complex of a migration is possible with GitHub.

### Running the audit command

To perform an audit of a CircleCI organization, run the following command in your terminal:

```shell
gh actions-importer audit circle-ci --output-dir tmp/audit
```

### Inspecting the audit results

## Forecast potential GitHub Actions usage

You can use the `forecast` command to forecast potential GitHub Actions usage by computing metrics from completed pipeline runs in CircleCI.

### Running the forecast command

To perform a forecast of potential GitHub Actions usage, run the following command in your terminal. By default, GitHub includes the previous seven days in the forecast report.

```shell
gh actions-importer forecast circle-ci --output-dir tmp/forecast_reports
```

### Inspecting the forecast report

The `forecast_report.md` file in the specified output directory contains the results of the forecast.

Listed below are some key terms that can appear in the forecast report:

* The **job count** is the total number of completed jobs.
* The **pipeline count** is the number of unique pipelines used.
* **Execution time** describes the amount of time a runner spent on a job. This metric can be used to help plan for the cost of GitHub-hosted runners.

  This metric is correlated to how much you should expect to spend in GitHub Actions. This will vary depending on the hardware used for these minutes. You can use the GitHub Actions pricing calculator to estimate the costs.
* **Queue time** metrics describe the amount of time a job spent waiting for a runner to be available to execute it.
* **Concurrent jobs** metrics describe the amount of jobs running at any given time. This metric can be used to define the number of runners you should configure.

Additionally, these metrics are defined for each queue of runners in CircleCI. This is especially useful if there is a mix of hosted or self-hosted runners, or high or low spec machines, so you can see metrics specific to different types of runners.

## Perform a dry-run migration of a CircleCI pipeline

You can use the `dry-run` command to convert a CircleCI pipeline to an equivalent GitHub Actions workflow. A dry-run creates the output files in a specified directory, but does not open a pull request to migrate the pipeline.

To perform a dry run of migrating your CircleCI project to GitHub Actions, run the following command in your terminal, replacing `my-circle-ci-project` with the name of your CircleCI project.

```shell
gh actions-importer dry-run circle-ci --output-dir tmp/dry-run --circle-ci-project my-circle-ci-project
```

You can view the logs of the dry run and the converted workflow files in the specified output directory.

## Perform a production migration of a CircleCI pipeline

You can use the `migrate` command to convert a CircleCI pipeline and open a pull request with the equivalent GitHub Actions workflow.

### Running the migrate command

To migrate a CircleCI pipeline to GitHub Actions, run the following command in your terminal, replacing the `target-url` value with the URL for your GitHub repository, and `my-circle-ci-project` with the name of your CircleCI project.

```shell
gh actions-importer migrate circle-ci --target-url https://github.com/octo-org/octo-repo --output-dir tmp/migrate --circle-ci-project my-circle-ci-project
```

The command's output includes the URL to the pull request that adds the converted workflow to your repository. An example of a successful output is similar to the following:

```shell
$ gh actions-importer migrate circle-ci --target-url https://github.com/octo-org/octo-repo --output-dir tmp/migrate --circle-ci-project my-circle-ci-project
[2022-08-20 22:08:20] Logs: 'tmp/migrate/log/actions-importer-20220916-014033.log'
[2022-08-20 22:08:20] Pull request: 'https://github.com/octo-org/octo-repo/pull/1'
```

## Reference

This section contains reference information on environment variables, optional arguments, and supported syntax when using GitHub to migrate from CircleCI.

### Using environment variables

GitHub uses the following environment variables to connect to your CircleCI instance:

* `GITHUB_ACCESS_TOKEN`: The  used to create pull requests with a converted workflow (requires `repo` and `workflow` scopes).
* `GITHUB_INSTANCE_URL`: The URL to the target GitHub instance (for example, `https://github.com`).
* `CIRCLE_CI_ACCESS_TOKEN`: The CircleCI personal API token used to authenticate with your CircleCI instance.
* `CIRCLE_CI_INSTANCE_URL`: The URL to the CircleCI instance (for example, `https://circleci.com`). If the variable is left unset, `https://circleci.com` is used as the default value.
* `CIRCLE_CI_ORGANIZATION`: The organization name of your CircleCI instance.
* `CIRCLE_CI_PROVIDER`: The location where your pipeline's source file is stored (such as `github`). Currently, only GitHub is supported.
* `CIRCLE_CI_SOURCE_GITHUB_ACCESS_TOKEN` (Optional): The  used to authenticate with your source GitHub instance (requires `repo` scope). If not provided, the value of `GITHUB_ACCESS_TOKEN` is used instead.
* `CIRCLE_CI_SOURCE_GITHUB_INSTANCE_URL` (Optional): The URL to the source GitHub instance. If not provided, the value of `GITHUB_INSTANCE_URL` is used instead.

These environment variables can be specified in a `.env.local` file that is loaded by GitHub when it is run.

### Optional arguments

#### `--source-file-path`

You can use the `--source-file-path` argument with the `forecast`, `dry-run`, or `migrate` subcommands.

By default, GitHub fetches pipeline contents from source control. The `--source-file-path` argument tells GitHub to use the specified source file path instead.

For example:

```shell
gh actions-importer dry-run circle-ci --output-dir ./output/ --source-file-path ./path/to/.circleci/config.yml
```

If you would like to supply multiple source files when running the `forecast` subcommand, you can use pattern matching in the file path value. For example, `gh forecast --source-file-path ./tmp/previous_forecast/jobs/*.json` supplies GitHub with any source files that match the `./tmp/previous_forecast/jobs/*.json` file path.

#### `--config-file-path`

You can use the `--config-file-path` argument with the `audit`, `dry-run`, and `migrate` subcommands.

By default, GitHub fetches pipeline contents from source control. The `--config-file-path` argument tells GitHub to use the specified source files instead.

The `--config-file-path` argument can also be used to specify which repository a converted composite action should be migrated to.

##### Audit example

In this example, GitHub uses the specified YAML configuration file to perform an audit.

```bash
gh actions-importer audit circle-ci --output-dir ./output/ --config-file-path ./path/to/circle-ci/config.yml
```

To audit a CircleCI instance using a config file, the config file must be in the following format, and each `repository_slug` must be unique:

```yaml
source_files:
  - repository_slug: circle-org-name/circle-project-name
    path: path/to/.circleci/config.yml
  - repository_slug: circle-org-name/some-other-circle-project-name
    path: path/to/.circleci/config.yml
```

##### Dry run example

In this example, GitHub uses the specified YAML configuration file as the source file to perform a dry run.

The pipeline is selected by matching the `repository_slug` in the config file to the value of the `--circle-ci-organization` and `--circle-ci-project` options. The `path` is then used to pull the specified source file.

```bash
gh actions-importer dry-run circle-ci --circle-ci-project circle-org-name/circle-project-name --output-dir ./output/ --config-file-path ./path/to/circle-ci/config.yml
```

##### Specify the repository of converted composite actions

GitHub uses the YAML file provided to the `--config-file-path` argument to determine the repository that converted composite actions are migrated to.

To begin, you should run an audit without the `--config-file-path` argument:

```bash
gh actions-importer audit circle-ci --output-dir ./output/
```

The output of this command will contain a file named `config.yml` that contains a list of all the composite actions that were converted by GitHub. For example, the `config.yml` file may have the following contents:

```yaml
composite_actions:
  - name: my-composite-action.yml
    target_url: https://github.com/octo-org/octo-repo
    ref: main
```

You can use this file to specify which repository and ref a reusable workflow or composite action should be added to. You can then use the `--config-file-path` argument to provide the `config.yml` file to GitHub. For example, you can use this file when running a `migrate` command to open a pull request for each unique repository defined in the config file:

```bash
gh actions-importer migrate circle-ci --circle-ci-project my-project-name --output-dir output/ --config-file-path config.yml --target-url https://github.com/my-org/my-repo
```

#### `--include-from`

You can use the `--include-from` argument with the `audit` subcommand.

The `--include-from` argument specifies a file that contains a line-delimited list of repositories to include in the audit of a CircleCI organization. Any repositories that are not included in the file are excluded from the audit.

For example:

```bash
gh actions-importer audit circle-ci --output-dir ./output/ --include-from repositories.txt
```

The file supplied for this parameter must be a line-delimited list of repositories, for example:

```text
repository_one
repository_two
repository_three
```

### Supported syntax for CircleCI pipelines

The following table shows the type of properties that GitHub is currently able to convert.

| CircleCI Pipelines  | GitHub Actions                     |              Status |
| :------------------ | :--------------------------------- | :------------------ |
| cron triggers       | `on.schedule`    |           Supported |
| environment         | `env``jobs..env``jobs..steps.env`          |           Supported |
| executors           | `runs-on`                          |           Supported |
| jobs                | `jobs`                             |           Supported |
| job                 | `jobs.``jobs..name` |           Supported |
| matrix              | `jobs..strategy``jobs..strategy.matrix`    |           Supported |
| parameters          | `env``workflow-dispatch.inputs`  |           Supported |
| steps               | `jobs..steps`              |           Supported |
| when, unless        | `jobs..if`                 |           Supported |
| triggers            | `on`                               |           Supported |
| executors           | `container``services`     | Partially Supported |
| orbs                | `actions`                          | Partially Supported |
| executors           | `self hosted runners`              |         Unsupported |
| setup               | Not applicable                                       |         Unsupported |
| version             | Not applicable                                       |         Unsupported |

For more information about supported CircleCI concept and orb mappings, see the `github/gh-actions-importer` repository.

### Environment variable mapping

GitHub uses the mapping in the table below to convert default CircleCI environment variables to the closest equivalent in GitHub Actions.

| CircleCI                              | GitHub Actions                                 |
| :------------------------------------ | :--------------------------------------------- |
| `CI`                                  | `$CI`                                       |
| `CIRCLE_BRANCH`                       | `$`                         |
| `CIRCLE_JOB`                          | `$`                         |
| `CIRCLE_PR_NUMBER`                    | `$`                |
| `CIRCLE_PR_REPONAME`                  | `$`                  |
| `CIRCLE_PROJECT_REPONAME`             | `$`                  |
| `CIRCLE_SHA1`                         | `$`                         |
| `CIRCLE_TAG`                          | `$`                         |
| `CIRCLE_USERNAME`                     | `$`                        |
| `CIRCLE_WORKFLOW_ID`                  | `$`                  |
| `CIRCLE_WORKING_DIRECTORY`            | `$`                   |
| `>`                   | `$`                    |
| `>`               | `$`                  |
| `>`      | `$GITHUB_SERVER_URL/$GITHUB_REPOSITORY`                          |
| `>`         | `github`                                                         |
| `>`              | `$`                         |
| `>`           | `$`                         |
| `>`         | `$` |
| `>`    | `$` |

## Legal notice
