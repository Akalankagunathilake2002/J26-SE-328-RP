<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/tutorials/manage-your-work/close-inactive-issues -->
# Closing inactive issues

You can use GitHub Actions to comment on or close issues that have been inactive for a certain period of time.

## Introduction

This tutorial demonstrates how to use the `actions/stale` action to comment on and close issues that have been inactive for a certain period of time. For example, you can comment if an issue has been inactive for 30 days to prompt participants to take action. Then, if no additional activity occurs after 14 days, you can close the issue.

In the tutorial, you will first make a workflow file that uses the `actions/stale` action. Then, you will customize the workflow to suit your needs.

## Creating the workflow

1.
1.
1. Copy the following YAML contents into your workflow file.

    ```yaml copy
    name: Close inactive issues
    on:
      schedule:
        - cron: "30 1 * * *"

    jobs:
      close-issues:
        runs-on: ubuntu-latest
        permissions:
          issues: write
          pull-requests: write
        steps:
          - uses:
            with:
              days-before-issue-stale: 30
              days-before-issue-close: 14
              stale-issue-label: "stale"
              stale-issue-message: "This issue is stale because it has been open for 30 days with no activity."
              close-issue-message: "This issue was closed because it has been inactive for 14 days since being marked as stale."
              days-before-pr-stale: -1
              days-before-pr-close: -1
              repo-token: $
    ```

1. Customize the parameters in your workflow file:
   * Change the value for `on.schedule` to dictate when you want this workflow to run. In the example above, the workflow will run every day at 1:30 UTC. For more information about scheduled workflows, see AUTOTITLE.
   * Change the value for `days-before-issue-stale` to the number of days without activity before the `actions/stale` action labels an issue. If you never want this action to label issues, set this value to `-1`.
   * Change the value for `days-before-issue-close` to the number of days without activity before the `actions/stale` action closes an issue. If you never want this action to close issues, set this value to `-1`.
   * Change the value for `stale-issue-label` to the label that you want to apply to issues that have been inactive for the amount of time specified by `days-before-issue-stale`.
   * Change the value for `stale-issue-message` to the comment that you want to add to issues that are labeled by the `actions/stale` action.
   * Change the value for `close-issue-message` to the comment that you want to add to issues that are closed by the `actions/stale` action.
1.

## Expected results

Based on the `schedule` parameter (for example, every day at 1:30 UTC), your workflow will find issues that have been inactive for the specified period of time and will add the specified comment and label. Additionally, your workflow will close any previously labeled issues if no additional activity has occurred for the specified period of time.

> [!NOTE]
>

You can view the history of your workflow runs to see this workflow run periodically. For more information, see AUTOTITLE.

This workflow will only label and/or close 30 issues at a time in order to avoid exceeding a rate limit. You can configure this with the `operations-per-run` setting. For more information, see the `actions/stale` action documentation.

## Next steps

* To learn more about additional things you can do with the `actions/stale` action, like closing inactive pull requests, ignoring issues with certain labels or milestones, or only checking issues with certain labels, see the `actions/stale` action documentation.
* Search GitHub for examples of workflows using this action.
