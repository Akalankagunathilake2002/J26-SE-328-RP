<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/tutorials/build-and-test-code/java-with-maven -->
# Building and testing Java with Maven

Learn how to create a continuous integration (CI) workflow in GitHub Actions to build and test your Java project with Maven.

## Introduction

This guide shows you how to create a workflow that performs continuous integration (CI) for your Java project using the Maven software project management tool. The workflow you create will allow you to see when commits to a pull request cause build or test failures against your default branch; this approach can help ensure that your code is always healthy. You can extend your CI workflow to cache files and upload artifacts from a workflow run.

GitHub-hosted runners have a tools cache with pre-installed software, which includes Java Development Kits (JDKs) and Maven. For a list of software and the pre-installed versions for JDK and Maven, see AUTOTITLE.

## Prerequisites

You should be familiar with YAML and the syntax for GitHub Actions. For more information, see:
* AUTOTITLE
* AUTOTITLE

We recommend that you have a basic understanding of Java and the Maven framework. For more information, see the Maven Getting Started Guide in the Maven documentation.

## Using a Maven workflow template

GitHub provides a workflow template for Maven that should work for most Java with Maven projects. The subsequent sections of this guide give examples of how you can customize this workflow template.

1. The "Choose a workflow" page shows a selection of recommended workflow templates. Search for "Java with Maven".
1. On the "Java with Maven" workflow, click **Configure**.

   If you don't find the "Java with Maven" workflow template, copy the following workflow code to a new file called `maven.yml` in the `.github/workflows` directory of your repository.

   ```yaml copy

   name: Java CI with Maven

   on:
     push:
       branches: [ "main" ]
     pull_request:
       branches: [ "main" ]

   jobs:
     build:
       runs-on: ubuntu-latest

       steps:
       - uses:
       - name: Set up JDK 17
         uses:
         with:
           java-version: '17'
           distribution: 'temurin'
           cache: maven
       - name: Build with Maven
         run: mvn -B package --file pom.xml

       # Optional: Uploads the full dependency graph to GitHub to improve the quality of Dependabot alerts this repository can receive
       - name: Update dependency graph
         uses: advanced-security/maven-dependency-submission-action@571e99aab1055c2e71a1e2309b9691de18d6b7d6
   ```

1. Edit the workflow as required. For example, change the Java version.
1. Click **Commit changes**.

   The `maven.yml` workflow file is added to the `.github/workflows` directory of your repository.

## Building and testing your code

You can use the same commands that you use locally to build and test your code.

The workflow template will run the `package` target by default. In the default Maven configuration, this command will download dependencies, build classes, run tests, and package classes into their distributable format, for example, a JAR file.

If you use different commands to build your project, or you want to use a different target, you can specify those. For example, you may want to run the `verify` target that's configured in a `pom-ci.xml` file.

```yaml copy
steps:
  - uses:
  - uses:
    with:
      java-version: '17'
      distribution: 'temurin'
  - name: Run the Maven verify phase
    run: mvn --batch-mode --update-snapshots verify
```

## Caching dependencies

You can cache your dependencies to speed up your workflow runs. After a successful run, your local Maven repository will be stored in a cache. In future workflow runs, the cache will be restored so that dependencies don't need to be downloaded from remote Maven repositories. You can cache dependencies simply using the `setup-java` action or can use `cache` action for custom and more advanced configuration.

```yaml copy
steps:
  - uses:
  - name: Set up JDK 17
    uses:
    with:
      java-version: '17'
      distribution: 'temurin'
      cache: maven
  - name: Build with Maven
    run: mvn --batch-mode --update-snapshots verify
```

This workflow will save the contents of your local Maven repository, located in the `.m2` directory of the runner's home directory. The cache key will be the hashed contents of `pom.xml`, so changes to `pom.xml` will invalidate the cache.

## Packaging workflow data as artifacts

After your build has succeeded and your tests have passed, you may want to upload the resulting Java packages as a build artifact. This will store the built packages as part of the workflow run, and allow you to download them. Artifacts can help you test and debug pull requests in your local environment before they're merged. For more information, see AUTOTITLE.

Maven will usually create output files like JARs, EARs, or WARs in the `target` directory. To upload those as artifacts, you can copy them into a new directory that contains artifacts to upload. For example, you can create a directory called `staging`. Then you can upload the contents of that directory using the `upload-artifact` action.

```yaml copy
steps:
  - uses:
  - uses:
    with:
      java-version: '17'
      distribution: 'temurin'
  - run: mvn --batch-mode --update-snapshots verify
  - run: mkdir staging && cp target/*.jar staging
  - uses:
    with:
      name: Package
      path: staging
```
