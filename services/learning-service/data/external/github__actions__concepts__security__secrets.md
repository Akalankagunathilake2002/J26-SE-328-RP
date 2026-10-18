<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/concepts/security/secrets -->
# Secrets

Learn about secrets as they are used in GitHub Actions workflows.

## About secrets

Secrets allow you to store sensitive information in your organization, repository, or repository environments. Secrets are variables that you create to use in GitHub Actions workflows in an organization, repository, or repository environment.

GitHub Actions can only read a secret if you explicitly include the secret in a workflow.

## How secrets work

Secrets use Libsodium sealed boxes, so that they are encrypted before reaching GitHub. This occurs when the secret is submitted using the UI or through the REST API. This client-side encryption helps minimize the risks related to accidental logging (for example, exception logs and request logs, among others) within GitHub's infrastructure. Once the secret is uploaded, GitHub is then able to decrypt it so that it can be injected into the workflow runtime.

## Organization-level secrets

When creating a secret for an organization, you can use a policy to limit access by repository. For example, you can grant access to all repositories, or limit access to only private repositories or a specified list of repositories.

For environment secrets, you can enable required reviewers to control access to the secrets. A workflow job cannot access environment secrets until approval is granted by required approvers.

To make a secret available to an action, you must set the secret as an input or environment variable in your workflow file. Review the action's README file to learn about which inputs and environment variables the action expects. See AUTOTITLE.

## Limiting credential permissions

When generating credentials, we recommend that you grant the minimum permissions possible. For example, instead of using personal credentials, use deploy keys or a service account. Consider granting read-only permissions if that's all that is needed, and limit access as much as possible.

When generating a , select the fewest scopes necessary. When generating a , select the minimum permissions and repository access required.

Instead of using a GitHub, consider using a GitHub, which uses fine-grained permissions and short lived tokens, similar to a . Unlike a GitHub, a GitHub is not tied to a user, so the workflow will continue to work even if the user who installed the app leaves your organization. For more information, see AUTOTITLE.

## Automatically redacted secrets

GitHub Actions automatically redacts the contents of all GitHub secrets that are printed to workflow logs.

GitHub Actions also redacts information that is recognized as sensitive, but is not stored as a secret. For a list of automatically redacted secrets, see AUTOTITLE.

Because there are multiple ways a secret value can be transformed, this redaction is not guaranteed. Additionally, the runner can only redact secrets used within the current job. As a result, there are certain security proactive steps you should follow to help ensure secrets are redacted, and to limit other risks associated with secrets. For a reference list of security best practices with secrets, see AUTOTITLE.

## Further reading

* AUTOTITLE
* AUTOTITLE
