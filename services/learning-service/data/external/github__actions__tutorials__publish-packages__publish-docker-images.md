<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images -->
# Publishing Docker images

In this tutorial, you'll learn how to publish Docker images to a registry, such as Docker Hub or GitHub, as part of your continuous integration (CI) workflow.

## Introduction

This guide shows you how to create a workflow that performs a Docker build, and then publishes Docker images to Docker Hub or GitHub. With a single workflow, you can publish images to a single registry or to multiple registries.

> [!NOTE]
> If you want to push to another third-party Docker registry, the example in the Publishing images to GitHub section can serve as a good template.

## Prerequisites

We recommend that you have a basic understanding of workflow configuration options and how to create a workflow file. For more information, see AUTOTITLE.

You might also find it helpful to have a basic understanding of the following:

* AUTOTITLE
* AUTOTITLE
* AUTOTITLE
* AUTOTITLE

## About image configuration

This guide assumes that you have a complete definition for a Docker image stored in a GitHub repository. For example, your repository must contain a _Dockerfile_, and any other files needed to perform a Docker build to create an image.

 For more information, see AUTOTITLE.

In this guide, we will use the Docker `build-push-action` action to build the Docker image and push it to one or more Docker registries. For more information, see `build-push-action`.

## Publishing images to Docker Hub

Each time you create a new release on GitHub, you can trigger a workflow to publish your image. The workflow in the example below runs when the `release` event triggers with the `published` activity type.

In the example workflow below, we use the Docker `login-action` and `build-push-action` actions to build the Docker image and, if the build succeeds, push the built image to Docker Hub.

To push to Docker Hub, you will need to have a Docker Hub account, and have a Docker Hub repository created. For more information, see Pushing a Docker container image to Docker Hub in the Docker documentation.

The `login-action` options required for Docker Hub are:
* `username` and `password`: This is your Docker Hub username and password. We recommend storing your Docker Hub username and password as secrets so they aren't exposed in your workflow file. For more information, see AUTOTITLE.

The `metadata-action` option required for Docker Hub is:
* `images`: The namespace and name for the Docker image you are building/pushing to Docker Hub.

The `build-push-action` options required for Docker Hub are:
* `tags`: The tag of your new image in the format `DOCKER-HUB-NAMESPACE/DOCKER-HUB-REPOSITORY:VERSION`. You can set a single tag as shown below, or specify multiple tags in a list.
* `push`: If set to `true`, the image will be pushed to the registry if it is built successfully.

```yaml copy

name: Publish Docker image

on:
  release:
    types: [published]

jobs:
  push_to_registry:
    name: Push Docker image to Docker Hub
    runs-on: [self-hosted]ubuntu-latest
    permissions:
      packages: write
      contents: read
      attestations: write
      id-token: write
    steps:
      - name: Check out the repo
        uses:

      - name: Log in to Docker Hub
        uses: docker/login-action@f4ef78c080cd8ba55a85445d5b36e214a81df20a
        with:
          username: $
          password: $

      - name: Extract metadata (tags, labels) for Docker
        id: meta
        uses: docker/metadata-action@9ec57ed1fcdbf14dcef7dfbe97b2010124a938b7
        with:
          images: my-docker-hub-namespace/my-docker-hub-repository

      - name: Build and push Docker image
        id: push
        uses: docker/build-push-action@3b5e8027fcad23fda98b2e3ac259d8d67585f671
        with:
          context: .
          file: ./Dockerfile
          push: true
          tags: $
          labels: $

      - name: Generate artifact attestation
        uses: actions/attest@v4
        with:
          subject-name: index.docker.io/my-docker-hub-namespace/my-docker-hub-repository
          subject-digest: $
          push-to-registry: true

```

The above workflow checks out the GitHub repository, uses the `login-action` to log in to the registry, and then uses the `build-push-action` action to: build a Docker image based on your repository's `Dockerfile`; push the image to Docker Hub, and apply a tag to the image.

## Publishing images to GitHub

Each time you create a new release on GitHub, you can trigger a workflow to publish your image. The workflow in the example below runs when a change is pushed to the `release` branch.

