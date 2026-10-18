<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/get-started/quickstart -->
# Quickstart for GitHub Actions

Try out the core features of GitHub Actions in minutes.

## Introduction

 You can create workflows that run tests whenever you push a change to your repository, or that deploy merged pull requests to production.

This quickstart guide shows you how to use the user interface of GitHub to add a workflow that demonstrates some of the essential features of GitHub Actions.

For an overview of GitHub Actions workflows, see AUTOTITLE. If you want to learn about the various components that make up GitHub Actions, see AUTOTITLE.

## Using workflow templates

## Prerequisites

This guide assumes that:
* You have at least a basic knowledge of how to use GitHub. If you don't, you'll find it helpful to read some of the articles in the documentation for repositories and pull requests first. For example, see AUTOTITLE, AUTOTITLE, and AUTOTITLE.
* You have a repository on GitHub where you can add files.
* You have access to GitHub Actions.

  > [!NOTE] If the ** Actions** tab is not displayed under the name of your repository on GitHub, it may be because Actions is disabled for the repository. For more information, see AUTOTITLE.

## Creating your first workflow

1. In your repository on GitHub, create a workflow file called `github-actions-demo.yml` in the `.github/workflows` directory. To do this:
   * If the `.github/workflows` directory already exists, navigate to that directory on GitHub, click **Add file**, then click **Create new file**, and name the file `github-actions-demo.yml`.
   * If your repository doesn't have a `.github/workflows` directory, go to the main page of the repository on GitHub, click **Add file**, then click **Create new file**, and name the file `.github/workflows/github-actions-demo.yml`. This creates the `.github` and `workflows` directories and the `github-actions-demo.yml` file in a single step.

   > [!NOTE]
   > For GitHub to discover any GitHub Actions workflows in your repository, you must save the workflow files in a directory called `.github/workflows`.
   >
   > You can give the workflow file any name you like, but you must use `.yml` or `.yaml` as the file name extension. YAML is a markup language that's commonly used for configuration files.

1. Copy the following YAML contents into the `github-actions-demo.yml` file:

   ```yaml copy
   name: GitHub Actions Demo
   run-name: $ is testing out GitHub Actions 🚀
   on: [push]
   jobs:
     Explore-GitHub-Actions:
       runs-on: ubuntu-latest
       steps:
         - run: echo "🎉 The job was automatically triggered by a $ event."
         - run: echo "🐧 This job is now running on a $ server hosted by GitHub!"
         - run: echo "🔎 The name of your branch is $ and your repository is $."
         - name: Check out repository code
           uses:
         - run: echo "💡 The $ repository has been cloned to the runner."
         - run: echo "🖥️ The workflow is now ready to test your code on the runner."
         - name: List files in the repository
           run: |
             ls $
         - run: echo "🍏 This job's status is $."
   ```

   At this stage you don't need to understand the details of this workflow. For now, you can just copy and paste the contents into the file. After completing this quickstart guide, you can learn about the syntax of workflow files in AUTOTITLE, and for an explanation of GitHub Actions contexts, such as `$` and `$`, see AUTOTITLE.

1. Click **Commit changes**.
1. In the "Propose changes" dialog, select either the option to commit to the default branch or the option to create a new branch and start a pull request. Then click **Commit changes** or **Propose changes**.

Committing the workflow file to a branch in your repository triggers the `push` event and runs your workflow.

If you chose to start a pull request, you can continue and create the pull request, but this is not necessary for the purposes of this quickstart because the commit has still been made to a branch and will trigger the new workflow.

## Viewing your workflow results

1. In the left sidebar, click the workflow you want to display, in this example "GitHub Actions Demo."

1. From the list of workflow runs, click the name of the run you want to see, in this example "USERNAME is testing out GitHub Actions."
1. In the left sidebar of the workflow run page, under **Jobs**, click the **Explore-GitHub-Actions** job.

1. The log shows you how each of the steps was processed. Expand any of the steps to view its details.

   For example, you can see the list of files in your repository:

The example workflow you just added is triggered each time code is pushed to the branch, and shows you how GitHub Actions can work with the contents of your repository. For an in-depth tutorial, see AUTOTITLE.

## Next steps
