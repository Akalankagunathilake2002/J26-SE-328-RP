<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/concepts/runners/self-hosted-runners -->
# Self-hosted runners

You can host your own runners and customize the environment used to run jobs in your GitHub Actions workflows.

A self-hosted runner is a system that you deploy and manage to execute jobs from GitHub Actions on GitHub.

Self-hosted runners:

* Give you more control of hardware, operating system, and software tools than GitHub-hosted runners provide. Be aware that you are responsible for updating the operating system and all other software.
* Allow you to use machines and services that your company already maintains and pays to use.
* Are free to use with GitHub Actions, but you are responsible for the cost of maintaining your runner machines.
* Let you create custom hardware configurations that meet your needs with processing power or memory to run larger jobs, install software available on your local network.
* Receive automatic updates for the self-hosted runner application only, though you may disable automatic updates of the runner.
* Don't need to have a clean instance for every job execution.
* Can be organized into groups to restrict access to specific workflows, organizations, and repositories. See AUTOTITLE.
* Can be physical, virtual, in a container, on-premises, or in a cloud.

You can use self-hosted runners anywhere in the management hierarchy. Repository-level runners are dedicated to a single repository, while organization-level runners can process jobs for multiple repositories in an organization. Organization owners can choose which repositories are allowed to create repository-level self-hosted runners. See AUTOTITLE. Finally, enterprise-level runners can be assigned to multiple organizations in an enterprise account.

## Next steps

To get hands-on experience with the policies and usage of self-hosted runners, see AUTOTITLE

To set up a self-hosted runner in your workspace, see AUTOTITLE.

To find information about the requirements and supported software and hardware for self-hosted runners, see AUTOTITLE.
