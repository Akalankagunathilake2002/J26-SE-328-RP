<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/tutorials/migrate-to-github-actions/automated-migrations/azure-devops-migration -->
# Migrating from Azure DevOps with GitHub Actions Importer

Learn how to use GitHub to automate the migration of your Azure DevOps pipelines to GitHub Actions.

## About migrating from Azure DevOps with GitHub Actions Importer

The instructions below will guide you through configuring your environment to use GitHub to migrate Azure DevOps pipelines to GitHub Actions.

### Prerequisites

* An Azure DevOps account or organization with projects and pipelines that you want to convert to GitHub Actions workflows.
* Access to create an Azure DevOps GitHub for your account or organization.

### Limitations

There are some limitations when migrating from Azure DevOps to GitHub Actions with GitHub:

* GitHub requires version 5.0 of the Azure DevOps API, available in either Azure DevOps Services or Azure DevOps Server 2019. Older versions of Azure DevOps Server are not compatible.
* Tasks that are implicitly added to an Azure DevOps pipeline, such as checking out source code, may be added to a GitHub audit as a GUID name. To find the friendly task name for a GUID, you can use the following URL: `https://dev.azure.com/:organization/_apis/distributedtask/tasks/:guid`.

#### Manual tasks

Certain Azure DevOps constructs must be migrated manually from Azure DevOps into GitHub Actions configurations. These include:
* Organization, repository, and environment secrets
* Service connections such as OIDC Connect, GitHub, and GitHub
* Unknown tasks
* Self-hosted agents
* Environments
* Pre-deployment approvals

For more information on manual migrations, see AUTOTITLE.

#### Unsupported tasks

GitHub does not support migrating the following tasks:

* Pre-deployment gates
* Post-deployment gates
* Post-deployment approvals
* Some resource triggers

## Installing the GitHub CLI extension

## Configuring credentials

The `configure` CLI command is used to set required credentials and options for GitHub when working with Azure DevOps and GitHub.

1. Create a GitHub . For more information, see AUTOTITLE.

   Your token must have the `workflow` scope.

   After creating the token, copy it and save it in a safe location for later use.
1. Create an Azure DevOps GitHub. For more information, see Use GitHub in the Azure DevOps documentation. The token must have the following scopes:

   * Agents Pool: `Read`
   * Build: `Read`
   * Code: `Read`
   * Release: `Read`
   * Service Connections: `Read`
   * Task Groups: `Read`
   * Variable Groups: `Read`

   After creating the token, copy it and save it in a safe location for later use.
1. In your terminal, run the GitHub `configure` CLI command:

   ```shell
   gh actions-importer configure
   ```

   The `configure` command will prompt you for the following information:

   * For "Which CI providers are you configuring?", use the arrow keys to select `Azure DevOps`, press Space to select it, then press Enter.
   * For "GitHub for GitHub", enter the value of the  that you created earlier, and press Enter.
   * For "Base url of the GitHub instance", enter the URL for GitHub, and press Enter.press Enter to accept the default value (`https://github.com`).
   * For "GitHub for Azure DevOps", enter the value for the Azure DevOps GitHub that you created earlier, and press Enter.
   * For "Base url of the Azure DevOps instance", press Enter to accept the default value (`https://dev.azure.com`).
   * For "Azure DevOps organization name", enter the name for your Azure DevOps organization, and press Enter.
   * For "Azure DevOps project name", enter the name for your Azure DevOps project, and press Enter.

   An example of the `configure` command is shown below:

   ```shell
   $ gh actions-importer configure
   ✔ Which CI providers are you configuring?: Azure DevOps
   Enter the following values (leave empty to omit):
   ✔ GitHub for GitHub: ***************
   ✔ Base url of the GitHub instance: https://github.com
   ✔ GitHub for Azure DevOps: ***************
   ✔ Base url of the Azure DevOps instance: https://dev.azure.com
   ✔ Azure DevOps organization name: :organization
   ✔ Azure DevOps project name: :project
   Environment variables successfully updated.
   ```

1. In your terminal, run the GitHub `update` CLI command to connect to the GitHub GitHub and ensure that the container image is updated to the latest version:

   ```shell
   gh actions-importer update
   ```

   The output of the command should be similar to below:

   ```shell
   Updating ghcr.io/actions-importer/cli:latest...
   ghcr.io/actions-importer/cli:latest up-to-date
   ```

## Perform an audit of Azure DevOps

You can use the `audit` command to get a high-level view of all projects in an Azure DevOps organization.

