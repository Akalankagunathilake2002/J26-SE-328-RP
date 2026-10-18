<!-- role: DevOps Engineer -->
<!-- topic: Linux Command Line -->
<!-- source: The Art of Command Line (Joshua Levy and contributors) -->
<!-- license: CC BY-SA 4.0 -->
<!-- url: https://github.com/jlevy/the-art-of-command-line#system-debugging -->
# Command Line: System debugging

- For web debugging, `curl` and `curl -I` are handy, or their `wget` equivalents, or the more modern `httpie`.

- To know current cpu/disk status, the classic tools are `top` (or the better `htop`), `iostat`, and `iotop`. Use `iostat -mxz 15` for basic CPU and detailed per-partition disk stats and performance insight.

- For network connection details, use `netstat` and `ss`.

- For a quick overview of what's happening on a system, `dstat` is especially useful. For broadest overview with details, use `glances`.

- To know memory status, run and understand the output of `free` and `vmstat`. In particular, be aware the "cached" value is memory held by the Linux kernel as file cache, so effectively counts toward the "free" value.

- Java system debugging is a different kettle of fish, but a simple trick on Oracle's and some other JVMs is that you can run `kill -3 ` and a full stack trace and heap summary (including generational garbage collection details, which can be highly informative) will be dumped to stderr/logs. The JDK's `jps`, `jstat`, `jstack`, `jmap` are useful. SJK tools are more advanced.

- Use `mtr` as a better traceroute, to identify network issues.

- For looking at why a disk is full, `ncdu` saves time over the usual commands like `du -sh *`.

- To find which socket or process is using bandwidth, try `iftop` or `nethogs`.

- The `ab` tool (comes with Apache) is helpful for quick-and-dirty checking of web server performance. For more complex load testing, try `siege`.

- For more serious network debugging, `wireshark`, `tshark`, or `ngrep`.

- Know about `strace` and `ltrace`. These can be helpful if a program is failing, hanging, or crashing, and you don't know why, or if you want to get a general idea of performance. Note the profiling option (`-c`), and the ability to attach to a running process (`-p`). Use trace child option (`-f`) to avoid missing important calls.

- Know about `ldd` to check shared libraries etc — but never run it on untrusted files.

- Know how to connect to a running process with `gdb` and get its stack traces.

- Use `/proc`. It's amazingly helpful sometimes when debugging live problems. Examples: `/proc/cpuinfo`, `/proc/meminfo`, `/proc/cmdline`, `/proc/xxx/cwd`, `/proc/xxx/exe`, `/proc/xxx/fd/`, `/proc/xxx/smaps` (where `xxx` is the process id or pid).

- When debugging why something went wrong in the past, `sar` can be very helpful. It shows historic statistics on CPU, memory, network, etc.

- For deeper systems and performance analyses, look at `stap` (SystemTap), `perf`, and `sysdig`.

- Check what OS you're on with `uname` or `uname -a` (general Unix/kernel info) or `lsb_release -a` (Linux distro info).

- Use `dmesg` whenever something's acting really funny (it could be hardware or driver issues).

- If you delete a file and it doesn't free up expected disk space as reported by `du`, check whether the file is in use by a process:
`lsof | grep deleted | grep "filename-of-my-big-file"`
