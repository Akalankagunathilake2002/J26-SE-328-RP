<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/tutorials/migrate-to-github-actions/automated-migrations/bitbucket-pipelines-migration -->
# Migrating from Bitbucket Pipelines with GitHub Actions Importer

Learn how to use GitHub to automate the migration of your Bitbucket pipelines to GitHub Actions.

## About migrating from Bitbucket Pipelines with GitHub Actions Importer

The instructions below will guide you through configuring your environment to use GitHub to migrate Bitbucket Pipelines to GitHub Actions.

### Prerequisites

### Limitations

There are some limitations when migrating from Bitbucket Pipelines to GitHub Actions with GitHub.

* Images in a private AWS ECR are not supported.
* The Bitbucket Pipelines option `size` is not supported. If additional runner resources are required in GitHub Actions, consider using GitHubs. For more information, see AUTOTITLE.
* Metrics detailing the queue time of jobs is not supported by the `forecast` command.
* Bitbucket after-scripts are supported using GitHub Actions `always()` in combination with checking the `steps..conclusion` of the previous step. For more information, see AUTOTITLE.

  The following is an example of using the `always()` with `steps..conclusion`.

  ```yaml
    - name: After Script 1
      run: |-
        echo "I'm after the script ran!"
        echo "We should be grouped!"
      id: after-script-1
      if: "$"
    - name: After Script 2
      run: |-
        echo "this is really the end"
        echo "goodbye, for now!"
      id: after-script-2
      if: "$"
  ```

### Manual tasks

Certain Bitbucket Pipelines constructs must be migrated manually. These include:

* Secured repository, workspace, and deployment variables
* SSH keys

## Installing the GitHub CLI extension

## Configuring credentials

The `configure` CLI command is used to set required credentials and options for GitHub when working with Bitbucket Pipelines and GitHub.

1. Create a GitHub . For more information, see AUTOTITLE.

   Your token must have the `workflow` scope.

   After creating the token, copy it and save it in a safe location for later use.
1. Create a Workspace Access Token for Bitbucket Pipelines. For more information, see Workspace Access Token permissions in the Bitbucket documentation. Your token must have the `read` scope for pipelines, projects, and repositories.