The `audit` command performs the following steps:

1. Fetches all of the projects defined in an Azure DevOps organization.
1. Converts each pipeline to its equivalent GitHub Actions workflow.
1. Generates a report that summarizes how complete and complex of a migration is possible with GitHub.

### Running the audit command

To perform an audit of an Azure DevOps organization, run the following command in your terminal:

```shell
gh actions-importer audit azure-devops --output-dir tmp/audit
```

### Inspecting the audit results

## Forecast potential GitHub Actions usage

You can use the `forecast` command to forecast potential GitHub Actions usage by computing metrics from completed pipeline runs in Azure DevOps.

### Running the forecast command

To perform a forecast of potential GitHub Actions usage, run the following command in your terminal. By default, GitHub includes the previous seven days in the forecast report.

```shell
gh actions-importer forecast azure-devops --output-dir tmp/forecast_reports
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

Additionally, these metrics are defined for each queue of runners in Azure DevOps. This is especially useful if there is a mix of hosted or self-hosted runners, or high or low spec machines, so you can see metrics specific to different types of runners.

## Perform a dry-run migration

You can use the `dry-run` command to convert an Azure DevOps pipeline to an equivalent GitHub Actions workflow. A dry run creates the output files in a specified directory, but does not open a pull request to migrate the pipeline.

### Running the dry-run command for a build pipeline

To perform a dry run of migrating your Azure DevOps build pipeline to GitHub Actions, run the following command in your terminal, replacing `pipeline_id` with the ID of the pipeline you are converting.

```shell
gh actions-importer dry-run azure-devops pipeline --pipeline-id :pipeline_id --output-dir tmp/dry-run
```

You can view the logs of the dry run and the converted workflow files in the specified output directory.

### Running the dry-run command for a release pipeline

To perform a dry run of migrating your Azure DevOps release pipeline to GitHub Actions, run the following command in your terminal, replacing `pipeline_id` with the ID of the pipeline you are converting.

```shell
gh actions-importer dry-run azure-devops release --pipeline-id :pipeline_id --output-dir tmp/dry-run
```

You can view the logs of the dry run and the converted workflow files in the specified output directory.

## Perform a production migration

You can use the `migrate` command to convert an Azure DevOps pipeline and open a pull request with the equivalent GitHub Actions workflow.

### Running the migrate command for a build pipeline

To migrate an Azure DevOps build pipeline to GitHub Actions, run the following command in your terminal, replacing the `target-url` value with the URL for your GitHub repository, and `pipeline_id` with the ID of the pipeline you are converting.

```shell
gh actions-importer migrate azure-devops pipeline --pipeline-id :pipeline_id --target-url https://github.com/octo-org/octo-repo --output-dir tmp/migrate
```

The command's output includes the URL of the pull request that adds the converted workflow to your repository. An example of a successful output is similar to the following:

```shell
$ gh actions-importer migrate azure-devops pipeline --target-url https://github.com/octo-org/octo-repo --output-dir tmp/migrate --azure-devops-project my-azure-devops-project
[2022-08-20 22:08:20] Logs: 'tmp/migrate/log/actions-importer-20220916-014033.log'
[2022-08-20 22:08:20] Pull request: 'https://github.com/octo-org/octo-repo/pull/1'
```

### Running the migrate command for a release pipeline

To migrate an Azure DevOps release pipeline to GitHub Actions, run the following command in your terminal, replacing the `target-url` value with the URL for your GitHub repository, and `pipeline_id` with the ID of the pipeline you are converting.

```shell
gh actions-importer migrate azure-devops release --pipeline-id :pipeline_id --target-url https://github.com/octo-org/octo-repo --output-dir tmp/migrate
```

The command's output includes the URL of the pull request that adds the converted workflow to your repository. An example of a successful output is similar to the following:

```shell
$ gh actions-importer migrate azure-devops release --target-url https://github.com/octo-org/octo-repo --output-dir tmp/migrate --azure-devops-project my-azure-devops-project
[2022-08-20 22:08:20] Logs: 'tmp/migrate/log/actions-importer-20220916-014033.log'
[2022-08-20 22:08:20] Pull request: 'https://github.com/octo-org/octo-repo/pull/1'
```

## Reference

This section contains reference information on environment variables, optional arguments, and supported syntax when using GitHub to migrate from Azure DevOps.

### Configuration environment variables

GitHub uses the following environment variables to connect to your Azure DevOps instance:

* `GITHUB_ACCESS_TOKEN`: The  used to create pull requests with a converted workflow (requires the `workflow` scope).
* `GITHUB_INSTANCE_URL`: The URL to the target GitHub instance (for example, `https://github.com`).
* `AZURE_DEVOPS_ACCESS_TOKEN`: The GitHub used to authenticate with your Azure DevOps instance. This token requires the following scopes:
  * Build: `Read`
  * Agent Pools: `Read`
  * Code: `Read`
  * Release: `Read`
  * Service Connections: `Read`
  * Task Groups: `Read`
  * Variable Groups: `Read`
