<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/tutorials/manage-your-work/add-labels-to-issues -->
# Adding labels to issues

You can use GitHub Actions to automatically label issues.

## Introduction

This tutorial demonstrates how to use the GitHub CLI in a workflow to label newly opened or reopened issues. For example, you can add the `triage` label every time an issue is opened or reopened. Then, you can see all issues that need to be triaged by filtering for issues with the `triage` label.

The GitHub CLI allows you to easily use the GitHub API in a workflow.

In the tutorial, you will first make a workflow file that uses the GitHub CLI. Then, you will customize the workflow to suit your needs.

## Creating the workflow

1.
1.
1. Copy the following YAML contents into your workflow file.

    ```yaml copy
    name: Label issues
    on:
      issues:
        types:
          - reopened
          - opened
    jobs:
      label_issues:
        runs-on: ubuntu-latest
        permissions:
          issues: write
        steps:
          - run: gh issue edit "$NUMBER" --add-label "$LABELS"
            env:
              GH_TOKEN: $
              GH_REPO: $
              NUMBER: $
              LABELS: triage
    ```

1. Customize the `env` values in your workflow file:
   * The `GH_TOKEN`, `GH_REPO`, and `NUMBER` values are automatically set using the `github` and `secrets` contexts. You do not need to change these.
   * Change the value for `LABELS` to the list of labels that you want to add to the issue. The label(s) must exist for your repository. Separate multiple labels with commas. For example, `help wanted,good first issue`. For more information about labels, see AUTOTITLE.
1.

## Testing the workflow

Every time an issue in your repository is opened or reopened, this workflow will add the labels that you specified to the issue.

Test out your workflow by creating an issue in your repository.

1. Create an issue in your repository. For more information, see AUTOTITLE.
1. To see the workflow run that was triggered by creating the issue, view the history of your workflow runs. For more information, see AUTOTITLE.
1. When the workflow completes, the issue that you created should have the specified labels added.

## Next steps

* To learn more about additional things you can do with the GitHub CLI, see the GitHub CLI manual.
* To learn more about different events that can trigger your workflow, see AUTOTITLE.
* Search GitHub for examples of workflows using `gh issue edit`.
