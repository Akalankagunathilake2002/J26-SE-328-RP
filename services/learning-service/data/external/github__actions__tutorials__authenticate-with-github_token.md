<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/tutorials/authenticate-with-github_token -->
# Use GITHUB_TOKEN for authentication in workflows

Learn how to use the `GITHUB_TOKEN` to authenticate on behalf of GitHub Actions.

This tutorial leads you through how to use the `GITHUB_TOKEN` for authentication in GitHub Actions workflows, including examples for passing the token to actions, making API requests, and configuring permissions for secure automation.

For reference information, see AUTOTITLE.

## Using the `GITHUB_TOKEN` in a workflow

You can use the `GITHUB_TOKEN` by using the standard syntax for referencing secrets: `$`. Examples of using the `GITHUB_TOKEN` include passing the token as an input to an action, or using it to make an authenticated GitHub API request.

> [!IMPORTANT]
> An action can access the `GITHUB_TOKEN` through the `github.token` context even if the workflow does not explicitly pass the `GITHUB_TOKEN` to the action. As a good security practice, you should always make sure that actions only have the minimum access they require by limiting the permissions granted to the `GITHUB_TOKEN`. For more information, see AUTOTITLE.

### Example 1: passing the `GITHUB_TOKEN` as an input

### Example 2: calling the REST API

You can use the `GITHUB_TOKEN` to make authenticated API calls. This example workflow creates an issue using the GitHub REST API:

```yaml
name: Create issue on commit

on: [ push ]

jobs:
  create_issue:
    runs-on: ubuntu-latest
    permissions:
      issues: write
    steps:
      - name: Create issue using REST API
        run: |
          curl --request POST \
          --url GitHub/repos/$/issues \
          --header 'authorization: Bearer $' \
          --header 'content-type: application/json' \
          --data '{
            "title": "Automated issue for commit: $",
            "body": "This issue was automatically created by the GitHub Action workflow **$**. \n\n The commit hash was: _$_."
            }' \
          --fail
```

## Modifying the permissions for the `GITHUB_TOKEN`

Use the `permissions` key in your workflow file to modify permissions for the `GITHUB_TOKEN` for an entire workflow or for individual jobs. This allows you to configure the minimum required permissions for a workflow or job. As a good security practice, you should grant the `GITHUB_TOKEN` the least required access.

 To see the list of permissions available for use and their parameterized names, see AUTOTITLE.

The two workflow examples earlier in this article show the `permissions` key being used at the job level.

## Granting additional permissions

If you need a token that requires permissions that aren't available in the `GITHUB_TOKEN`, create a GitHub and generate an installation access token within your workflow. For more information, see AUTOTITLE. Alternatively, you can create a GitHub, store it as a secret in your repository, and use the token in your workflow with the `$` syntax. For more information, see AUTOTITLE and AUTOTITLE.

## Next steps

* AUTOTITLE
* AUTOTITLE
