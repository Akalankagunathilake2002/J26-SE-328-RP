<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/tutorials/publish-packages/publish-java-packages-with-maven -->
# Publishing Java packages with Maven

In this tutorial, you'll learn how to use Maven to publish Java packages to a registry as part of your continuous integration (CI) workflow.

## Introduction

## Prerequisites

We recommend that you have a basic understanding of workflow files and configuration options. For more information, see AUTOTITLE.

For more information about creating a CI workflow for your Java project with Maven, see AUTOTITLE.

You may also find it helpful to have a basic understanding of the following:

* AUTOTITLE
* AUTOTITLE
* AUTOTITLE
* AUTOTITLE

## About package configuration

The `groupId` and `artifactId` fields in the _pom.xml_ file create a unique identifier for your package that registries use to link your package to a registry. For more information see Guide to uploading artifacts to the Central Repository in the Apache Maven documentation.

The _pom.xml_ file also contains configuration for the distribution management repositories that Maven will deploy packages to. Each repository must have a name and a deployment URL. Authentication for these repositories can be configured in the _.m2/settings.xml_ file in the home directory of the user running Maven.

You can use the `setup-java` action to configure the deployment repository as well as authentication for that repository. For more information, see `setup-java`.

## Publishing packages to the Maven Central Repository

Each time you create a new release, you can trigger a workflow to publish your package. The workflow in the example below runs when the `release` event triggers with type `created`. The workflow publishes the package to the Maven Central Repository if CI tests pass. For more information on the `release` event, see AUTOTITLE.

In this workflow, you can use the `setup-java` action. This action installs the given version of the JDK into the `PATH`, but it also configures a Maven _settings.xml_ for publishing packages. By default, the settings file will be configured for GitHub, but it can be configured to deploy to another package registry, such as the Maven Central Repository. If you already have a distribution management repository configured in _pom.xml_, then you can specify that `id` during the `setup-java` action invocation.

For example, if you were deploying to the Maven Central Repository through the OSSRH hosting project, your _pom.xml_ could specify a distribution management repository with the `id` of `ossrh`.

```xml copy

  ...

      ossrh
      Central Repository OSSRH
      https://oss.sonatype.org/service/local/staging/deploy/maven2/

```

With this configuration, you can create a workflow that publishes your package to the Maven Central Repository by specifying the repository management `id` to the `setup-java` action. You’ll also need to provide environment variables that contain the username and password to authenticate to the repository.

In the deploy step, you’ll need to set the environment variables to the username that you authenticate with to the repository, and to a secret that you’ve configured with the password or token to authenticate with. For more information, see AUTOTITLE.

```yaml copy
name: Publish package to the Maven Central Repository
on:
  release:
    types: [created]
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses:
      - name: Set up Maven Central Repository
        uses:
        with:
          java-version: '11'
          distribution: 'temurin'
          server-id: ossrh
          server-username: MAVEN_USERNAME
          server-password: MAVEN_PASSWORD
      - name: Publish package
        run: mvn --batch-mode deploy
        env:
          MAVEN_USERNAME: $
          MAVEN_PASSWORD: $
```

This workflow performs the following steps:

1. Checks out a copy of project's repository.
1. Sets up the Java JDK, and also configures the Maven _settings.xml_ file to add authentication for the `ossrh` repository using the `MAVEN_USERNAME` and `MAVEN_PASSWORD` environment variables.
1.

   For more information about using secrets in your workflow, see AUTOTITLE.

## Publishing packages to GitHub

Each time you create a new release, you can trigger a workflow to publish your package. The workflow in the example below runs when the `release` event triggers with type `created`. The workflow publishes the package to GitHub if CI tests pass. For more information on the `release` event, see AUTOTITLE.

In this workflow, you can use the `setup-java` action. This action installs the given version of the JDK into the `PATH`, and also sets up a Maven _settings.xml_ for publishing the package to GitHub. The generated _settings.xml_ defines authentication for a server with an `id` of `github`, using the `GITHUB_ACTOR` environment variable as the username and the `GITHUB_TOKEN` environment variable as the password. The `GITHUB_TOKEN` environment variable is assigned the value of the special `GITHUB_TOKEN` secret.

For a Maven-based project, you can make use of these settings by creating a distribution repository in your _pom.xml_ file with an `id` of `github` that points to your GitHub endpoint.

For example, if your organization is named "octocat" and your repository is named "hello-world", then the GitHub configuration in _pom.xml_ would look similar to the below example.

```xml copy

  ...

      github
      GitHub Packages
      https://maven.pkg.github.com/octocat/hello-world

```

With this configuration, you can create a workflow that publishes your package to GitHub by making use of the automatically generated _settings.xml_.

```yaml copy
name: Publish package to GitHub Packages
on:
  release:
    types: [created]
jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses:
      - uses:
        with:
          java-version: '11'
          distribution: 'temurin'
      - name: Publish package
        run: mvn --batch-mode deploy
        env:
          GITHUB_TOKEN: $
```

This workflow performs the following steps:

1. Checks out a copy of project's repository.
1. Sets up the Java JDK, and also automatically configures the Maven _settings.xml_ file to add authentication for the `github` Maven repository to use the `GITHUB_TOKEN` environment variable.
1.

   For more information about using secrets in your workflow, see AUTOTITLE.

## Publishing packages to the Maven Central Repository and GitHub

You can publish your packages to both the Maven Central Repository and GitHub by using the `setup-java` action for each registry.

Ensure your _pom.xml_ file includes a distribution management repository for both your GitHub repository and your Maven Central Repository provider. For example, if you deploy to the Central Repository through the OSSRH hosting project, you might want to specify it in a distribution management repository with the `id` set to `ossrh`, and you might want to specify GitHub in a distribution management repository with the `id` set to `github`.

```yaml copy
name: Publish package to the Maven Central Repository and GitHub Packages
on:
  release:
    types: [created]
jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses:
      - name: Set up Java for publishing to Maven Central Repository
        uses:
        with:
          java-version: '11'
          distribution: 'temurin'
          server-id: ossrh
          server-username: MAVEN_USERNAME
          server-password: MAVEN_PASSWORD
      - name: Publish to the Maven Central Repository
        run: mvn --batch-mode deploy
        env:
          MAVEN_USERNAME: $
          MAVEN_PASSWORD: $
      - name: Set up Java for publishing to GitHub Packages
        uses:
        with:
          java-version: '11'
          distribution: 'temurin'
      - name: Publish to GitHub Packages
        run: mvn --batch-mode deploy
        env:
          GITHUB_TOKEN: $
```

This workflow calls the `setup-java` action twice. Each time the `setup-java` action runs, it overwrites the Maven _settings.xml_ file for publishing packages. For authentication to the repository, the _settings.xml_ file references the distribution management repository `id`, and the username and password.

This workflow performs the following steps:

1. Checks out a copy of project's repository.
1. Calls `setup-java` the first time. This configures the Maven _settings.xml_ file for the `ossrh` repository, and sets the authentication options to environment variables that are defined in the next step.
1.
1. Calls `setup-java` the second time. This automatically configures the Maven _settings.xml_ file for GitHub.
1.

   For more information about using secrets in your workflow, see AUTOTITLE.