In the example workflow below, we use the Docker `login-action`, `metadata-action`, and `build-push-action` actions to build the Docker image, and if the build succeeds, push the built image to GitHub.

The `login-action` options required for GitHub are:
* `registry`: Must be set to `ghcr.io```.
* `username`: You can use the `$` context to automatically use the username of the user that triggered the workflow run. For more information, see AUTOTITLE.
* `password`: You can use the automatically-generated `GITHUB_TOKEN` secret for the password. For more information, see AUTOTITLE.

The `metadata-action` option required for GitHub is:
* `images`: The namespace and name for the Docker image you are building.

The `build-push-action` options required for GitHub are:

* `context`: Defines the build's context as the set of files located in the specified path.
* `push`: If set to `true`, the image will be pushed to the registry if it is built successfully.
* `tags` and `labels`: These are populated by output from `metadata-action`.
* `tags`: Must be set in the format `/OWNER/REPOSITORY/IMAGE_NAME:VERSION`.

   For example, for an image named `octo-image` stored on GitHub Enterprise Server at `https://HOSTNAME/octo-org/octo-repo`, the `tags` option should be set to `/octo-org/octo-repo/octo-image:latest`
. You can set a single tag as shown below, or specify multiple tags in a list.

The above workflow is triggered by a push to the "release" branch. It checks out the GitHub repository, and uses the `login-action` to log in to the GitHub. It then extracts labels and tags for the Docker image. Finally, it uses the `build-push-action` action to build the image and publish it on the GitHub.

## Publishing images to Docker Hub and GitHub

In a single workflow, you can publish your Docker image to multiple registries by using the `login-action` and `build-push-action` actions for each registry.

The following example workflow uses the steps from the previous sections (Publishing images to Docker Hub and Publishing images to GitHub) to create a single workflow that pushes to both registries.

```yaml copy

name: Publish Docker image

on:
  release:
    types: [published]

jobs:
  push_to_registries:
    name: Push Docker image to multiple registries
    runs-on: [self-hosted]ubuntu-latest
    permissions:
      packages: write
      contents: read
    steps:
      - name: Check out the repo
        uses:

      - name: Log in to Docker Hub
        uses: docker/login-action@f4ef78c080cd8ba55a85445d5b36e214a81df20a
        with:
          username: $
          password: $

      - name: Log in to the Container registry
        uses: docker/login-action@65b78e6e13532edd9afa3aa52ac7964289d1a9c1
        with:
          registry: ghcr.io
          username: $
          password: $

      - name: Extract metadata (tags, labels) for Docker
        id: meta
        uses: docker/metadata-action@9ec57ed1fcdbf14dcef7dfbe97b2010124a938b7
        with:
          images: |
            my-docker-hub-namespace/my-docker-hub-repository
            /$

      - name: Build and push Docker images
        id: push
        uses: docker/build-push-action@3b5e8027fcad23fda98b2e3ac259d8d67585f671
        with:
          context: .
          push: true
          tags: $
          labels: $
```

The above workflow checks out the GitHub repository, uses the `login-action` twice to log in to both registries and generates tags and labels with the `metadata-action` action.
Then the `build-push-action` action builds and pushes the Docker image to Docker Hub and the GitHub.

> [!NOTE]
> When pushing to multiple registries:
>
> * Image digests may differ between registries, making attestation verification difficult.
> * To maintain a consistent digest and allow a single attestation to verify all copies, push to one registry first and use a tool like `crane copy` to replicate the image elsewhere.
> * If you choose to build and push to each registry separately instead, you must generate a distinct attestation for each one to ensure your artifacts remain verifiable.

## Hands-on practice

Practice publishing Docker images with the Publishing Docker images GitHub exercise.

In this exercise, you will learn how to:

* Authenticate to GitHub using the `GITHUB_TOKEN`.
* Build and publish container images to the GitHub (`ghcr.io`).
* Use official Docker actions, such as `docker/login-action`, `docker/build-push-action`, and `docker/setup-buildx-action`.
* Generate tags automatically with `docker/metadata-action` based on branches, pull requests, and releases.
* Create features, pull requests, and releases with proper container versioning.
