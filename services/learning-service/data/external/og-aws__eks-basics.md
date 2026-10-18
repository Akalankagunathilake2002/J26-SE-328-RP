<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#eks-basics -->
# AWS Guide: EKS Basics

-	📒 Homepage ∙ User guide ∙ FAQ ∙ Pricing
- EKS (Elastic Kubernetes Service) is a new service (launched June 2018) that provides managed Kubernetes Masters in a Highly Available pair to deploy K8s Services and Pods on top of EC2 based Kubernetes nodes.
- See the Containers and AWS section for more context on containers.
- EKS is AWS's solution to hosting Kubernetes natively on AWS. It is not a replacement for ECS directly but is in response to the large market dominance of Kubernetes.
- EKS does not launch EC2 nodes and would have to be configured and setup either manually or via Cloudformation (or other automation solution)
- EKS management is done through a utility called kubectl, and with Kube configuration files. These files will need to be configured to speak with the K8s Master with a certificate and URL. The AWS CLI can autogenerate the configuration file that kubectl requires for communicating with the cluster.1
- EKS authentication is integrated with IAM roles/permissions. The AWS CLI has an integrated sub-command for generating authentication tokens.2 This was formerly done via a custom plugin for kubectl called aws-iam-authenticator (formerly heptio-authenticator-aws).
- EKS provides Calico from Tigera for securing workloads within a cluster using Kubernetes network policy.

Back to top :arrow_up:
