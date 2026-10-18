<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/tutorials/migrate-to-github-actions/automated-migrations/travis-ci-migration -->
# Migrating from Travis CI with GitHub Actions Importer

Learn how to use GitHub to automate the migration of your Travis CI pipelines to GitHub Actions.

## About migrating from Travis CI with GitHub Actions Importer

The instructions below will guide you through configuring your environment to use GitHub to migrate Travis CI pipelines to GitHub Actions.

### Prerequisites

* A Travis CI account or organization with pipelines and jobs that you want to convert to GitHub Actions workflows.
* Access to create a Travis CI API access token for your account or organization.

### Limitations

There are some limitations when migrating from Travis CI pipelines to GitHub Actions with GitHub.

#### Manual tasks

Certain Travis CI constructs must be migrated manually. These include:

* Secrets
* Unknown job properties

For more information on manual migrations, see AUTOTITLE.

#### Travis CI project languages

GitHub transforms Travis CI project languages by adding a set of preconfigured build tools and a default build script to the transformed workflow. If no language is explicitly declared, GitHub assumes a project language is Ruby.

For a list of the project languages supported by GitHub, see Supported project languages.

## Installing the GitHub CLI extension

## Configuring credentials

The `configure` CLI command is used to set required credentials and options for GitHub when working with Travis CI and GitHub.

1. Create a GitHub . For more information, see AUTOTITLE.

   Your token must have the `workflow` scope.

   After creating the token, copy it and save it in a safe location for later use.
1. Create a Travis CI API access token. For more information, see Get your Travis CI API token in the Travis CI documentation.

   After creating the token, copy it and save it in a safe location for later use.
1. In your terminal, run the GitHub `configure` CLI command:

   ```shell
   gh actions-importer configure
   ```

   The `configure` command will prompt you for the following information:

   * For "Which CI providers are you configuring?", use the arrow keys to select `Travis CI`, press Space to select it, then press Enter.
   * For "GitHub for GitHub", enter the value of the  that you created earlier, and press Enter.
   * For "Base url of the GitHub instance", enter the URL for GitHub, and press Enter.press Enter to accept the default value (`https://github.com`).
   * For "GitHub for Travis CI", enter the value for the Travis CI API access token that you created earlier, and press Enter.
   * For "Base url of the Travis CI instance", enter the URL of your Travis CI instance, and press Enter.
   * For "Travis CI organization name", enter the name of your Travis CI organization, and press Enter.

   An example of the output of the `configure` command is shown below.

   ```shell
   $ gh actions-importer configure
   ✔ Which CI providers are you configuring?: Travis CI
   Enter the following values (leave empty to omit):
   ✔ GitHub for GitHub: ***************
   ✔ Base url of the GitHub instance: https://github.com
   ✔ GitHub for Travis CI: ***************
   ✔ Base url of the Travis CI instance: https://travis-ci.com
   ✔ Travis CI organization name: actions-importer-labs
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

## Perform an audit of Travis CI

You can use the `audit` command to get a high-level view of all pipelines in a Travis CI server.

The `audit` command performs the following steps:

1. Fetches all of the projects defined in a Travis CI server.
1. Converts each pipeline to its equivalent GitHub Actions workflow.
1. Generates a report that summarizes how complete and complex of a migration is possible with GitHub.

### Running the audit command

To perform an audit of a Travis CI server, run the following command in your terminal:

```shell
gh actions-importer audit travis-ci --output-dir tmp/audit
```

### Inspecting the audit results

## Forecast potential build runner usage

You can use the `forecast` command to forecast potential GitHub Actions usage by computing metrics from completed pipeline runs in your Travis CI server.

### Running the forecast command

To perform a forecast of potential GitHub Actions usage, run the following command in your terminal. By default, GitHub includes the previous seven days in the forecast report.

```shell
gh actions-importer forecast travis-ci --output-dir tmp/forecast
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

Additionally, these metrics are defined for each queue of runners in Travis CI. This is especially useful if there is a mix of hosted or self-hosted runners, or high or low spec machines, so you can see metrics specific to different types of runners.

## Perform a dry-run migration of a Travis CI pipeline

You can use the `dry-run` command to convert a Travis CI pipeline to an equivalent GitHub Actions workflow. A dry-run creates the output files in a specified directory, but does not open a pull request to migrate the pipeline.

