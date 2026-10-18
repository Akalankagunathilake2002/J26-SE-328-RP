<!-- role: DevOps Engineer -->
<!-- topic: Linux Command Line -->
<!-- source: The Art of Command Line (Joshua Levy and contributors) -->
<!-- license: CC BY-SA 4.0 -->
<!-- url: https://github.com/jlevy/the-art-of-command-line#windows-only -->
# Command Line: Windows only

These items are relevant *only* on Windows.

### Ways to obtain Unix tools under Windows

- Access the power of the Unix shell under Microsoft Windows by installing Cygwin. Most of the things described in this document will work out of the box.

- On Windows 10, you can use Windows Subsystem for Linux (WSL), which provides a familiar Bash environment with Unix command line utilities.

- If you mainly want to use GNU developer tools (such as GCC) on Windows, consider MinGW and its MSYS package, which provides utilities such as bash, gawk, make and grep. MSYS doesn't have all the features compared to Cygwin. MinGW is particularly useful for creating native Windows ports of Unix tools.

- Another option to get Unix look and feel under Windows is Cash. Note that only very few Unix commands and command-line options are available in this environment.

### Useful Windows command-line tools

- You can perform and script most Windows system administration tasks from the command line by learning and using `wmic`.

- Native command-line Windows networking tools you may find useful include `ping`, `ipconfig`, `tracert`, and `netstat`.

- You can perform many useful Windows tasks by invoking the `Rundll32` command.

### Cygwin tips and tricks

- Install additional Unix programs with the Cygwin's package manager.

- Use `mintty` as your command-line window.

- Access the Windows clipboard through `/dev/clipboard`.

- Run `cygstart` to open an arbitrary file through its registered application.

- Access the Windows registry with `regtool`.

- Note that a `C:\` Windows drive path becomes `/cygdrive/c` under Cygwin, and that Cygwin's `/` appears under `C:\cygwin` on Windows. Convert between Cygwin and Windows-style file paths with `cygpath`. This is most useful in scripts that invoke Windows programs.
