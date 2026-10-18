<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/tutorials/migrate-to-github-actions/automated-migrations/jenkins-migration -->
# Migrating from Jenkins with GitHub Actions Importer

Learn how to use GitHub to automate the migration of your Jenkins pipelines to GitHub Actions.

## About migrating from Jenkins with GitHub Actions Importer

The instructions below will guide you through configuring your environment to use GitHub to migrate Jenkins pipelines to GitHub Actions.

### Prerequisites

* A Jenkins account or organization with pipelines and jobs that you want to convert to GitHub Actions workflows.
* Access to create a Jenkins personal API token for your account or organization.

### Limitations

There are some limitations when migrating from Jenkins to GitHub Actions with GitHub. For example, you must migrate the following constructs manually:

* Mandatory build tools
* Scripted pipelines
* Secrets
* Self-hosted runners
* Unknown plugins

For more information on manual migrations, see AUTOTITLE.

## Installing the GitHub CLI extension

## Configuring credentials

The `configure` CLI command is used to set required credentials and options for GitHub when working with Jenkins and GitHub.

1. Create a GitHub . For more information, see AUTOTITLE.

   Your token must have the `workflow` scope.

   After creating the token, copy it and save it in a safe location for later use.
1. Create a Jenkins API token. For more information, see Authenticating scripted clients in the Jenkins documentation.

   After creating the token, copy it and save it in a safe location for later use.
1. In your terminal, run the GitHub `configure` CLI command:

   ```shell
   gh actions-importer configure
   ```

   The `configure` command will prompt you for the following information:

   * For "Which CI providers are you configuring?", use the arrow keys to select `Jenkins`, press Space to select it, then press Enter.
   * For "GitHub for GitHub", enter the value of the  that you created earlier, and press Enter.
   * For "Base url of the GitHub instance", enter the URL for GitHub, and press Enter.press Enter to accept the default value (`https://github.com`).
   * For "GitHub for Jenkins", enter the value for the Jenkins personal API token that you created earlier, and press Enter.
   * For "Username of Jenkins user", enter your Jenkins username and press Enter.
   * For "Base url of the Jenkins instance", enter the URL of your Jenkins instance, and press Enter.

   An example of the `configure` command is shown below:

   ```shell
   $ gh actions-importer configure
   ✔ Which CI providers are you configuring?: Jenkins
   Enter the following values (leave empty to omit):
   ✔ GitHub for GitHub: ***************
   ✔ Base url of the GitHub instance: https://github.com
   ✔ GitHub for Jenkins: ***************
   ✔ Username of Jenkins user: admin
   ✔ Base url of the Jenkins instance: https://localhost
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

## Perform an audit of Jenkins

You can use the `audit` command to get a high-level view of all pipelines in a Jenkins server.

The `audit` command performs the following steps:

1. Fetches all of the projects defined in a Jenkins server.
1. Converts each pipeline to its equivalent GitHub Actions workflow.
1. Generates a report that summarizes how complete and complex of a migration is possible with GitHub.

### Running the audit command

To perform an audit of a Jenkins server, run the following command in your terminal:

```shell
gh actions-importer audit jenkins --output-dir tmp/audit
```

### Inspecting the audit results

## Forecast potential build runner usage

You can use the `forecast` command to forecast potential GitHub Actions usage by computing metrics from completed pipeline runs in your Jenkins server.

### Prerequisites for running the forecast command

In order to run the `forecast` command against a Jenkins instance, you must install the `paginated-builds` plugin on your Jenkins server. This plugin allows GitHub to efficiently retrieve historical build data for jobs that have a large number of builds. Because Jenkins does not provide a method to retrieve paginated build data, using this plugin prevents timeouts from the Jenkins server that can occur when fetching a large amount of historical data. The `paginated-builds` plugin is open source, and exposes a REST API endpoint to fetch build data in pages, rather than all at once.

To install the `paginated-builds` plugin:

1. On your Jenkins instance, navigate to `https:///pluginManager/available`.
1. Search for the `paginated-builds` plugin.
1. Check the box on the left and select **Install without restart**.