* `AZURE_DEVOPS_PROJECT`: The project name or GUID to use when migrating a pipeline. If you'd like to perform an audit on all projects, this is optional.
* `AZURE_DEVOPS_ORGANIZATION`: The organization name of your Azure DevOps instance.
* `AZURE_DEVOPS_INSTANCE_URL`: The URL to the Azure DevOps instance, such as `https://dev.azure.com`.

These environment variables can be specified in a `.env.local` file that is loaded by GitHub when it is run.

### Optional arguments

#### `--source-file-path`

You can use the `--source-file-path` argument with the `forecast`, `dry-run`, or `migrate` subcommands.

By default, GitHub fetches pipeline contents from source control. The `--source-file-path` argument tells GitHub to use the specified source file path instead.

For example:

```shell
gh actions-importer dry-run azure-devops pipeline --output-dir ./output/ --source-file-path ./path/to/azure_devops/pipeline.yml
```

#### `--config-file-path`

You can use the `--config-file-path` argument with the `audit`, `dry-run`, and `migrate` subcommands.

By default, GitHub fetches pipeline contents from source control. The `--config-file-path` argument tells GitHub to use the specified source files instead.

The `--config-file-path` argument can also be used to specify which repository a converted reusable workflow or composite action should be migrated to.

##### Audit example

In this example, GitHub uses the specified YAML configuration file as the source file to perform an audit.

```shell
gh actions-importer audit azure-devops pipeline --output-dir ./output/ --config-file-path ./path/to/azure_devops/config.yml
```

To audit an Azure DevOps instance using a configuration file, the configuration file must be in the following format and each `repository_slug` must be unique:

```yaml
source_files:
  - repository_slug: azdo-project/1
    path: file.yml
  - repository_slug: azdo-project/2
    paths: path.yml
```

You can generate the `repository_slug` for a pipeline by combining the Azure DevOps organization name, project name, and the pipeline ID. For example, `my-organization-name/my-project-name/42`.

##### Dry run example

In this example, GitHub uses the specified YAML configuration file as the source file to perform a dry run.

The pipeline is selected by matching the `repository_slug` in the configuration file to the value of the `--azure-devops-organization` and `--azure-devops-project` option. The `path` is then used to pull the specified source file.

```shell
gh actions-importer dry-run azure-devops pipeline --output-dir ./output/ --config-file-path ./path/to/azure_devops/config.yml
```

##### Specify the repository of converted reusable workflows and composite actions

GitHub uses the YAML file provided to the `--config-file-path` argument to determine the repository that converted reusable workflows and composite actions are migrated to.

To begin, you should run an audit without the `--config-file-path` argument:

```shell
gh actions-importer audit azure-devops --output-dir ./output/
```

The output of this command will contain a file named `config.yml` that contains a list of all the reusable workflows and composite actions that were converted by GitHub. For example, the `config.yml` file may have the following contents:

```yaml
reusable_workflows:
  - name: my-reusable-workflow.yml
    target_url: https://github.com/octo-org/octo-repo
    ref: main

composite_actions:
  - name: my-composite-action.yml
    target_url: https://github.com/octo-org/octo-repo
    ref: main
```

You can use this file to specify which repository and ref a reusable workflow or composite action should be added to. You can then use the `--config-file-path` argument to provide the `config.yml` file to GitHub. For example, you can use this file when running a `migrate` command to open a pull request for each unique repository defined in the config file:

```shell
gh actions-importer migrate azure-devops pipeline --config-file-path config.yml --target-url https://github.com/my-org/my-repo
```

### Supported syntax for Azure DevOps pipelines

The following table shows the type of properties that GitHub is currently able to convert.

