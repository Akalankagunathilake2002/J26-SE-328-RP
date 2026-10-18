<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/get-started/continuous-deployment -->
# Continuous deployment

You can create custom continuous deployment (CD) workflows directly in your GitHub repository with GitHub Actions.

## About continuous deployment

_Continuous deployment_ (CD) is the practice of using automation to publish and deploy software updates. As part of the typical CD process, the code is automatically built and tested before deployment.

Continuous deployment is often coupled with continuous integration. For more information about continuous integration, see AUTOTITLE.

## About continuous deployment using GitHub Actions

You can set up a GitHub Actions workflow to deploy your software product. To verify that your product works as expected, your workflow can build the code in your repository and run your tests before deploying.

You can configure your CD workflow to run when an event occurs (for example, when new code is pushed to the default branch of your repository), on a set schedule, manually, or when an external event occurs using the repository dispatch webhook. For more information about when your workflow can run, see AUTOTITLE.

GitHub Actions provides features that give you more control over deployments. For example, you can use environments to require approval for a job to proceed, restrict which branches can trigger a workflow, or limit access to secrets. You can use concurrency to limit your CD pipeline to a maximum of one in-progress deployment and one pending deployment. For more information about these features, see AUTOTITLE and AUTOTITLE.

> [!TIP]
> You can use GitHub for deployment preparation, such as release notes, change analysis, and rollout summaries, while keeping production deployments in deterministic GitHub Actions workflows. For more information, see AUTOTITLE.

## Workflow templates and third-party actions

## Next steps

If your GitHub Actions workflows need to access resources from a cloud provider that supports OpenID Connect (OIDC), you can configure your workflows to authenticate directly to the cloud provider. This will let you stop storing these credentials as long-lived secrets and provide other security benefits. For more information, see AUTOTITLE.