1. In your terminal, run the GitHub `configure` CLI command:

   ```shell
   gh actions-importer configure
   ```

   The `configure` command will prompt you for the following information:

   * For "Which CI providers are you configuring?", use the arrow keys to select `Bitbucket`, press Space to select it, then press Enter.
   * For "GitHub for GitHub", enter the value of the  that you created earlier, and press Enter.
   * For "Base url of the GitHub instance", enter the URL for GitHub, and press Enter.press Enter to accept the default value (`https://github.com`).
   * For "GitHub for Bitbucket", enter the Workspace Access Token that you created earlier, and press Enter.
   * For "Base url of the Bitbucket instance", enter the URL for your Bitbucket instance, and press Enter.

   An example of the `configure` command is shown below:

   ```shell
   $ gh actions-importer configure
   ✔ Which CI providers are you configuring?: Bitbucket
   Enter the following values (leave empty to omit):
   ✔ GitHub for GitHub: ***************
   ✔ Base url of the GitHub instance: https://github.com
   ✔ GitHub for Bitbucket: ********************
   ✔ Base url of the Bitbucket instance: https://bitbucket.example.com
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

## Perform an audit of the Bitbucket instance

You can use the audit command to get a high-level view of pipelines in a Bitbucket instance.

The audit command performs the following steps.
1. Fetches all of the pipelines for a workspace.
1. Converts pipeline to its equivalent GitHub Actions workflow.
1. Generates a report that summarizes how complete and complex of a migration is possible with GitHub.

### Running the audit command

To perform an audit run the following command in your terminal, replacing `:workspace` with the name of the Bitbucket workspace to audit.

```bash
gh actions-importer audit bitbucket --workspace :workspace --output-dir tmp/audit
```

Optionally, a `--project-key` option can be provided to the audit command to limit the results to only pipelines associated with a project.

In the below example command `:project_key` should be replaced with the key of the project that should be audited. Project keys can be found in Bitbucket on the workspace projects page.

```bash
gh actions-importer audit bitbucket --workspace :workspace --project-key :project_key --output-dir tmp/audit
```

### Inspecting the audit results

## Forecasting usage

You can use the `forecast` command to forecast potential GitHub Actions usage by computing metrics from completed pipeline runs in your Bitbucket instance.

### Running the forecast command

To perform a forecast of potential GitHub Actions usage, run the following command in your terminal, replacing `:workspace` with the name of the Bitbucket workspace to forecast. By default, GitHub Actions Importer includes the previous seven days in the forecast report.

```shell
gh actions-importer forecast bitbucket --workspace :workspace --output-dir tmp/forecast_reports
```

### Forecasting a project

To limit the forecast to a project, you can use the `--project-key` option. Replace the value for the `:project_key` with the project key for the project to forecast.

```shell
gh actions-importer forecast bitbucket --workspace :workspace --project-key :project_key --output-dir tmp/forecast_reports
```

### Inspecting the forecast report

The `forecast_report.md` file in the specified output directory contains the results of the forecast.

Listed below are some key terms that can appear in the forecast report:

* The **job count** is the total number of completed jobs.
* The **pipeline count** is the number of unique pipelines used.
* **Execution time** describes the amount of time a runner spent on a job. This metric can be used to help plan for the cost of GitHub-hosted runners.
  * This metric is correlated to how much you should expect to spend in GitHub Actions. This will vary depending on the hardware used for these minutes. You can use the GitHub Actions pricing calculator to estimate the costs.
* **Concurrent jobs** metrics describe the amount of jobs running at any given time.

## Performing a dry-run migration

You can use the dry-run command to convert a Bitbucket pipeline to an equivalent GitHub Actions workflow(s). A dry-run creates the output files in a specified directory, but does not open a pull request to migrate the pipeline.

### Running the dry-run command

To perform a dry run of migrating a Bitbucket pipeline to GitHub Actions, run the following command in your terminal, replacing `:workspace` with the name of the workspace and `:repo` with the name of the repository in Bitbucket.

```bash
gh actions-importer dry-run bitbucket --workspace :workspace --repository :repo --output-dir tmp/dry-run
```

### Inspecting the converted workflows

You can view the logs of the dry run and the converted workflow files in the specified output directory.

## Performing a production migration

You can use the migrate command to convert a Bitbucket pipeline and open a pull request with the equivalent GitHub Actions workflow(s).

### Running the migrate command

To migrate a Bitbucket pipeline to GitHub Actions, run the following command in your terminal, replacing the following values.

* Replace `target-url` value with the URL for your GitHub repository.
* Replace `:repo` with the name of the repository in Bitbucket.
* Replace `:workspace` with the name of the workspace.

```bash
gh actions-importer migrate bitbucket --workspace :workspace --repository :repo --target-url https://github.com/:owner/:repo --output-dir tmp/dry-run
```

The command's output includes the URL of the pull request that adds the converted workflow to your repository. An example of a successful output is similar to the following:

```bash
gh actions-importer migrate bitbucket --workspace actions-importer --repository custom-trigger --target-url https://github.com/valet-dev-testing/demo-private --output-dir tmp/bitbucket
[2023-07-18 09:56:06] Logs: 'tmp/bitbucket/log/valet-20230718-165606.log'
[2023-07-18 09:56:24] Pull request: 'https://github.com/valet-dev-testing/demo-private/pull/55'
```

## Reference

This section contains reference information on environment variables, optional arguments, and supported syntax when using GitHub to migrate from Bitbucket Pipelines.

### Using environment variables

GitHub uses the following environment variables to connect to your Bitbucket instance.

* `GITHUB_ACCESS_TOKEN`: The  used to create pull requests with a transformed workflow (requires `repo` and `workflow` scopes).
* `GITHUB_INSTANCE_URL`: The url to the target GitHub instance. (e.g. `https://github.com`)
* `BITBUCKET_ACCESS_TOKEN`: The workspace access token with read scopes for pipeline, project, and repository.

These environment variables can be specified in a `.env.local` file that will be loaded by GitHub at run time. The distribution archive contains a `.env.local.template` file that can be used to create these files.

### Optional arguments

#### `--source-file-path`

You can use the `--source-file-path` argument with the `dry-run` or `migrate` subcommands.

By default, GitHub fetches pipeline contents from the Bitbucket instance. The `--source-file-path` argument tells GitHub to use the specified source file path instead.

For example:

```bash
gh actions-importer dry-run bitbucket --workspace :workspace --repository :repo --output-dir tmp/dry-run --source-file-path path/to/my/pipeline/file.yml
```

#### `--config-file-path`

You can use the `--config-file-path` argument with the `audit`, `dry-run`, and `migrate` subcommands.

By default, GitHub fetches pipeline contents from the Bitbucket instance. The `--config-file-path` argument tells GitHub to use the specified source files instead.

### Audit example

In this example, GitHub uses the specified YAML configuration file to perform an audit.

```bash
gh actions-importer audit bitbucket --workspace :workspace --output-dir tmp/audit --config-file-path "path/to/my/bitbucket/config.yml"
```

To audit a Bitbucket instance using a config file, the config file must be in the following format, and each `repository_slug` must be unique:

```yaml
source_files:
  - repository_slug: repo_name
    path: path/to/one/source/file.yml
  - repository_slug: another_repo_name
    path: path/to/another/source/file.yml
```

