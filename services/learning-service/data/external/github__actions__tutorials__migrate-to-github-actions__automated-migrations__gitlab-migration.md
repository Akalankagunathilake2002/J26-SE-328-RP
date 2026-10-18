<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/tutorials/migrate-to-github-actions/automated-migrations/gitlab-migration -->
# Migrating from GitLab with GitHub Actions Importer

Learn how to use GitHub to automate the migration of your GitLab pipelines to GitHub Actions.

## About migrating from GitLab with GitHub Actions Importer

The instructions below will guide you through configuring your environment to use GitHub to migrate GitLab pipelines to GitHub Actions.

### Prerequisites

* A GitLab account or organization with pipelines and jobs that you want to convert to GitHub Actions workflows.
* Access to create a GitLab GitHub for your account or organization.

### Limitations

There are some limitations on migrating processes automatically from GitLab pipelines to GitHub Actions with GitHub.

* Automatic caching in between jobs of different workflows is not supported.
* The `audit` command is only supported when using an organization account. However, the `dry-run` and `migrate` commands can be used with an organization or user account.

#### Manual tasks

Certain GitLab constructs must be migrated manually. These include:

* Masked project or group variable values
* Artifact reports

For more information on manual migrations, see AUTOTITLE.

## Installing the GitHub CLI extension

## Configuring credentials

The `configure` CLI command is used to set required credentials and options for GitHub when working with GitLab and GitHub.

1. Create a GitHub . For more information, see AUTOTITLE.

   Your token must have the `workflow` scope.

   After creating the token, copy it and save it in a safe location for later use.
1. Create a GitLab GitHub. For more information, see GitHub in the GitLab documentation.

   Your token must have the `read_api` scope.

   After creating the token, copy it and save it in a safe location for later use.
