<!-- role: DevOps Engineer -->
<!-- topic: Linux Command Line -->
<!-- source: The Art of Command Line (Joshua Levy and contributors) -->
<!-- license: CC BY-SA 4.0 -->
<!-- url: https://github.com/jlevy/the-art-of-command-line#everyday-use -->
# Command Line: Everyday use

- In Bash, use **Tab** to complete arguments or list all available commands and **ctrl-r** to search through command history (after pressing, type to search, press **ctrl-r** repeatedly to cycle through more matches, press **Enter** to execute the found command, or hit the right arrow to put the result in the current line to allow editing).

- In Bash, use **ctrl-w** to delete the last word, and **ctrl-u** to delete the content from current cursor back to the start of the line. Use **alt-b** and **alt-f** to move by word, **ctrl-a** to move cursor to beginning of line,  **ctrl-e** to move cursor to end of line, **ctrl-k** to kill to the end of the line, **ctrl-l** to clear the screen. See `man readline` for all the default keybindings in Bash. There are a lot. For example **alt-.** cycles through previous arguments, and **alt-*** expands a glob.

- Alternatively, if you love vi-style key-bindings, use `set -o vi` (and `set -o emacs` to put it back).

- For editing long commands, after setting your editor (for example `export EDITOR=vim`), **ctrl-x** **ctrl-e** will open the current command in an editor for multi-line editing. Or in vi style, **escape-v**.

- To see recent commands, use `history`. Follow with `!n` (where `n` is the command number) to execute again. There are also many abbreviations you can use, the most useful probably being `!$` for last argument and `!!` for last command (see "HISTORY EXPANSION" in the man page). However, these are often easily replaced with **ctrl-r** and **alt-.**.

- Go to your home directory with `cd`. Access files relative to your home directory with the `~` prefix (e.g. `~/.bashrc`). In `sh` scripts refer to the home directory as `$HOME`.

- To go back to the previous working directory: `cd -`.

- If you are halfway through typing a command but change your mind, hit **alt-#** to add a `#` at the beginning and enter it as a comment (or use **ctrl-a**, **#**, **enter**). You can then return to it later via command history.

- Use `xargs` (or `parallel`). It's very powerful. Note you can control how many items execute per line (`-L`) as well as parallelism (`-P`). If you're not sure if it'll do the right thing, use `xargs echo` first. Also, `-I{}` is handy. Examples:
```bash
      find . -name '*.py' | xargs grep some_function
      cat hosts | xargs -I{} ssh root@{} hostname
```

- `pstree -p` is a helpful display of the process tree.

- Use `pgrep` and `pkill` to find or signal processes by name (`-f` is helpful).

- Know the various signals you can send processes. For example, to suspend a process, use `kill -STOP [pid]`. For the full list, see `man 7 signal`

- Use `nohup` or `disown` if you want a background process to keep running forever.

- Check what processes are listening via `netstat -lntp` or `ss -plat` (for TCP; add `-u` for UDP) or `lsof -iTCP -sTCP:LISTEN -P -n` (which also works on macOS).

- See also `lsof` and `fuser` for open sockets and files.

- See `uptime` or `w` to know how long the system has been running.

- Use `alias` to create shortcuts for commonly used commands. For example, `alias ll='ls -latr'` creates a new alias `ll`.

- Save aliases, shell settings, and functions you commonly use in `~/.bashrc`, and arrange for login shells to source it. This will make your setup available in all your shell sessions.

- Put the settings of environment variables as well as commands that should be executed when you login in `~/.bash_profile`. Separate configuration will be needed for shells you launch from graphical environment logins and `cron` jobs.

- Synchronize your configuration files (e.g. `.bashrc` and `.bash_profile`) among various computers with Git.

- Understand that care is needed when variables and filenames include whitespace. Surround your Bash variables with quotes, e.g. `"$FOO"`. Prefer the `-0` or `-print0` options to enable null characters to delimit filenames, e.g. `locate -0 pattern | xargs -0 ls -al` or `find / -print0 -type d | xargs -0 ls -al`. To iterate on filenames containing whitespace in a for loop, set your IFS to be a newline only using `IFS=$'\n'`.

- In Bash scripts, use `set -x` (or the variant `set -v`, which logs raw input, including unexpanded variables and comments) for debugging output. Use strict modes unless you have a good reason not to: Use `set -e` to abort on errors (nonzero exit code). Use `set -u` to detect unset variable usages. Consider `set -o pipefail` too, to abort on errors within pipes (though read up on it more if you do, as this topic is a bit subtle). For more involved scripts, also use `trap` on EXIT or ERR. A useful habit is to start a script like this, which will make it detect and abort on common errors and print a message:
```bash
      set -euo pipefail
      trap "echo 'error: Script failed: see failed command above'" ERR
```

- In Bash scripts, subshells (written with parentheses) are convenient ways to group commands. A common example is to temporarily move to a different working directory, e.g.
```bash
      # do something in current dir
      (cd /some/other/dir && other-command)
      # continue in original dir
```