To perform a dry run of migrating your Travis CI pipelines to GitHub Actions, run the following command in your terminal, replacing `my-travis-ci-repository` with the name of your Travis CI repository.

```shell
gh actions-importer dry-run travis-ci --travis-ci-repository my-travis-ci-repository --output-dir tmp/dry-run
```

You can view the logs of the dry run and the converted workflow files in the specified output directory.

## Perform a production migration of a Travis CI pipeline

You can use the `migrate` command to convert a Travis CI pipeline and open a pull request with the equivalent GitHub Actions workflow.

### Running the migrate command

To migrate a Travis CI pipeline to GitHub Actions, run the following command in your terminal, replacing the `target-url` value with the URL for your GitHub repository, and `my-travis-ci-repository` with the name of your Travis CI repository.

```shell
gh actions-importer migrate travis-ci --target-url https://github.com/octo-org/octo-repo --output-dir tmp/migrate --travis-ci-repository my-travis-ci-repository
```

The command's output includes the URL to the pull request that adds the converted workflow to your repository. An example of a successful output is similar to the following:

```shell
$ gh actions-importer migrate travis-ci --target-url https://github.com/octo-org/octo-repo --output-dir tmp/migrate --travis-ci-repository my-travis-ci-repository
[2022-08-20 22:08:20] Logs: 'tmp/migrate/log/actions-importer-20220916-014033.log'
[2022-08-20 22:08:20] Pull request: 'https://github.com/octo-org/octo-repo/pull/1'
```

## Reference

This section contains reference information on environment variables, optional arguments, and supported syntax when using GitHub to migrate from Travis CI.

### Using environment variables

GitHub uses the following environment variables to connect to your Travis CI instance:

* `GITHUB_ACCESS_TOKEN`: The  used to create pull requests with a converted workflow (requires the `workflow` scope).
* `GITHUB_INSTANCE_URL`: The URL to the target GitHub instance (for example, `https://github.com`).
* `TRAVIS_CI_ACCESS_TOKEN`: The Travis CI API access token used to view Travis CI resources.
* `TRAVIS_CI_ORGANIZATION`: The organization name of your Travis CI instance.
* `TRAVIS_CI_INSTANCE_URL`: The URL of the Travis CI instance.
* `TRAVIS_CI_SOURCE_GITHUB_ACCESS_TOKEN`: (Optional) The GitHub used to authenticate with your source GitHub instance. If not provided, `GITHUB_ACCESS_TOKEN` will be used instead.
* `TRAVIS_CI_SOURCE_GITHUB_INSTANCE_URL`: (Optional) The URL to the source GitHub instance, such as https://github.com. If not provided, `GITHUB_INSTANCE_URL` will be used instead.

These environment variables can be specified in a `.env.local` file that is loaded by GitHub when it is run.

### Using optional arguments

#### `--source-file-path`

You can use the `--source-file-path` argument with the `forecast`, `dry-run`, or `migrate` subcommands.

By default, GitHub fetches pipeline contents from source control. The `--source-file-path` argument tells GitHub to use the specified source file path instead.

For example:

```shell
gh actions-importer dry-run travis-ci --output-dir ./path/to/output/ --travis-ci-repository my-travis-ci-repository --source-file-path ./path/to/.travis.yml
```

#### `--allow-inactive-repositories`

You can use this argument to specify whether GitHub should include inactive repositories in an audit. If this option is not set, inactive repositories are not included in audits.

```shell
gh actions-importer dry-run travis-ci --output-dir ./path/to/output/ --travis-ci-repository my-travis-ci-repository --allow-inactive-repositories
```

#### `--config-file-path`

You can use the `--config-file-path` argument with the `audit`, `dry-run`, and `migrate` subcommands.

By default, GitHub fetches pipeline contents from source control. The `--config-file-path` argument tells GitHub to use the specified source files instead.

##### Audit example

In this example, GitHub uses the specified YAML configuration file to perform an audit.

```shell
gh actions-importer audit travis-ci --output-dir ./path/to/output/ --config-file-path ./path/to/travis-ci/config.yml
```

To audit a Travis CI instance using a configuration file, the file must be in the following format and each `repository_slug` value must be unique:

```yaml
source_files:
  - repository_slug: travis-org-name/travis-repo-name
    path: path/to/.travis.yml
  - repository_slug: travis-org-name/some-other-travis-repo-name
    path: path/to/.travis.yml
```

##### Dry run example

