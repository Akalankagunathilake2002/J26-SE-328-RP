<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/tutorials/build-and-test-code/net -->
# Building and testing .NET

Learn how to create a continuous integration (CI) workflow to build and test your .NET project.

## Introduction

This guide shows you how to build, test, and publish a .NET package.

 GitHub-hosted runners have a tools cache with preinstalled software, which includes the .NET Core SDK. For a full list of up-to-date software and the preinstalled versions of .NET Core SDK, see software installed on GitHub-hosted runners.

## Prerequisites

You should already be familiar with YAML syntax and how it's used with GitHub Actions. For more information, see AUTOTITLE.

We recommend that you have a basic understanding of the .NET Core SDK. For more information, see Getting started with .NET.

## Using a .NET workflow template

GitHub provides a workflow template for .NET that should work for most .NET projects. The subsequent sections of this guide give examples of how you can customize this workflow template.

1. The "Choose a workflow" page shows a selection of recommended workflow templates. Search for "dotnet".
1. On the ".NET" workflow, click **Configure**.

   If you don't find the ".NET" workflow template, copy the following workflow code to a new file called `dotnet.yml` in the `.github/workflows` directory of your repository.

   ```yaml copy
   name: .NET

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
       - name: Setup .NET
         uses:
         with:
           dotnet-version: 6.0.x
       - name: Restore dependencies
         run: dotnet restore
       - name: Build
         run: dotnet build --no-restore
       - name: Test
         run: dotnet test --no-build --verbosity normal
   ```

1. Edit the workflow as required. For example, change the .NET version.
1. Click **Commit changes**.

   The `dotnet.yml` workflow file is added to the `.github/workflows` directory of your repository.

## Specifying a .NET version

To use a preinstalled version of the .NET Core SDK on a GitHub-hosted runner, use the `setup-dotnet` action. This action finds a specific version of .NET from the tools cache on each runner, and adds the necessary binaries to `PATH`. These changes will persist for the remainder of the job.

The `setup-dotnet` action is the recommended way of using .NET with GitHub Actions, because it ensures consistent behavior across different runners and different versions of .NET. If you are using a self-hosted runner, you must install .NET and add it to `PATH`. For more information, see the `setup-dotnet` action.

### Using multiple .NET versions

```yaml
name: dotnet package

on: [push]

jobs:
  build:

    runs-on: ubuntu-latest
    strategy:
      matrix:
        dotnet-version: [ '3.1.x', '6.0.x' ]

    steps:
      - uses:
      - name: Setup dotnet $
        uses:
        with:
          dotnet-version: $
      # You can test your matrix by printing the current dotnet version
      - name: Display dotnet version
        run: dotnet --version
```

### Using a specific .NET version

You can configure your job to use a specific version of .NET, such as `6.0.22`. Alternatively, you can use semantic version syntax to get the latest minor release. This example uses the latest minor release of .NET 6.

```yaml
    - name: Setup .NET 6.x
      uses:
      with:
        # Semantic version range syntax or exact version of a dotnet version
        dotnet-version: '6.x'
```

## Installing dependencies

GitHub-hosted runners have the NuGet package manager installed. You can use the dotnet CLI to install dependencies from the NuGet package registry before building and testing your code. For example, the YAML below installs the `Newtonsoft` package.

```yaml
steps:
- uses:
- name: Setup dotnet
  uses:
  with:
    dotnet-version: '6.0.x'
- name: Install dependencies
  run: dotnet add package Newtonsoft.Json --version 12.0.1
```

### Caching dependencies

You can cache NuGet dependencies for future workflows using the optional `cache` input. Caching requires a `packages.lock.json` file. If the action cannot find a matching lock file, it fails.

Before enabling caching:

1. In the directory containing your project or solution, generate the lock files locally.

   ```shell
   dotnet restore --use-lock-file
   ```

1. Commit the generated `packages.lock.json` files to your repository so they are available when the workflow runs.

For more information, see Locking dependencies in the NuGet documentation.

By default, `setup-dotnet` looks for a lock file in the repository root. Use `cache-dependency-path` to specify lock files in subdirectories or multiple lock files. The following example caches the NuGet `global-packages` folder using lock files throughout the repository, then restores the dependencies in locked mode.

For more information, see AUTOTITLE.

```yaml
steps:
- uses:
- name: Setup dotnet
  uses:
  with:
    dotnet-version: '6.x'
    cache: true
    cache-dependency-path: '**/packages.lock.json'
- name: Restore dependencies
  run: dotnet restore --locked-mode
```

> [!NOTE]
> Depending on the number of dependencies, it may be faster to use the dependency cache. Projects with many large dependencies should see a performance increase as it cuts down the time required for downloading. Projects with fewer dependencies may not see a significant performance increase and may even see a slight decrease due to how NuGet installs cached dependencies. The performance varies from project to project.

## Building and testing your code

You can use the same commands that you use locally to build and test your code. This example demonstrates how to use `dotnet build` and `dotnet test` in a job:

```yaml
steps:
- uses:
- name: Setup dotnet
  uses:
  with:
    dotnet-version: '6.0.x'
- name: Install dependencies
  run: dotnet restore
- name: Build
  run: dotnet build --no-restore
- name: Test with the dotnet CLI
  run: dotnet test --no-build
```

## Packaging workflow data as artifacts

After a workflow completes, you can upload the resulting artifacts for analysis. For example, you may need to save log files, core dumps, test results, or screenshots. The following example demonstrates how you can use the `upload-artifact` action to upload test results.

For more information, see AUTOTITLE.

```yaml
name: dotnet package

on: [push]

jobs:
  build:

    runs-on: ubuntu-latest
    strategy:
      matrix:
        dotnet-version: [ '3.1.x', '6.0.x' ]

    steps:
      - uses:
      - name: Setup dotnet
        uses:
        with:
          dotnet-version: $
      - name: Install dependencies
        run: dotnet restore
      - name: Test with dotnet
        run: dotnet test --no-restore --logger trx --results-directory "TestResults-$"
      - name: Upload dotnet test results
        uses:
        with:
          name: dotnet-results-$
          path: TestResults-$
        # Use always() to always run this step to publish test results when there are test failures
        if: $
```

## Publishing to package registries

You can configure your workflow to publish your .NET package to a package registry when your CI tests pass. You can use repository secrets to store any tokens or credentials needed to publish your binary. The following example creates and publishes a package to GitHub using `dotnet core cli`.

```yaml
name: Upload dotnet package

on:
  release:
    types: [created]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      packages: write
      contents: read
    steps:
      - uses:
      - uses:
        with:
          dotnet-version: '6.0.x' # SDK Version to use.
          source-url: https://nuget.pkg.github.com//index.json
        env:
          NUGET_AUTH_TOKEN: $
      - run: dotnet build --configuration Release
      - name: Create the package
        run: dotnet pack --configuration Release
      - name: Publish the package to GPR
        run: dotnet nuget push /bin/Release/*.nupkg
```