1. In your terminal, run the GitHub `configure` CLI command:

   ```shell
   gh actions-importer configure
   ```

   The `configure` command will prompt you for the following information:

   * For "Which CI providers are you configuring?", use the arrow keys to select `GitLab`, press Space to select it, then press Enter.
   * For "GitHub for GitHub", enter the value of the  that you created earlier, and press Enter.
   * For "Base url of the GitHub instance", enter the URL for GitHub, and press Enter.press Enter to accept the default value (`https://github.com`).
   * For "Private token for GitLab", enter the value for the GitLab GitHub that you created earlier, and press Enter.
   * For "Base url of the GitLab instance", enter the URL of your GitLab instance, and press Enter.

   An example of the output of the `configure` command is shown below.

   ```shell
   $ gh actions-importer configure
   ✔ Which CI providers are you configuring?: GitLab
   Enter the following values (leave empty to omit):
   ✔ GitHub for GitHub: ***************
   ✔ Base url of the GitHub instance: https://github.com
   ✔ Private token for GitLab: ***************
   ✔ Base url of the GitLab instance: http://localhost
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

## Perform an audit of GitLab

You can use the `audit` command to get a high-level view of all pipelines in a GitLab server.

The `audit` command performs the following steps:

1. Fetches all of the projects defined in a GitLab server.
1. Converts each pipeline to its equivalent GitHub Actions workflow.
1. Generates a report that summarizes how complete and complex of a migration is possible with GitHub.

### Prerequisites for the audit command

In order to use the `audit` command, you must have a GitHub configured with a GitLab organization account.

### Running the audit command

To perform an audit of a GitLab server, run the following command in your terminal, replacing `my-gitlab-namespace` with the namespace or group you are auditing:

```shell
gh actions-importer audit gitlab --output-dir tmp/audit --namespace my-gitlab-namespace
```

### Inspecting the audit results

## Forecast potential build runner usage

You can use the `forecast` command to forecast potential GitHub Actions usage by computing metrics from completed pipeline runs in your GitLab server.

### Running the forecast command

To perform a forecast of potential GitHub Actions usage, run the following command in your terminal, replacing `my-gitlab-namespace` with the namespace or group you are forecasting. By default, GitHub includes the previous seven days in the forecast report.

```shell
gh actions-importer forecast gitlab --output-dir tmp/forecast --namespace my-gitlab-namespace
```

### Forecasting an entire namespace

To forecast an entire namespace and all of its subgroups, you must specify each subgroup in the `--namespace` argument or `NAMESPACE` environment variable.

For example:

```shell
gh actions-importer forecast gitlab --namespace my-gitlab-namespace my-gitlab-namespace/subgroup-one my-gitlab-namespace/subgroup-two ...
```

### Inspecting the forecast report

The `forecast_report.md` file in the specified output directory contains the results of the forecast.

Listed below are some key terms that can appear in the forecast report:

* The **job count** is the total number of completed jobs.
* The **pipeline count** is the number of unique pipelines used.
* **Execution time** describes the amount of time a runner spent on a job. This metric can be used to help plan for the cost of GitHub-hosted runners.
  * This metric is correlated to how much you should expect to spend in GitHub Actions. This will vary depending on the hardware used for these minutes. You can use the GitHub Actions pricing calculator to estimate the costs.
* **Queue time** metrics describe the amount of time a job spent waiting for a runner to be available to execute it.
* **Concurrent jobs** metrics describe the amount of jobs running at any given time. This metric can be used to define the number of runners you should configure.

Additionally, these metrics are defined for each queue of runners in GitLab. This is especially useful if there is a mix of hosted or self-hosted runners, or high or low spec machines, so you can see metrics specific to different types of runners.

## Perform a dry-run migration of a GitLab pipeline

You can use the `dry-run` command to convert a GitLab pipeline to its equivalent GitHub Actions workflow.

### Running the dry-run command

You can use the `dry-run` command to convert a GitLab pipeline to an equivalent GitHub Actions workflow. A dry-run creates the output files in a specified directory, but does not open a pull request to migrate the pipeline.

To perform a dry run of migrating your GitLab pipelines to GitHub Actions, run the following command in your terminal, replacing `my-gitlab-project` with your GitLab project slug, and `my-gitlab-namespace` with the namespace or group (full group path for subgroups, e.g. `my-org/my-team`) you are performing a dry run for.

```shell
gh actions-importer dry-run gitlab --output-dir tmp/dry-run --namespace my-gitlab-namespace --project my-gitlab-project
```

### Inspecting the converted workflows

You can view the logs of the dry run and the converted workflow files in the specified output directory.

## Perform a production migration of a GitLab pipeline

You can use the `migrate` command to convert a GitLab pipeline and open a pull request with the equivalent GitHub Actions workflow.

### Running the migrate command

To migrate a GitLab pipeline to GitHub Actions, run the following command in your terminal, replacing the following values:

* `target-url` value with the URL for your GitHub repository
* `my-gitlab-project` with your GitLab project slug
* `my-gitlab-namespace` with the namespace or group you are migrating (full path for subgroups, e.g. `my-org/my-team`)

```shell
gh actions-importer migrate gitlab --target-url https://github.com/:owner/:repo --output-dir tmp/migrate --namespace my-gitlab-namespace --project my-gitlab-project
```

The command's output includes the URL to the pull request that adds the converted workflow to your repository. An example of a successful output is similar to the following:

```shell
$ gh actions-importer migrate gitlab --target-url https://github.com/octo-org/octo-repo --output-dir tmp/migrate --namespace octo-org --project monas-project
[2022-08-20 22:08:20] Logs: 'tmp/migrate/log/actions-importer-20220916-014033.log'
[2022-08-20 22:08:20] Pull request: 'https://github.com/octo-org/octo-repo/pull/1'
```

## Reference

This section contains reference information on environment variables, optional arguments, and supported syntax when using GitHub to migrate from GitLab.

### Using environment variables

GitHub uses the following environment variables to connect to your GitLab instance:

* `GITHUB_ACCESS_TOKEN`: The  used to create pull requests with a converted workflow (requires the `workflow` scope).
* `GITHUB_INSTANCE_URL`: The URL to the target GitHub instance (for example, `https://github.com`).
* `GITLAB_ACCESS_TOKEN`: The GitLab GitHub used to view GitLab resources.
* `GITLAB_INSTANCE_URL`: The URL of the GitLab instance.
* `NAMESPACE`: The namespaces or groups that contain the GitLab pipelines.

