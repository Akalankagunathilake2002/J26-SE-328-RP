<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts -->
# Workflow artifacts

Learn about storing and sharing data as artifacts of GitHub Actions workflows.

## About workflow artifacts

An artifact is a file or collection of files produced during a workflow run. Artifacts allow you to persist data after a job has completed, and share that data with another job in the same workflow. For example, you can use artifacts to save your build and test output after a workflow run has ended.

GitHub provides two actions that you can use to upload and download build artifacts, upload-artifact and download-artifact `upload-artifact` and `download-artifact` on GitHub Enterprise Server.

Common artifacts include:

* Log files and core dumps
* Test results, failures, and screenshots
* Binary or compressed files
* Stress test performance output and code coverage results

For more information on dependency caching, see AUTOTITLE.

## Generating artifact attestations for builds

You can access attestations after a build run, underneath the list of the artifacts the build produced.

For more information, see AUTOTITLE.
