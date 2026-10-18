<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/get-started/understand-github-actions -->
# Understanding GitHub Actions

Learn the basics of core concepts and essential terminology in GitHub Actions.

## Overview

 You can create workflows that build and test every pull request to your repository, or deploy merged pull requests to production.

GitHub Actions goes beyond just DevOps and lets you run workflows when other events happen in your repository. For example, you can run a workflow to automatically add the appropriate labels whenever someone creates a new issue in your repository.

GitHub provides Linux, Windows, and macOS virtual machines to run your workflows, or you can host your own self-hosted runners in your own data center or cloud infrastructure.

You must host your own Linux, Windows, or macOS virtual machines to run workflows for GitHub.

For more information about introducing GitHub Actions to your enterprise, see AUTOTITLE.

## The components of GitHub Actions

You can configure a GitHub Actions **workflow** to be triggered when an **event** occurs in your repository, such as a pull request being opened or an issue being created. Your workflow contains one or more **jobs** which can run in sequential order or in parallel. Each job will run inside its own virtual machine **runner**, or inside a container, and has one or more **steps** that either run a script that you define or run an **action**, which is a reusable extension that can simplify your workflow.

### Workflows

You can reference a workflow within another workflow. For more information, see AUTOTITLE.

For more information, see AUTOTITLE.

### Events

An **event** is a specific activity in a repository that triggers a **workflow** run. For example, an activity can originate from GitHub when someone creates a pull request, opens an issue, or pushes a commit to a repository. You can also trigger a workflow to run on a schedule, by posting to a REST API, or manually.

For a complete list of events that can be used to trigger workflows, see Events that trigger workflows.

### Jobs

A **job** is a set of **steps** in a workflow that is executed on the same **runner**. Each step is either a shell script that will be executed, or an **action** that will be run. Steps are executed in order and are dependent on each other. Since each step is executed on the same runner, you can share data from one step to another. For example, you can have a step that builds your application followed by a step that tests the application that was built.

Steps run in order by default, but you can also run selected steps concurrently when your workflow benefits from parallel execution, such as starting a long-running service while later steps continue. For more information, see AUTOTITLE.

You can configure a job's dependencies with other jobs; by default, jobs have no dependencies and run in parallel. When a job takes a dependency on another job, it waits for the dependent job to complete before running.

You can also use a **matrix** to run the same job multiple times, each with a different combination of variables—like operating systems or language versions.

For example, you might configure multiple build jobs for different architectures without any job dependencies and a packaging job that depends on those builds. The build jobs run in parallel, and once they complete successfully, the packaging job runs.

For more information, see AUTOTITLE.

### Actions

An **action** is a pre-defined, reusable set of jobs or code that performs specific tasks within a **workflow**, reducing the amount of repetitive code you write in your workflow files. Actions can perform tasks such as:

* Pulling your Git repository from GitHub
* Setting up the correct toolchain for your build environment
* Setting up authentication to your cloud provider

You can write your own actions, or you can find actions to use in your workflows in the GitHub.

For more information on actions, see AUTOTITLE.

### Runners

A **runner** is a server that runs your workflows when they're triggered. Each runner can run a single **job** at a time.
 You must host your own runners for GitHub Enterprise Server.
GitHub provides Ubuntu Linux, Microsoft Windows, and macOS runners to run your **workflows**. Each workflow run executes in a fresh, newly-provisioned virtual machine.

 GitHub also offers GitHubs, which are available in larger configurations. For more information, see AUTOTITLE.

If you need a different operating system or require a specific hardware configuration, you can host your own runners.

For more information about self-hosted runners, see AUTOTITLE.

## Next steps

> [!NOTE]
> For automations that require contextual judgment about your repository's content, you can also author GitHub in natural language instead of a traditional GitHub Actions workflow. For more information, see AUTOTITLE and AUTOTITLE.

## Further reading

* AUTOTITLE
