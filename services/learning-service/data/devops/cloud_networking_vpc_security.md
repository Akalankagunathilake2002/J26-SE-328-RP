# Cloud Networking: Virtual Private Clouds (VPC), Subnetting, and Zero-Trust Security

## Core Cloud Networking Topologies
A Virtual Private Cloud (VPC) represents an isolated software-defined private network within a public cloud provider. It provides granular control over IP address ranges, subnets, route tables, and network gateways.

## Subnetting Architecture: Public vs Private
- **Classless Inter-Domain Routing (CIDR)**: IP block allocation (e.g., `10.0.0.0/16` providing 65,536 private IP addresses).
- **Public Subnet**:
  - Connected directly to an **Internet Gateway (IGW)** via its route table (`0.0.0.0/0 -> igw-xxxx`).
  - Resources receive public IPv4 addresses and can accept inbound connections from the public Internet (ideal for Application Load Balancers, Bastion hosts, NAT Gateways).
- **Private Subnet**:
  - Has no direct route to an Internet Gateway (`0.0.0.0/0 -> nat-xxxx`).
  - Outbound traffic to the Internet (e.g. for OS security patches or third-party API calls) routes through a **NAT Gateway** located in the public subnet.
  - Inbound traffic from the public Internet is fundamentally blocked at the network routing layer (ideal for application microservices, Redis clusters, and PostgreSQL databases).

## Defense-in-Depth Network Filtering
1. **Security Groups (Stateful Instance Firewalls)**:
   - Operate at the virtual network interface (ENI) level.
   - **Stateful**: If an inbound rule permits traffic on port 443, outbound response packets are automatically permitted regardless of outbound rules.
   - Support referencing other Security Groups as traffic sources (e.g., "Allow port 5432 only from `sg-backend-microservices`").

2. **Network Access Control Lists (NACLs - Stateless Subnet Firewalls)**:
   - Operate at the subnet boundary level.
   - **Stateless**: Inbound and outbound rules must be explicitly configured, including ephemeral port return ranges (`1024-65535`).
   - Process rules strictly in numerical order (Rule 100 before Rule 200).

3. **VPC Endpoints & PrivateLink**:
   - Enables private connections between a VPC and cloud services (S3, DynamoDB, Secrets Manager) without traversing public Internet routes.
