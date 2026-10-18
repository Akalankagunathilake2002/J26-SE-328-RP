<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/concepts/runners/support-for-arc -->
# Support for Actions Runner Controller

What to know before you contact GitHub for assistance with Actions Runner Controller.

## Overview

The Actions Runner Controller (ARC) project was adopted by GitHub to release as a new GitHub product. As a result, there are currently two ARC releases: the legacy community-maintained ARC and GitHub's Autoscaling Runner Sets. GitHub's Autoscaling Runner Sets work with both Kubernetes and OpenShift.

GitHub only supports the latest Autoscaling Runner Sets version of ARC. Support for the legacy ARC is provided by the community in the Actions Runner Controller repository only.

## Scope of support for Actions Runner Controller

To ensure a smooth adoption of GitHub, we recommend that organizations have staff with expert-level knowledge of container orchestration. Many aspects of ARC installation, including orchestration, networking, policy application, and integration with managed cluster providers, fall outside GitHub's scope and require in-depth knowledge of your clustering tools (i.e. Kubernetes or OpenShift). If your support request is outside of the scope of what our team can help you with, we may be able to recommend next steps to help resolve your issue or provide other guidance. Your support request is out of GitHub's scope if the request is primarily about:

* The legacy community-maintained version of ARC
* Installing, configuring, or maintaining dependencies
* Template spec customization
* Container orchestration, such as Kubernetes/OpenShift setup, networking, building images in ARC (DinD), etc.
* Applying cluster policies
* Managed container orchestration providers or provider-specific configurations
* Runner Container Hooks in conjunction with ARC's `kubernetes` mode
* Installation tooling other than Helm
* Storage provisioners and PersistentVolumeClaims (PVCs)
* Best practices, such as configuring metrics servers, image caching, etc.

While ARC may be deployed successfully with different tooling and configurations, your support request is possibly out of GitHub's scope if ARC has been deployed with:

* Installation tooling other than Helm
* Service account and/or template spec customization

For more information about contacting GitHub, see AUTOTITLE.

> [!NOTE]
> * ARC is only supported on GitHub Enterprise Server versions 3.9 and greater.

## Working with GitHub for Actions Runner Controller

GitHub may ask questions about your Actions Runner Controller deployment and request that you collect and attach controller logs, listener logs, runner logs, and Helm charts (`values.yaml`) to the support ticket.
