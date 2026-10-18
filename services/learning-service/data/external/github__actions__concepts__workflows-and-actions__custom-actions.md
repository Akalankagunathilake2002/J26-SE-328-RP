<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/concepts/workflows-and-actions/custom-actions -->
# About custom actions

Actions are individual tasks that you can combine to create jobs and customize your workflow. You can create your own actions, or use and customize actions shared by the GitHub community.

## About custom actions

You can create actions by writing custom code that interacts with your repository in any way you'd like, including integrating with GitHub's APIs and any publicly available third-party API. For example, an action can publish npm modules, send SMS alerts when urgent issues are created, or deploy production-ready code.

You can write your own actions to use in your workflow or share the actions you build with the GitHub community. To share actions you've built with everyone, your repository must be public. To share actions only within your enterprise, your repository must be internal.

Actions can run directly on a machine or in a Docker container. You can define an action's inputs, outputs, and environment variables.

## Types of actions

| Type | Linux | macOS | Windows |
| ---- | ----- | ----- | -------- |
| Docker container |  |  |  |
| JavaScript |  |  |  |
| Composite Actions |  |  |  |

### Docker container actions

Docker containers package the environment with the GitHub Actions code. This creates a more consistent and reliable unit of work because the consumer of the action does not need to worry about the tools or dependencies.

A Docker container allows you to use specific versions of an operating system, dependencies, tools, and code. For actions that must run in a specific environment configuration, Docker is an ideal option because you can customize the operating system and tools. Because of the latency to build and retrieve the container, Docker container actions are slower than JavaScript actions.

Docker container actions can only execute on runners with a Linux operating system.

### JavaScript actions

JavaScript actions can run directly on a runner machine, and separate the action code from the environment used to run the code. Using a JavaScript action simplifies the action code and executes faster than a Docker container action.

If you're developing a Node.js project, the GitHub Actions Toolkit provides packages that you can use in your project to speed up development. For more information, see the actions/toolkit repository.

### Composite Actions

A _composite_ action allows you to combine multiple workflow steps within one action. For example, you can use this feature to bundle together multiple run commands into an action, and then have a workflow that executes the bundled commands as a single step using that action. To see an example, check out AUTOTITLE.

## Next steps

To learn about how to manage your custom actions, see AUTOTITLE.