These environment variables can be specified in a `.env.local` file that is loaded by GitHub when it is run.

### Using optional arguments

#### `--source-file-path`

You can use the `--source-file-path` argument with the `forecast`, `dry-run`, or `migrate` subcommands.

By default, GitHub fetches pipeline contents from source control. The `--source-file-path` argument tells GitHub to use the specified source file path instead.

For example:

```shell
gh actions-importer dry-run gitlab --output-dir output/ --namespace my-gitlab-namespace --project my-gitlab-project --source-file-path path/to/.gitlab-ci.yml
```

If you would like to supply multiple source files when running the `forecast` subcommand, you can use pattern matching in the file path value. The following example supplies GitHub with any source files that match the `./tmp/previous_forecast/jobs/*.json` file path.

```shell
gh actions-importer forecast gitlab --output-dir output/ --namespace my-gitlab-namespace --project my-gitlab-project --source-file-path ./tmp/previous_forecast/jobs/*.json
```

#### `--config-file-path`

You can use the `--config-file-path` argument with the `audit`, `dry-run`, and `migrate` subcommands.

By default, GitHub fetches pipeline contents from source control. The `--config-file-path` argument tells GitHub to use the specified source files instead.

The `--config-file-path` argument can also be used to specify which repository a converted reusable workflow should be migrated to.

##### Audit example

In this example, GitHub uses the specified YAML configuration file to perform an audit.

```shell
gh actions-importer audit gitlab --output-dir path/to/output/ --namespace my-gitlab-namespace --config-file-path path/to/gitlab/config.yml
```

To audit a GitLab instance using a configuration file, the file must be in the following format, and each `repository_slug` value must be unique:

```yaml
source_files:
  - repository_slug: namespace/project-name
    path: path/to/.gitlab-ci.yml
  - repository_slug: namespace/some-other-project-name
    path: path/to/.gitlab-ci.yml
```

##### Dry run example

In this example, GitHub uses the specified YAML configuration file as the source file to perform a dry run.

The pipeline is selected by matching the `repository_slug` in the configuration file to the value of the `--namespace` and `--project` options. The `path` is then used to pull the specified source file.

```shell
gh actions-importer dry-run gitlab --namespace my-gitlab-namespace --project my-gitlab-project-name --output-dir ./output/ --config-file-path ./path/to/gitlab/config.yml
```

##### Specify the repository of converted reusable workflows

GitHub uses the YAML file provided to the `--config-file-path` argument to determine the repository that converted reusable workflows are migrated to.

To begin, you should run an audit without the `--config-file-path` argument:

```shell
gh actions-importer audit gitlab --output-dir ./output/
```

The output of this command will contain a file named `config.yml` that contains a list of all the composite actions that were converted by GitHub. For example, the `config.yml` file may have the following contents:

```yaml
reusable_workflows:
  - name: my-reusable-workflow.yml
    target_url: https://github.com/octo-org/octo-repo
    ref: main
```

You can use this file to specify which repository and ref a reusable workflow or composite action should be added to. You can then use the `--config-file-path` argument to provide the `config.yml` file to GitHub. For example, you can use this file when running a `migrate` command to open a pull request for each unique repository defined in the config file:

```shell
gh actions-importer migrate gitlab --project my-project-name --output-dir output/ --config-file-path config.yml --target-url https://github.com/my-org/my-repo
```

