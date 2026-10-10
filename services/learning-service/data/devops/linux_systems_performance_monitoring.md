# Linux Systems Performance Engineering and Troubleshooting

## The Linux Performance Methodology (USE Method)
Brendan Gregg's USE Method provides a systematic framework for analyzing system resource bottlenecks:
- **Utilization**: The percentage of time a resource is actively performing work (e.g., CPU core busy percentage).
- **Saturation**: The degree to which extra work is queued waiting for the resource (e.g., CPU run-queue length, disk queue depth).
- **Errors**: Count of error events (e.g., network packet drops, disk I/O retries).

## Key Subsystems and Diagnostic Tooling
1. **CPU & Scheduling**:
   - `uptime` / `top` / `htop`: Reports Load Average across 1, 5, and 15-minute intervals. If load average exceeds the total physical CPU core count, CPU saturation is occurring.
   - `mpstat -P ALL 1`: Breaks down CPU utilization per core into user space (`%usr`), system kernel space (`%sys`), and I/O wait (`%iowait`). High `%sys` indicates excessive system calls or context switching.

2. **Memory & Paging**:
   - `free -h`: Displays total, used, free, and cached memory.
   - `vmstat 1`: Inspects memory paging. Active swap-in (`si`) and swap-out (`so`) indicates the Linux kernel is thrashing disk to compensate for memory starvation, killing throughput.
   - **OOM Killer (Out-of-Memory)**: When kernel allocation fails, the OOM Killer invokes `oom_badness()` heuristics to terminate processes with high memory usage (frequently containerized microservices).

3. **Disk I/O & Storage Subsystems**:
   - `iostat -xz 1`: Monitors disk queue depth, read/write IOPS, throughput (MB/s), and `%util`. If `%util` reaches 100%, the storage device is fully saturated.
   - High `await` latency relative to `r_await` or `w_await` reveals queueing delays on physical storage controllers.

4. **Network Stack**:
   - `ss -s` / `netstat -ant`: Inspects TCP socket states (`ESTABLISHED`, `TIME_WAIT`, `CLOSE_WAIT`). High `CLOSE_WAIT` points to application leaks failing to close sockets.
   - `sar -n DEV 1`: Tracks packet throughput and drops per network interface.
