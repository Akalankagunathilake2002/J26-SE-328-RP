<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/tutorials/publish-packages/publish-java-packages-with-gradle -->
# Publishing Java packages with Gradle

In this tutorial, you'll learn how to use Gradle to publish Java packages to a registry as part of your continuous integration (CI) workflow.

## Introduction

## Prerequisites

We recommend that you have a basic understanding of workflow files and configuration options. For more information, see AUTOTITLE.

For more information about creating a CI workflow for your Java project with Gradle, see AUTOTITLE.

You may also find it helpful to have a basic understanding of the following:

* AUTOTITLE
* AUTOTITLE
* AUTOTITLE
* AUTOTITLE

## About package configuration

The `groupId` and `artifactId` fields in the `MavenPublication` section of the _build.gradle_ file create a unique identifier for your package that registries use to link your package to a registry. This is similar to the `groupId` and `artifactId` fields of the Maven _pom.xml_ file. For more information, see the Maven Publish Plugin in the Gradle documentation.

The _build.gradle_ file also contains configuration for the distribution management repositories that Gradle will publish packages to. Each repository must have a name, a deployment URL, and credentials for authentication.

## Publishing packages to the Maven Central Repository

Each time you create a new release, you can trigger a workflow to publish your package. The workflow in the example below runs when the `release` event triggers with type `created`. The workflow publishes the package to the Maven Central Repository if CI tests pass. For more information on the `release` event, see AUTOTITLE.

You can define a new Maven repository in the publishing block of your _build.gradle_ file that points to your package repository. For example, if you were deploying to the Maven Central Repository through the OSSRH hosting project, your _build.gradle_ could specify a repository with the name `"OSSRH"`.

```groovy copy
plugins {
  ...
  id 'maven-publish'
}

publishing {
  ...

  repositories {
    maven {
      name = "OSSRH"
      url = "https://oss.sonatype.org/service/local/staging/deploy/maven2/"
      credentials {
        username = System.getenv("MAVEN_USERNAME")
        password = System.getenv("MAVEN_PASSWORD")
      }
    }
  }
}
```

With this configuration, you can create a workflow that publishes your package to the Maven Central Repository by running the `gradle publish` command. In the deploy step, you’ll need to set environment variables for the username and password or token that you use to authenticate to the Maven repository. For more information, see AUTOTITLE.

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
      - name: Set up Java
        uses:
        with:
          java-version: '11'
          distribution: 'temurin'

      - name: Setup Gradle
        uses: gradle/actions/setup-gradle@017a9effdb900e5b5b2fddfb590a105619dca3c3 # v4.4.2

      - name: Publish package
        run: ./gradlew publish
        env:
          MAVEN_USERNAME: $
          MAVEN_PASSWORD: $
```

1. Executes the Gradle `publish` task to publish to the `OSSRH` Maven repository. The `MAVEN_USERNAME` environment variable will be set with the contents of your `OSSRH_USERNAME` secret, and the `MAVEN_PASSWORD` environment variable will be set with the contents of your `OSSRH_TOKEN` secret.

   For more information about using secrets in your workflow, see AUTOTITLE.

## Publishing packages to GitHub

Each time you create a new release, you can trigger a workflow to publish your package. The workflow in the example below runs when the `release` event triggers with type `created`. The workflow publishes the package to GitHub if CI tests pass. For more information on the `release` event, see AUTOTITLE.

You can define a new Maven repository in the publishing block of your _build.gradle_ that points to GitHub. In that repository configuration, you can also take advantage of environment variables set in your CI workflow run. You can use the `GITHUB_ACTOR` environment variable as a username, and you can set the `GITHUB_TOKEN` environment variable with your `GITHUB_TOKEN` secret.

For example, if your organization is named "octocat" and your repository is named "hello-world", then the GitHub configuration in _build.gradle_ would look similar to the below example.

```groovy copy
plugins {
  ...
  id 'maven-publish'
}

publishing {
  ...

  repositories {
    maven {
      name = "GitHubPackages"
      url = "https://maven.pkg.github.com/octocat/hello-world"
      credentials {
        username = System.getenv("GITHUB_ACTOR")
        password = System.getenv("GITHUB_TOKEN")
      }
    }
  }
}
```

With this configuration, you can create a workflow that publishes your package to GitHub by running the `gradle publish` command.

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
      - name: Setup Gradle
        uses: gradle/actions/setup-gradle@017a9effdb900e5b5b2fddfb590a105619dca3c3 # v4.4.2

      - name: Publish package
        run: ./gradlew publish
        env:
          GITHUB_TOKEN: $
```

1. Executes the Gradle `publish` task to publish to GitHub. The `GITHUB_TOKEN` environment variable will be set with the content of the `GITHUB_TOKEN` secret. The `permissions` key specifies the access that the `GITHUB_TOKEN` secret will allow.

   For more information about using secrets in your workflow, see AUTOTITLE.

## Publishing packages to the Maven Central Repository and GitHub

You can publish your packages to both the Maven Central Repository and GitHub by configuring each in your _build.gradle_ file.

Ensure your _build.gradle_ file includes a repository for both your GitHub repository and your Maven Central Repository provider.

For example, if you deploy to the Central Repository through the OSSRH hosting project, you might want to specify it in a distribution management repository with the `name` set to `OSSRH`. If you deploy to GitHub, you might want to specify it in a distribution management repository with the `name` set to `GitHubPackages`.

If your organization is named "octocat" and your repository is named "hello-world", then the configuration in _build.gradle_ would look similar to the below example.

```groovy copy
plugins {
  ...
  id 'maven-publish'
}

publishing {
  ...

  repositories {
    maven {
      name = "OSSRH"
      url = "https://oss.sonatype.org/service/local/staging/deploy/maven2/"
      credentials {
        username = System.getenv("MAVEN_USERNAME")
        password = System.getenv("MAVEN_PASSWORD")
      }
    }
    maven {
      name = "GitHubPackages"
      url = "https://maven.pkg.github.com/octocat/hello-world"
      credentials {
        username = System.getenv("GITHUB_ACTOR")
        password = System.getenv("GITHUB_TOKEN")
      }
    }
  }
}
```

With this configuration, you can create a workflow that publishes your package to both the Maven Central Repository and GitHub by running the `gradle publish` command.

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
      - name: Set up Java
        uses:
        with:
          java-version: '11'
          distribution: 'temurin'
      - name: Setup Gradle
        uses: gradle/actions/setup-gradle@017a9effdb900e5b5b2fddfb590a105619dca3c3 # v4.4.2

      - name: Publish package
        run: ./gradlew publish
        env:
          MAVEN_USERNAME: $
          MAVEN_PASSWORD: $
          GITHUB_TOKEN: $
```

1. Executes the Gradle `publish` task to publish to the `OSSRH` Maven repository and GitHub. The `MAVEN_USERNAME` environment variable will be set with the contents of your `OSSRH_USERNAME` secret, and the `MAVEN_PASSWORD` environment variable will be set with the contents of your `OSSRH_TOKEN` secret. The `GITHUB_TOKEN` environment variable will be set with the content of the `GITHUB_TOKEN` secret. The `permissions` key specifies the access that the `GITHUB_TOKEN` secret will allow.

   For more information about using secrets in your workflow, see AUTOTITLE.