- In Bash, note there are lots of kinds of variable expansion. Checking a variable exists: `${name:?error message}`. For example, if a Bash script requires a single argument, just write `input_file=${1:?usage: $0 input_file}`. Using a default value if a variable is empty: `${name:-default}`. If you want to have an additional (optional) parameter added to the previous example, you can use something like `output_file=${2:-logfile}`. If `$2` is omitted and thus empty, `output_file` will be set to `logfile`. Arithmetic expansion: `i=$(( (i + 1) % 5 ))`. Sequences: `{1..10}`. Trimming of strings: `${var%suffix}` and `${var#prefix}`. For example if `var=foo.pdf`, then `echo ${var%.pdf}.txt` prints `foo.txt`.

- Brace expansion using `{`...`}` can reduce having to re-type similar text and automate combinations of items.  This is helpful in examples like `mv foo.{txt,pdf} some-dir` (which moves both files), `cp somefile{,.bak}` (which expands to `cp somefile somefile.bak`) or `mkdir -p test-{a,b,c}/subtest-{1,2,3}` (which expands all possible combinations and creates a directory tree). Brace expansion is performed before any other expansion.

- The order of expansions is: brace expansion; tilde expansion, parameter and variable expansion, arithmetic expansion, and command substitution (done in a left-to-right fashion); word splitting; and filename expansion. (For example, a range like `{1..20}` cannot be expressed with variables using `{$a..$b}`. Use `seq` or a `for` loop instead, e.g., `seq $a $b` or `for((i=a; i<=b; i++)); do ... ; done`.)

- The output of a command can be treated like a file via `<(some command)` (known as process substitution). For example, compare local `/etc/hosts` with a remote one:
```sh
      diff /etc/hosts <(ssh somehost cat /etc/hosts)
```

- When writing scripts you may want to put all of your code in curly braces. If the closing brace is missing, your script will be prevented from executing due to a syntax error. This makes sense when your script is going to be downloaded from the web, since it prevents partially downloaded scripts from executing:
```bash
{
      # Your code here
}
```

- A "here document" allows redirection of multiple lines of input as if from a file:
```
cat <<EOF
input
on multiple lines
EOF
```

- In Bash, redirect both standard output and standard error via: `some-command >logfile 2>&1` or `some-command &>logfile`. Often, to ensure a command does not leave an open file handle to standard input, tying it to the terminal you are in, it is also good practice to add `</dev/null`.

- Use `man ascii` for a good ASCII table, with hex and decimal values. For general encoding info, `man unicode`, `man utf-8`, and `man latin1` are helpful.

- Use `screen` or `tmux` to multiplex the screen, especially useful on remote ssh sessions and to detach and re-attach to a session. `byobu` can enhance screen or tmux by providing more information and easier management. A more minimal alternative for session persistence only is `dtach`.

- In ssh, knowing how to port tunnel with `-L` or `-D` (and occasionally `-R`) is useful, e.g. to access web sites from a remote server.

- It can be useful to make a few optimizations to your ssh configuration; for example, this `~/.ssh/config` contains settings to avoid dropped connections in certain network environments, uses compression (which is helpful with scp over low-bandwidth connections), and multiplex channels to the same server with a local control file:
```
      TCPKeepAlive=yes
      ServerAliveInterval=15
      ServerAliveCountMax=6
      Compression=yes
      ControlMaster auto
      ControlPath /tmp/%r@%h:%p
      ControlPersist yes
```

- A few other options relevant to ssh are security sensitive and should be enabled with care, e.g. per subnet or host or in trusted networks: `StrictHostKeyChecking=no`, `ForwardAgent=yes`

- Consider `mosh` an alternative to ssh that uses UDP, avoiding dropped connections and adding convenience on the road (requires server-side setup).

- To get the permissions on a file in octal form, which is useful for system configuration but not available in `ls` and easy to bungle, use something like
```sh
      stat -c '%A %a %n' /etc/timezone
```

- For interactive selection of values from the output of another command, use `percol` or `fzf`.

- For interaction with files based on the output of another command (like `git`), use `fpp` (PathPicker).

- For a simple web server for all files in the current directory (and subdirs), available to anyone on your network, use:
`python -m SimpleHTTPServer 7777` (for port 7777 and Python 2) and `python -m http.server 7777` (for port 7777 and Python 3).

- For running a command as another user, use `sudo`. Defaults to running as root; use `-u` to specify another user. Use `-i` to login as that user (you will be asked for _your_ password).

- For switching the shell to another user, use `su username` or `su - username`. The latter with "-" gets an environment as if another user just logged in. Omitting the username defaults to root. You will be asked for the password _of the user you are switching to_.

- Know about the 128K limit on command lines. This "Argument list too long" error is common when wildcard matching large numbers of files. (When this happens alternatives like `find` and `xargs` may help.)

- For a basic calculator (and of course access to Python in general), use the `python` interpreter. For example,
```
>>> 2+3
5
```
