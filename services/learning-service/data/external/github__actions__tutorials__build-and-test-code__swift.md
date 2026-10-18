<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/tutorials/build-and-test-code/swift -->
# Building and testing Swift

Learn how to create a continuous integration (CI) workflow to build and test your Swift project.

## Introduction

This guide shows you how to build and test a Swift package.

GitHub-hosted runners have a tools cache with preinstalled software, and the Ubuntu and macOS runners include the dependencies for building Swift packages. For a full list of up-to-date software and the preinstalled versions of Swift and Xcode, see AUTOTITLE.

## Prerequisites

You should already be familiar with YAML syntax and how it's used with GitHub Actions. For more information, see AUTOTITLE.

We recommend that you have a basic understanding of Swift packages. For more information, see Swift Packages in the Apple developer documentation.

## Using a Swift workflow template

GitHub provides a workflow template for Swift that should work for most Swift projects. The subsequent sections of this guide give examples of how you can customize this workflow template.

1. The "Choose a workflow" page shows a selection of recommended workflow templates. Search for "swift".
1. Filter the selection of workflows by clicking **Continuous integration**.
1. On the "Swift" workflow, click **Configure**.

   If you don't find the "Swift" workflow template, copy the following workflow code to a new file called `swift.yml` in the `.github/workflows` directory of your repository.

   ```yaml copy
   name: Swift

   on:
     push:
       branches: [ "main" ]
     pull_request:
       branches: [ "main" ]

   jobs:
     build:
       runs-on: macos-latest

       steps:
       - uses:
       - name: Build
         run: swift build -v
       - name: Run tests
         run: swift test -v
   ```

1. Edit the workflow as required. For example, change the branch on which the workflow will run.
1. Click **Commit changes**.

   The `swift.yml` workflow file is added to the `.github/workflows` directory of your repository.

## Specifying a Swift version

To use a specific preinstalled version of Swift on a GitHub-hosted runner, use the `swift-actions/setup-swift` action. This action finds a specific version of Swift from the tools cache on the runner and adds the necessary binaries to `PATH`. These changes will persist for the remainder of a job. For more information, see the `swift-actions/setup-swift` action.

If you are using a self-hosted runner, you must install your desired Swift versions and add them to `PATH`.

The examples below demonstrate using the `swift-actions/setup-swift` action.

### Using multiple Swift versions

You can configure your job to use multiple versions of Swift in a matrix.

```yaml copy

name: Swift

on: [push]

jobs:
  build:
    name: Swift $ on $
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        swift: ["5.2", "5.3"]
    runs-on: $
    steps:
      - uses: swift-actions/setup-swift@65540b95f51493d65f5e59e97dcef9629ddf11bf
        with:
          swift-version: $
      - uses:
      - name: Build
        run: swift build
      - name: Run tests
        run: swift test
```

### Using a single specific Swift version

You can configure your job to use a single specific version of Swift, such as `5.3.3`.

```yaml copy

steps:
  - uses: swift-actions/setup-swift@65540b95f51493d65f5e59e97dcef9629ddf11bf
    with:
      swift-version: "5.3.3"
  - name: Get swift version
    run: swift --version # Swift 5.3.3
```

## Building and testing your code

You can use the same commands that you use locally to build and test your code using Swift. This example demonstrates how to use `swift build` and `swift test` in a job:

```yaml copy

steps:
  - uses:
  - uses: swift-actions/setup-swift@65540b95f51493d65f5e59e97dcef9629ddf11bf
    with:
      swift-version: "5.3.3"
  - name: Build
    run: swift build
  - name: Run tests
    run: swift test
```
