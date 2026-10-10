# Infrastructure as Code (IaC) with HashiCorp Terraform

## Imperative vs Declarative Infrastructure Management
- **Imperative Approach (CLI scripts, Ansible commands)**: Instructs the system *how* to achieve a state step-by-step (`aws ec2 run-instances`, `apt-get install nginx`). Prone to configuration drift and non-idempotent duplicate provisioning.
- **Declarative Approach (Terraform HCL, CloudFormation)**: Describes *what* the desired final state of infrastructure should be (e.g. "There should be a PostgreSQL instance with 32GB RAM and 3 read replicas"). The engine computes the difference between current state and desired state and executes only necessary changes.

## Terraform Architecture & The Core Workflow
Terraform operates on three primary artifacts:
1. **Configuration (`.tf` files)**: Written in HashiCorp Configuration Language (HCL) defining providers (AWS, Azure, GCP, Kubernetes), resources, and variables.
2. **State File (`terraform.tfstate`)**: A JSON document recording real-world resource IDs, attributes, and metadata mapped to configuration blocks.
   - *Remote State & Locking*: In team environments, state is stored in durable remote object storage (AWS S3) paired with distributed locking (DynamoDB) to prevent concurrent conflicting writes.

### The Four-Step Terraform Lifecycle
1. `terraform init`: Downloads provider plugins and initializes remote backend storage.
2. `terraform plan`: Performs dry-run analysis. Compares HCL configuration against the state file and live cloud APIs, outputting a precise execution plan (`+ create`, `~ update in-place`, `- destroy`).
3. `terraform apply`: Applies the changes across cloud provider APIs.
4. `terraform destroy`: Tear down all managed resources cleanly.

## Modular Design and State Drift Detection
- **Terraform Modules**: Reusable, parameterized packages of Terraform configurations (e.g. a standardized VPC module or secure EKS cluster module).
- **Configuration Drift**: Occurs when an engineer manually modifies cloud resources via the AWS Web Console. Running `terraform plan` queries the live cloud API, detects out-of-band modifications, and proposes changes to restore infrastructure to the declared code baseline.