### Running the forecast command

To perform a forecast of potential GitHub Actions, run the following command in your terminal. By default, GitHub includes the previous seven days in the forecast report.

```shell
gh actions-importer forecast jenkins --output-dir tmp/forecast
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

Additionally, these metrics are defined for each queue of runners in Jenkins. This is especially useful if there is a mix of hosted or self-hosted runners, or high or low spec machines, so you can see metrics specific to different types of runners.

## Perform a dry-run migration of a Jenkins pipeline

You can use the `dry-run` command to convert a Jenkins pipeline to its equivalent GitHub Actions workflow.

### Running the dry-run command

You can use the `dry-run` command to convert a Jenkins pipeline to an equivalent GitHub Actions workflow. A dry-run creates the output files in a specified directory, but does not open a pull request to migrate the pipeline.

To perform a dry run of migrating your Jenkins pipelines to GitHub Actions, run the following command in your terminal, replacing `my-jenkins-project` with the URL of your Jenkins job.

```shell
gh actions-importer dry-run jenkins --source-url my-jenkins-project --output-dir tmp/dry-run
```

### Inspecting the converted workflows

You can view the logs of the dry run and the converted workflow files in the specified output directory.

## Perform a production migration of a Jenkins pipeline

You can use the `migrate` command to convert a Jenkins pipeline and open a pull request with the equivalent GitHub Actions workflow.

### Running the migrate command

To migrate a Jenkins pipeline to GitHub Actions, run the following command in your terminal, replacing the `target-url` value with the URL for your GitHub repository, and `my-jenkins-project` with the URL for your Jenkins job.

```shell
gh actions-importer migrate jenkins --target-url https://github.com/:owner/:repo --output-dir tmp/migrate --source-url my-jenkins-project
```

The command's output includes the URL to the pull request that adds the converted workflow to your repository. An example of a successful output is similar to the following:

```shell
$ gh actions-importer migrate jenkins --target-url https://github.com/octo-org/octo-repo --output-dir tmp/migrate --source-url http://localhost:8080/job/monas_dev_work/job/monas_freestyle
[2022-08-20 22:08:20] Logs: 'tmp/migrate/log/actions-importer-20220916-014033.log'
[2022-08-20 22:08:20] Pull request: 'https://github.com/octo-org/octo-repo/pull/1'
```

## Reference

This section contains reference information on environment variables, optional arguments, and supported syntax when using GitHub to migrate from Jenkins.

### Using environment variables

GitHub uses the following environment variables to connect to your Jenkins instance:

* `GITHUB_ACCESS_TOKEN`: The  used to create pull requests with a converted workflow (requires `repo` and `workflow` scopes).
* `GITHUB_INSTANCE_URL`: The URL to the target GitHub instance (for example, `https://github.com`).
* `JENKINS_ACCESS_TOKEN`: The Jenkins API token used to view Jenkins resources.

  > [!NOTE]
  > This token requires access to all jobs that you want to migrate or audit. In cases where a folder or job does not inherit access control lists from their parent, you must grant explicit permissions or full admin privileges.

* `JENKINS_USERNAME`: The username of the user account that created the Jenkins API token.
* `JENKINS_INSTANCE_URL`: The URL of the Jenkins instance.
* `JENKINSFILE_ACCESS_TOKEN` (Optional) The API token used to retrieve the contents of a `Jenkinsfile` stored in the build repository. This requires the `repo` scope. If this is not provided, the `GITHUB_ACCESS_TOKEN` will be used instead.

These environment variables can be specified in a `.env.local` file that is loaded by GitHub when it is run.

### Using optional arguments

#### `--source-file-path`

You can use the `--source-file-path` argument with the `forecast`, `dry-run`, or `migration` subcommands.

By default, GitHub fetches pipeline contents from source control. The `--source-file-path` argument tells GitHub to use the specified source file path instead. You can use this option for Jenkinsfile and multibranch pipelines.