### Supported syntax for GitLab pipelines

The following table shows the type of properties GitHub is currently able to convert. For more details about how GitLab pipeline syntax aligns with GitHub Actions, see AUTOTITLE.

| GitLab Pipelines                        | GitHub Actions                  | Status                      |
| :-------------------------------------- | :------------------------------ | :-------------------------- |
| `after_script`                          | `jobs..steps`           |                   Supported |
| `auto_cancel_pending_pipelines`         | `concurrency`                   |                   Supported |
| `before_script`                         | `jobs..steps`           |                   Supported |
| `build_timeout` or `timeout`            | `jobs..timeout-minutes` |                   Supported |
| `default`                               |  Not applicable                 |                   Supported |
| `image`                                 | `jobs..container`       |                   Supported |
| `job`                                   | `jobs.`                 |                   Supported |
| `needs`                                 | `jobs..needs`           |                   Supported |
| `only_allow_merge_if_pipeline_succeeds` | `on.pull_request`               |                   Supported |
| `resource_group`                        | `jobs..concurrency`     |                   Supported |
| `schedule`                              | `on.schedule`                   |                   Supported |
| `script`                                | `jobs..steps`           |                   Supported |
| `stages`                                | `jobs`                          |                   Supported |
| `tags`                                  | `jobs..runs-on`         |                   Supported |
| `variables`                             | `env`, `jobs..env`      |                   Supported |
| Run pipelines for new commits           | `on.push`                       |                   Supported |
| Run pipelines manually                  | `on.workflow_dispatch`          |                   Supported |
| `environment`                           | `jobs..environment`     |         Partially supported |
| `include`                               | Files referenced in an `include` statement are merged into a single job graph before being transformed. |         Partially supported |
| `only` or `except`                      | `jobs..if`              |         Partially supported |
| `parallel`                              | `jobs..strategy`        |         Partially supported |
| `rules`                                 | `jobs..if`              |         Partially supported |
| `services`                              | `jobs..services`        |         Partially supported |
| `workflow`                              | `if`                            |         Partially supported |

For information about supported GitLab constructs, see the `github/gh-actions-importer` repository.

### Environment variables syntax

GitHub uses the mapping in the table below to convert default GitLab environment variables to the closest equivalent in GitHub Actions.