| Azure Pipelines       | GitHub Actions                        |              Status |
| :-------------------- | :------------------------------------ | :------------------ |
| condition             | `jobs..if``jobs..steps[*].if` |           Supported |
| container             | `jobs..container``jobs..name`                  |           Supported |
| continuousIntegration | `on..``on..``on..paths` |           Supported |
| job                   | `jobs.` |           Supported |
| pullRequest           | `on..``on..paths` |           Supported |
| stage                 | `jobs` |           Supported |
| steps                 | `jobs..steps` |           Supported |
| strategy              | `jobs..strategy.fail-fast``jobs..strategy.max-parallel``jobs..strategy.matrix`       |           Supported |
| timeoutInMinutes      | `jobs..timeout-minutes` |           Supported |
| variables             | `env``jobs..env``jobs..steps.env` |           Supported |
| manual deployment     | `jobs..environment` | Partially supported |
| pool                  | `runners``self hosted runners` | Partially supported |
| services              | `jobs..services` | Partially supported |
| strategy              | `jobs..strategy` | Partially supported |
| triggers              | `on`                        | Partially supported |
| pullRequest           | `on..`  |         Unsupported |
| schedules             | `on.schedule``on.workflow_run` |         Unsupported |
| triggers              | `on..types`     |         Unsupported |

For more information about supported Azure DevOps tasks, see the `github/gh-actions-importer` repository.

### Environment variable mapping

GitHub uses the mapping in the table below to convert default Azure DevOps environment variables to the closest equivalent in GitHub Actions.

| Azure Pipelines                             | GitHub Actions                                      |
| :------------------------------------------ | :-------------------------------------------------- |
| `$(Agent.BuildDirectory)`                   | `$`                           |
| `$(Agent.HomeDirectory)`                    | `$`                                   |
| `$(Agent.JobName)`                          | `$`                                 |
| `$(Agent.OS)`                               | `$`                                  |
| `$(Agent.ReleaseDirectory)`                 | `$`                            |
| `$(Agent.RootDirectory)`                    | `$`                           |
| `$(Agent.ToolsDirectory)`                   | `$`                          |
| `$(Agent.WorkFolder)`                       | `$`                           |
| `$(Build.ArtifactStagingDirectory)`         | `$`                                |
| `$(Build.BinariesDirectory)`                | `$`                           |
| `$(Build.BuildId)`                          | `$`                              |
| `$(Build.BuildNumber)`                      | `$`                          |
| `$(Build.DefinitionId)`                     | `$`                            |
| `$(Build.DefinitionName)`                   | `$`                            |
| `$(Build.PullRequest.TargetBranch)`         | `$`                            |
| `$(Build.PullRequest.TargetBranch.Name)`    | `$`                            |
| `$(Build.QueuedBy)`                         | `$`                               |
| `$(Build.Reason)`                           | `$`                          |
| `$(Build.Repository.LocalPath)`             | `$`                           |
| `$(Build.Repository.Name)`                  | `$`                          |
| `$(Build.Repository.Provider)`              | `GitHub`                                            |
| `$(Build.Repository.Uri)`                   | `$/$` |
| `$(Build.RequestedFor)`                     | `$`                               |
| `$(Build.SourceBranch)`                     | `$`                                 |
| `$(Build.SourceBranchName)`                 | `$`                                 |
| `$(Build.SourceVersion)`                    | `$`                                 |
| `$(Build.SourcesDirectory)`                 | `$`                           |
| `$(Build.StagingDirectory)`                 | `$`                                |
| `$(Pipeline.Workspace)`                     | `$`                           |
| `$(Release.DefinitionEnvironmentId)`        | `$`                                 |
| `$(Release.DefinitionId)`                   | `$`                            |
| `$(Release.DefinitionName)`                 | `$`                            |
| `$(Release.Deployment.RequestedFor)`        | `$`                               |
| `$(Release.DeploymentID)`                   | `$`                              |
| `$(Release.EnvironmentId)`                 | `$`                                 |
| `$(Release.EnvironmentName)`                | `$`                                 |
| `$(Release.Reason)`                        | `$`                          |
| `$(Release.RequestedFor)`                  | `$`                               |
| `$(System.ArtifactsDirectory)`              | `$`                           |
| `$(System.DefaultWorkingDirectory)`         | `$`                           |
| `$(System.HostType)`                        | `build`                                             |
| `$(System.JobId)`                           | `$`                                 |
| `$(System.JobName)`                         | `$`                                 |
| `$(System.PullRequest.PullRequestId)`       | `$`                        |
| `$(System.PullRequest.PullRequestNumber)`   | `$`                        |
| `$(System.PullRequest.SourceBranch)`        | `$`                                 |
| `$(System.PullRequest.SourceRepositoryUri)` | `$/$` |
| `$(System.PullRequest.TargetBranch)`        | `$`                      |
| `$(System.PullRequest.TargetBranchName)`    | `$`                      |
| `$(System.StageAttempt)`                    | `$`                          |
| `$(System.TeamFoundationCollectionUri)`     | `$/$` |
| `$(System.WorkFolder)`                      | `$`                           |