If you would like to supply multiple source files when running the `forecast` subcommand, you can use pattern matching in the file path value. For example, `gh forecast --source-file-path ./tmp/previous_forecast/jobs/*.json` supplies GitHub with any source files that match the `./tmp/previous_forecast/jobs/*.json` file path.

##### Jenkinsfile pipeline example

In this example, GitHub uses the specified Jenkinsfile as the source file to perform a dry run.

```shell
gh actions-importer dry-run jenkins --output-dir path/to/output/ --source-file-path path/to/Jenkinsfile --source-url :url_to_jenkins_job
```

#### `--config-file-path`

You can use the `--config-file-path` argument with the `audit`, `dry-run`, and `migrate` subcommands.

By default, GitHub fetches pipeline contents from source control. The `--config-file-path` argument tells GitHub to use the specified source files instead.

When you use the `--config-file-path` option with the `dry-run` or `migrate` subcommands, GitHub matches the repository slug to the job represented by the `--source-url` option to select the pipeline. It uses the `config-file-path` to pull the specified source file.

##### Audit example

In this example, GitHub uses the specified YAML configuration file to perform an audit.

```shell
gh actions-importer audit jenkins --output-dir path/to/output/ --config-file-path path/to/jenkins/config.yml
```

To audit a Jenkins instance using a config file, the config file must be in the following format, and each `repository_slug` value must be unique:

```yaml
source_files:
  - repository_slug: pipeline-name
    path: path/to/Jenkinsfile
  - repository_slug: multi-branch-pipeline-name
    branches:
      - branch: main
        path: path/to/Jenkinsfile
      - branch: node
        path: path/to/Jenkinsfile
```

### Supported syntax for Jenkins pipelines

The following tables show the type of properties GitHub is currently able to convert. For more details about how Jenkins pipeline syntax aligns with GitHub Actions, see AUTOTITLE.

For information about supported Jenkins plugins, see the `github/gh-actions-importer` repository.

#### Supported syntax for Freestyle pipelines

| Jenkins                   | GitHub Actions                     |              Status |
| :------------------------ | :--------------------------------- | :------------------ |
| docker template           | `jobs..container`          |           Supported |
| build                     | `jobs`                             | Partially supported |
| build environment         | `env`                              | Partially supported |
| build triggers            | `on`                               | Partially supported |
| general                   | `runners`                          | Partially supported |

#### Supported syntax for Jenkinsfile pipelines

| Jenkins     | GitHub Actions                     |              Status |
| :---------- | :--------------------------------- | :------------------ |
| docker      | `jobs..container`          |           Supported |
| stage       | `jobs.`                    |           Supported |
| agent       | `runners`                          | Partially supported |
| environment | `env`                              | Partially supported |
| stages      | `jobs`                             | Partially supported |
| steps       | `jobs..steps`              | Partially supported |
| triggers    | `on`                               | Partially supported |
| when        | `jobs..if`                 | Partially supported |
| inputs      | `inputs`                           |         Unsupported |
| matrix      | `jobs..strategy.matrix`    |         Unsupported |
| options     | `jobs..strategy`           |         Unsupported |
| parameters  | `inputs`                           |         Unsupported |

### Environment variables syntax

GitHub uses the mapping in the table below to convert default Jenkins environment variables to the closest equivalent in GitHub Actions.

| Jenkins           | GitHub Actions                                                                        |
| :---------------- | :------------------------------------------------------------------------------------ |
| `${BUILD_ID}`     | `$`                                                                |
| `${BUILD_NUMBER}` | `$`                                                                |
| `${BUILD_TAG}`    | `$-$`                                         |
| `${BUILD_URL}`    | `$/$/actions/runs/$` |
| `${JENKINS_URL}`  | `$`                                                            |
| `${JOB_NAME}`     | `$`                                                              |
| `${WORKSPACE}`    | `$`                                                             |

## Legal notice
