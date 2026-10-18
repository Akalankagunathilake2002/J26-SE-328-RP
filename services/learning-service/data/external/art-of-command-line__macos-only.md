<!-- role: DevOps Engineer -->
<!-- topic: Linux Command Line -->
<!-- source: The Art of Command Line (Joshua Levy and contributors) -->
<!-- license: CC BY-SA 4.0 -->
<!-- url: https://github.com/jlevy/the-art-of-command-line#macos-only -->
# Command Line: macOS only

These are items relevant *only* on macOS.

- Package management with `brew` (Homebrew) and/or `port` (MacPorts). These can be used to install on macOS many of the above commands.

- Copy output of any command to a desktop app with `pbcopy` and paste input from one with `pbpaste`.

- To enable the Option key in macOS Terminal as an alt key (such as used in the commands above like **alt-b**, **alt-f**, etc.), open Preferences -> Profiles -> Keyboard and select "Use Option as Meta key".

- To open a file with a desktop app, use `open` or `open -a /Applications/Whatever.app`.

- Spotlight: Search files with `mdfind` and list metadata (such as photo EXIF info) with `mdls`.

- Be aware macOS is based on BSD Unix, and many commands (for example `ps`, `ls`, `tail`, `awk`, `sed`) have many subtle variations from Linux, which is largely influenced by System V-style Unix and GNU tools. You can often tell the difference by noting a man page has the heading "BSD General Commands Manual." In some cases GNU versions can be installed, too (such as `gawk` and `gsed` for GNU awk and sed). If writing cross-platform Bash scripts, avoid such commands (for example, consider Python or `perl`) or test carefully.

- To get macOS release information, use `sw_vers`.