| GitLab                                     | GitHub Actions                                                                        |
| :-------------------------------------------- | :------------------------------------------------------------------------------------ |
| `CI_API_V4_URL`                               | `$`                                                               |
| `CI_BUILDS_DIR`                               | `$`                                                        |
| `CI_COMMIT_BRANCH`                            | `$`                                                                |
| `CI_COMMIT_REF_NAME`                          | `$`                                                                  |
| `CI_COMMIT_REF_SLUG`                          | `$`                                                                  |
| `CI_COMMIT_SHA`                               | `$`                                                                 |
| `CI_COMMIT_SHORT_SHA`                         | `$`                                                                 |
| `CI_COMMIT_TAG`                               | `$`                                                                 |
| `CI_JOB_ID`                                   | `$`                                                                 |
| `CI_JOB_MANUAL`                               | `$`                                   |
| `CI_JOB_NAME`                                 | `$`                                                                 |
| `CI_JOB_STATUS`                               | `$`                                                                   |
| `CI_JOB_URL`                                  | `$/$/actions/runs/$` |
| `CI_JOB_TOKEN`                                | `$`                                                                 |
| `CI_NODE_INDEX`                               | `$`                                                           |
| `CI_NODE_TOTAL`                               | `$`                                                           |
| `CI_PIPELINE_ID`                              | `$/$`                                      |
| `CI_PIPELINE_IID`                             | `$`                                                              |
| `CI_PIPELINE_SOURCE`                          | `$`                                                            |
| `CI_PIPELINE_TRIGGERED`                       | `$`                                                               |
| `CI_PIPELINE_URL`                             | `$/$/actions/runs/$` |
| `CI_PROJECT_DIR`                              | `$`                                                             |
| `CI_PROJECT_ID`                               | `$`                                                            |
| `CI_PROJECT_NAME`                             | `$`                                                 |
| `CI_PROJECT_NAMESPACE`                        | `$`                                                      |
| `CI_PROJECT_PATH_SLUG`                        | `$`                                                            |
| `CI_PROJECT_PATH`                             | `$`                                                            |
| `CI_PROJECT_ROOT_NAMESPACE`                   | `$`                                                      |
| `CI_PROJECT_TITLE`                            | `$`                                            |
| `CI_PROJECT_URL`                              | `$/$`                                   |
| `CI_REPOSITORY_URL`                           | `$`                                            |
| `CI_RUNNER_EXECUTABLE_ARCH`                   | `$`                                                                    |
| `CI_SERVER_HOST`                              | `$`                                                            |
| `CI_SERVER_URL`                               | `$`                                                            |
| `CI_SERVER`                                   | `$`                                                               |
| `GITLAB_CI`                                   | `$`                                                               |
| `GITLAB_USER_EMAIL`                           | `$`                                                                 |
| `GITLAB_USER_ID`                              | `$`                                                                 |
| `GITLAB_USER_LOGIN`                           | `$`                                                                 |
| `GITLAB_USER_NAME`                            | `$`                                                                 |
| `TRIGGER_PAYLOAD`                             | `$`                                                            |
| `CI_MERGE_REQUEST_ASSIGNEES`                  | `$`                                          |
| `CI_MERGE_REQUEST_ID`                         | `$`                                             |
| `CI_MERGE_REQUEST_IID`                        | `$`                                             |
| `CI_MERGE_REQUEST_LABELS`                     | `$`                                             |
| `CI_MERGE_REQUEST_MILESTONE`                  | `$`                                          |
| `CI_MERGE_REQUEST_PROJECT_ID`                 | `$`                                                            |
| `CI_MERGE_REQUEST_PROJECT_PATH`               | `$`                                                            |
| `CI_MERGE_REQUEST_PROJECT_URL`                | `$/$`                                   |
| `CI_MERGE_REQUEST_REF_PATH`                   | `$`                                                                   |
| `CI_MERGE_REQUEST_SOURCE_BRANCH_NAME`         | `$`                                           |
| `CI_MERGE_REQUEST_SOURCE_BRANCH_SHA`          | `$`                                            |
| `CI_MERGE_REQUEST_SOURCE_PROJECT_ID`          | `$`                                |
| `CI_MERGE_REQUEST_SOURCE_PROJECT_PATH`        | `$`                                |
| `CI_MERGE_REQUEST_SOURCE_PROJECT_URL`         | `$`                                      |
| `CI_MERGE_REQUEST_TARGET_BRANCH_NAME`         | `$`                                           |
| `CI_MERGE_REQUEST_TARGET_BRANCH_SHA`          | `$`                                           |
| `CI_MERGE_REQUEST_TITLE`                      | `$`                                              |
| `CI_EXTERNAL_PULL_REQUEST_IID`                | `$`                                             |
| `CI_EXTERNAL_PULL_REQUEST_SOURCE_REPOSITORY`  | `$`                                |
| `CI_EXTERNAL_PULL_REQUEST_TARGET_REPOSITORY`  | `$`                                |
| `CI_EXTERNAL_PULL_REQUEST_SOURCE_BRANCH_NAME` | `$`                                           |
| `CI_EXTERNAL_PULL_REQUEST_SOURCE_BRANCH_SHA`  | `$`                                           |
| `CI_EXTERNAL_PULL_REQUEST_TARGET_BRANCH_NAME` | `$`                                           |
| `CI_EXTERNAL_PULL_REQUEST_TARGET_BRANCH_SHA`  | `$`                                           |

## Legal notice