## Supported syntax for Bitbucket Pipelines

The following table shows the type of properties that GitHub is currently able to convert.

| Bitbucket                 | GitHub Actions                                  |  Status      |
| :-------------------      | :-------------------------------------------    | -----------: |
| `after-script`            | `jobs..steps[*]`                        | Supported    |
| `artifacts`               | `actions/upload-artifact` & `download-artifact` | Supported    |
| `caches`                  | `actions/cache`                                 | Supported    |
| `clone`                   | `actions/checkout`                              | Supported    |
| `condition`               | `job..steps[*].run`                     | Supported    |
| `deployment`              | `jobs..environment`                     | Supported    |
| `image`                   | `jobs..container`                       | Supported    |
| `max-time`                | `jobs..steps[*].timeout-minutes`        | Supported    |
| `options.docker`          | None                                            | Supported    |
| `options.max-time`        | `jobs..steps[*].timeout-minutes`        | Supported    |
| `parallel`                | `jobs.`                                 | Supported    |
| `pipelines.branches`      | `on.push`                                       | Supported    |
| `pipelines.custom`        | `on.workflow_dispatch`                          | Supported    |
| `pipelines.default`       | `on.push`                                       | Supported    |
| `pipelines.pull-requests` | `on.pull_requests`                              | Supported    |
| `pipelines.tags`          | `on.tags`                                       | Supported    |
| `runs-on`                 | `jobs..runs-on`                         | Supported    |
| `script`                  | `job..steps[*].run`                     | Supported    |
| `services`                | `jobs..service`                         | Supported    |
| `stage`                   | `jobs.`                                 | Supported    |
| `step`                    | `jobs..steps[*]`                        | Supported    |
| `trigger`                 | `on.workflow_dispatch`                          | Supported    |
| `fail-fast`               | None                                            | Unsupported  |
| `oidc`                    | None                                            | Unsupported  |
| `options.size`            | None                                            | Unsupported  |
| `size`                    | None                                            | Unsupported  |

### Environment variable mapping

GitHub uses the mapping in the table below to convert default Bitbucket environment variables to the closest equivalent in GitHub Actions.

| Bitbucket                                | GitHub Actions                                                                 |
| :-------------------------------------   | :------------------------------------------------------                        |
|  `CI`                                    | `true`                                                    |
|  `BITBUCKET_BUILD_NUMBER`                | `$`                                |
|  `BITBUCKET_CLONE_DIR`                   | `$`                                 |
|  `BITBUCKET_COMMIT`                      | `$`                                       |
|  `BITBUCKET_WORKSPACE`                   | `$`                          |
|  `BITBUCKET_REPO_SLUG`                   | `$`                                |
|  `BITBUCKET_REPO_UUID`                   | `$`                             |
|  `BITBUCKET_REPO_FULL_NAME`              | `$`/`$` |
|  `BITBUCKET_BRANCH`                      | `$`                                       |
|  `BITBUCKET_TAG`                         | `$`                                       |
|  `BITBUCKET_PR_ID`                       | `$`                 |
|  `BITBUCKET_PR_DESTINATION_BRANCH`       | `$`               |
|  `BITBUCKET_GIT_HTTP_ORIGIN`             | `$`                |
|  `BITBUCKET_GIT_SSH_ORIGIN`              | `$`                  |
|  `BITBUCKET_EXIT_CODE`                   | `$`                                       |
|  `BITBUCKET_STEP_UUID`                   | `$`                                   |
|  `BITBUCKET_PIPELINE_UUID`               | `$`                                  |
|  `BITBUCKET_PROJECT_KEY`                 | `$`                          |
|  `BITBUCKET_PROJECT_UUID`                | `$`                          |
|  `BITBUCKET_STEP_TRIGGERER_UUID`         | `$`                                  |
|  `BITBUCKET_SSH_KEY_FILE`                | `$/.ssh/id_rsa`                     |
|  `BITBUCKET_STEP_OIDC_TOKEN`             | No Mapping                                           |
|  `BITBUCKET_DEPLOYMENT_ENVIRONMENT`      | No Mapping                                           |
|  `BITBUCKET_DEPLOYMENT_ENVIRONMENT_UUID` | No Mapping                                           |
|  `BITBUCKET_BOOKMARK`                    | No Mapping                                           |
|  `BITBUCKET_PARALLEL_STEP`               | No Mapping                                           |
|  `BITBUCKET_PARALLEL_STEP_COUNT`         | No Mapping                                           |

### System Variables

System variables used in tasks are transformed to the equivalent bash shell variable and are assumed to be available. For example, `${system.}` will be transformed to `$variable_name`. We recommend you verify this to ensure proper operation of the workflow.

## Legal notice