In this example, GitHub uses the specified YAML configuration file as the source file to perform a dry run.

The pipeline is selected by matching the `repository_slug` in the configuration file to the value of the `--travis-ci-repository` option. The `path` is then used to pull the specified source file.

```shell
gh actions-importer dry-run travis-ci --travis-ci-repository travis-org-name/travis-repo-name --output-dir ./output/ --config-file-path ./path/to/travis-ci/config.yml
```

### Supported project languages

GitHub supports migrating Travis CI projects in the following languages.

<code>android</code>
<code>bash</code>
<code>c</code>
<code>clojure</code>
<code>c++</code>
<code>crystal</code>
<code>c#</code>
<code>d</code>
<code>dart</code>
<code>elixir</code>
<code>erlang</code>
<code>generic</code>
<code>go</code>
<code>groovy</code>
<code>haskell</code>
<code>haxe</code>
<code>java</code>
<code>julia</code>
<code>matlab</code>
<code>minimal</code>
<code>nix</code>
<code>node_js</code>
<code>objective-c</code>
<code>perl</code>
<code>perl6</code>
<code>php</code>
<code>python</code>
<code>r</code>
<code>ruby</code>
<code>rust</code>
<code>scala</code>
<code>sh</code>
<code>shell</code>
<code>smalltalk</code>
<code>swift</code>

### Supported syntax for Travis CI pipelines

The following table shows the type of properties GitHub is currently able to convert. For more details about how Travis CI pipeline syntax aligns with GitHub Actions, see AUTOTITLE.

| Travis CI    | GitHub Actions                     |              Status |
| :------------------ | :--------------------------------- | ------------------: |
| branches            | `on..`|           Supported |
| build_pull_requests | `on.`   |           Supported |
| env                 | `env` `jobs..env``jobs..steps.env`                                                               |           Supported |
| if                  | `jobs..if`       |           Supported |
| job                 | `jobs.``jobs..name` |           Supported |
| matrix              | `jobs..strategy``jobs..strategy.fail-fast``jobs..strategy.matrix`                 |           Supported |
| os & dist           | `runners`        |           Supported |
| scripts             | `jobs..steps`    |           Supported |
| stages              | `jobs`           |           Supported |
| env                 | `on`                               | Partially supported |
| branches            | `on..``on..paths`                                                                     |         Unsupported |
| build_pull_requests | `on..``on..``on..paths`                          |         Unsupported |
| cron triggers       | `on.schedule``on.workflow_run` |         Unsupported |
| env                 | `jobs..timeout-minutes``on..types`                                                                     |         Unsupported |
| job                 | `jobs..container`          |         Unsupported |
| os & dist           | `self hosted runners`         |         Unsupported |

For information about supported Travis CI constructs, see the `github/gh-actions-importer` repository.

### Environment variables syntax

GitHub uses the mapping in the table below to convert default Travis CI environment variables to the closest equivalent in GitHub Actions.

| Travis CI                     | GitHub Actions                                                                        |
| :---------------------------- | :------------------------------------------------------------------------------------ |
| `$CONTINUOUS_INTEGRATION`     | `$CI`                                                                                 |
| `$USER`                       | `$`                                                          |
| `$HOME`                       | `$`                                                             |
| `$TRAVIS_BRANCH`             | `$`                                                                   |
| `$TRAVIS_BUILD_DIR`           | `$`                                                             |
| `$TRAVIS_BUILD_ID`            | `$`                                                            |
| `$TRAVIS_BUILD_NUMBER`        | `$`                                                                |
| `$TRAVIS_COMMIT`              | `$`                                                                   |
| `$TRAVIS_EVENT_TYPE`          | `$`                                                            |
| `$TRAVIS_PULL_REQUEST_BRANCH` | `$`                                                              |
| `$TRAVIS_PULL_REQUEST`        | `$`                                                          |
| `$TRAVIS_PULL_REQUEST_SHA`    | `$`                                                              |
| `$TRAVIS_PULL_REQUEST_SLUG`   | `$`                                                            |
| `$TRAVIS_TAG`                 | `$`                                                                   |
| `$TRAVIS_OS_NAME`             | `$`                                                                    |
| `$TRAVIS_JOB_ID`              | `$`                                                                   |
| `$TRAVIS_REPO_SLUG`           | `$`                                    |
| `$TRAVIS_BUILD_WEB_URL`       | `$/$/actions/runs/$` |

## Legal notice
