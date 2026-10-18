<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: Architecture Styles -->
<!-- source: Azure Architecture Center (Microsoft) -->
<!-- license: CC BY 4.0 -->
<!-- url: https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/big-compute -->
# Big compute architecture style

Understand the benefits, challenges, and best practices of the Big Compute architecture style on Azure.

The term *big compute* describes large-scale workloads that can require hundreds or thousands of cores. Use cases that require big compute include image rendering, fluid dynamics, financial risk modeling, oil exploration, drug design, and engineering stress analysis.

   In the diagram, an arrow that represents a job queue points from a client to a scheduler or coordinator. The job queue arrow then branches from the scheduler to one box that contains parallel tasks and to another box that contains tightly coupled tasks.

The following characteristics are common in big compute applications:

- The work can be split into discrete tasks that can run across many cores simultaneously.

- Each task is finite. It takes input, processes that input, and produces an output. The entire application can run for a few minutes to several days, but it runs for a finite amount of time. A common pattern is to provision a large number of cores in a burst and then reduce the number of cores to zero when the application completes.

- The application doesn't need to continuously run. However, the system must handle node failures or application crashes.

- For some applications, tasks are independent and can run in parallel. In other cases, tasks are tightly coupled, which means that they must interact or exchange intermediate results. In this case, consider using high-speed networking technologies such as InfiniBand and remote direct memory access (RDMA).

- Depending on your workload, you might use compute-intensive virtual machine (VM) families like HBv5-series, HC-series, and HX-series.

## When to use this architecture

- Computationally intensive operations such as simulations and number crunching

- Simulations that are computationally intensive and must be split across CPUs in hundreds or thousands of computers

- Simulations that require too much memory for one computer and must be split across multiple computers

- Long-running computations that take too long to complete on a single computer

- Smaller computations that must run hundreds or thousands of times, such as Monte Carlo simulations

## Benefits

- High performance with *embarrassingly parallel* processing

- The ability to use hundreds or thousands of computer cores to solve large problems faster

- Access to specialized high-performance hardware that uses dedicated high-speed InfiniBand networks

- The ability to provision and remove VMs as needed

## Challenges

- Managing the VM infrastructure

- Managing the volume of number crunching

- Provisioning thousands of cores in a timely manner

- For tightly coupled tasks, adding more cores can have diminishing returns. You might need to experiment to find the optimum number of cores.

## Big compute by using Azure Batch

Azure Batch is a managed service for running large-scale, high-performance computing (HPC) applications.

Use Batch to configure a VM pool and upload the applications and data files. The Batch service provisions the VMs, assigns tasks to the VMs, runs the tasks, and monitors the progress. Batch can automatically scale out the VMs in response to the workload. Batch also provides job scheduling.

   In the diagram, a dotted line surrounds icons that represent the VM pool. A double-sided arrow connects the VM pool with an icon that represents Batch. Another double-sided arrow connects the VM pool with an icon that represents storage.

## Big compute that runs on VMs

You can use Microsoft HPC Pack to administer a cluster of VMs and schedule and monitor HPC jobs. If you use this approach, you must provision and manage the VMs and network infrastructure. Consider this approach if you have existing HPC workloads and want to move some or all of them to Azure. You can move the entire HPC cluster to Azure, or you can keep your HPC cluster on-premises and use Azure for burst capacity. For more information, see HPC on Azure.

### HPC Pack deployed to Azure

In this scenario, the HPC cluster is created entirely within Azure.

   In this diagram, a box represents a virtual network. The virtual network contains icons that represent cluster nodes, an RDMA network, and the cluster head node. A double-sided arrow connects the virtual network box to storage outside of the virtual network.

The head node provides management and job scheduling services to the cluster. For tightly coupled tasks, use an RDMA network that provides high-bandwidth, low-latency communication between VMs. For more information, see Overview of Microsoft HPC Pack 2019.

### Burst an HPC cluster to Azure

In this scenario, you run HPC Pack on-premises and use Azure VMs for burst capacity. The cluster head node is on-premises. Azure ExpressRoute or Azure VPN Gateway connects the on-premises network to the Azure virtual network.

   The diagram contains two boxes. One box represents the on-premises environment. It contains icons that represent cluster nodes and the cluster head node. The other box represents a virtual network. It contains cluster nodes. Double-sided arrows that represent Expressroute or VPN Gateway connect the on-premises box and the virtual network box. Another double-sided arrow connects the virtual network box to storage outside of the virtual network.

## Related resources

- Choose an Azure compute service for your application
- HPC on Azure
