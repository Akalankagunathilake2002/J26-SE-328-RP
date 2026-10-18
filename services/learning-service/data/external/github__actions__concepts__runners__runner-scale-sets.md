<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/concepts/runners/runner-scale-sets -->
# Runner scale sets

Learn about what a runner scale set is and how they can interact with the GitHub.

## About runner scale sets

A runner scale set is a group of homogeneous runners that can be assigned jobs from GitHub Actions. The number of active runners owned by a runner scale set can be controlled by auto-scaling runner solutions such as GitHub (ARC).

You can use runner groups to manage runner scale sets. Similar to self-hosted runners, you can add runner scale sets to existing runner groups. However, runner scale sets can belong to only one runner group at a time. A runner scale set can have more than one label, and workflows can target it by its name or by its labels in `runs-on`. Support for multiple labels was added in Actions Runner Controller 0.14.0.

To assign jobs to a runner scale set, you must configure your workflow to reference the runner scale set’s name. For more information, see AUTOTITLE.

## Legal notice

## Next steps

* For more information about the GitHub as a concept, see AUTOTITLE.
* To learn about runner groups, see AUTOTITLE.