### Templates

You can transform Azure DevOps templates with GitHub.

#### Limitations

GitHub is able to transform Azure DevOps templates with some limitations.

* Azure DevOps templates used under the `stages`, `deployments`, and `jobs` keys are converted into reusable workflows in GitHub Actions. For more information, see AUTOTITLE.
* Azure DevOps templates used under the `steps` key are converted into composite actions. For more information, see AUTOTITLE.
* If you currently have job templates that reference other job templates, GitHub converts the templates into reusable workflows. Because reusable workflows cannot reference other reusable workflows, this is invalid syntax in GitHub Actions. You must manually correct nested reusable workflows.
* If a template references an external Azure DevOps organization or GitHub repository, you must use the `--credentials-file` option to provide credentials to access this template. For more information, see AUTOTITLE.
* You can dynamically generate YAML using `each` expressions with the following caveats:
  * Nested `each` blocks are not supported and cause the parent `each` block to be unsupported.
  * `each` and contained `if` conditions are evaluated at transformation time, because GitHub Actions does not support this style of insertion.
  * `elseif` blocks are unsupported. If this functionality is required, you must manually correct them.
  * Nested `if` blocks are supported, but `if/elseif/else` blocks nested under an `if` condition are not.
  * `if` blocks that use predefined Azure DevOps variables are not supported.

#### Supported templates

GitHub supports the templates listed in the table below.

| Azure Pipelines               | GitHub Actions                        |              Status |
| :---------------------------- | :------------------------------------ | ------------------: |
| Extending from a template     | `Reusable workflow`                   |           Supported |
| Job templates                 | `Reusable workflow`                   |           Supported |
| Stage templates               | `Reusable workflow`                   |           Supported |
| Step templates                | `Composite action`                    |           Supported |
| Task groups in classic editor | Varies                                |           Supported |
| Templates in a different Azure DevOps organization, project, or repository    | Varies                              |           Supported |
| Templates in a GitHub repository | Varies                              |           Supported |
| Variable templates            | `env`                                 |           Supported |
| Conditional insertion         | `if` conditions on job/steps          | Partially supported |
| Iterative insertion           | Not applicable                        | Partially supported |
| Templates with parameters     | Varies                                | Partially supported |

#### Template file path names

GitHub can extract templates with relative or dynamic file paths with variable, parameter, and iterative expressions in the file name. However, there must be a default value set.

##### Variable file path name example

```yaml
# File: azure-pipelines.yml
variables:
- template: 'templates/vars.yml'

steps:
- template: "./templates/$"
```

```yaml
# File: templates/vars.yml
variables:
  one: 'simple_step.yml'
```

##### Parameter file path name example

```yaml
parameters:
- name: template
  type: string
  default: simple_step.yml

steps:
- template: "./templates/$"
```

##### Iterative file path name example

```yaml
parameters:
- name: steps
  type: object
  default:
  - build_step
  - release_step
steps:
- $:
    - template: "$-variables.yml"
```

#### Template parameters

GitHub supports the parameters listed in the table below.

| Azure Pipelines       | GitHub Actions                              |              Status   |
| :-------------------- | :-----------------------------------------  | :-------------------  |
| string                | `inputs.string`                             |           Supported   |
| number                | `inputs.number`                             |           Supported   |
| boolean               | `inputs.boolean`                            |           Supported   |
| object                | `inputs.string` with `fromJSON` expression  | Partially supported   |
| step                  | `step`                                      | Partially supported  |
| stepList              | `step`                                      | Partially supported  |
| job                   | `job`                                       | Partially supported |
| jobList               | `job`                                       | Partially supported |
| deployment            | `job`                                       | Partially supported |
| deploymentList        | `job`                                       | Partially supported |
| stage                 | `job`                                       | Partially supported |
| stageList             | `job`                                       | Partially supported |

> [!NOTE]
> A template used under the `step` key with this parameter type is only serialized as a composite action if the steps are used at the beginning or end of the template steps. A template used under the `stage`, `deployment`, and `job` keys with this parameter type are not transformed into a reusable workflow, and instead are serialized as a standalone workflow.

## Legal notice
