<!-- role: DevOps Engineer -->
<!-- topic: Linux Command Line -->
<!-- source: The Art of Command Line (Joshua Levy and contributors) -->
<!-- license: CC BY-SA 4.0 -->
<!-- url: https://github.com/jlevy/the-art-of-command-line#basics -->
# Command Line: Basics

- Learn basic Bash. Actually, type `man bash` and at least skim the whole thing; it's pretty easy to follow and not that long. Alternate shells can be nice, but Bash is powerful and always available (learning *only* zsh, fish, etc., while tempting on your own laptop, restricts you in many situations, such as using existing servers).

- Learn at least one text-based editor well. The `nano` editor is one of the simplest for basic editing (opening, editing, saving, searching). However, for the power user in a text terminal, there is no substitute for Vim (`vi`), the hard-to-learn but venerable, fast, and full-featured editor. Many people also use the classic Emacs, particularly for larger editing tasks. (Of course, any modern software developer working on an extensive project is unlikely to use only a pure text-based editor and should also be familiar with modern graphical IDEs and tools.)

- Finding documentation:
  - Know how to read official documentation with `man` (for the inquisitive, `man man` lists the section numbers, e.g. 1 is "regular" commands, 5 is files/conventions, and 8 are for administration). Find man pages with `apropos`.
  - Know that some commands are not executables, but Bash builtins, and that you can get help on them with `help` and `help -d`. You can find out whether a command is an executable, shell builtin or an alias by using `type command`.
  - `curl cheat.sh/command` will give a brief "cheat sheet" with common examples of how to use a shell command.

- Learn about redirection of output and input using `>` and `` overwrites the output file and `>>` appends. Learn about stdout and stderr.

- Learn about file glob expansion with `*` (and perhaps `?` and `[`...`]`) and quoting and the difference between double `"` and single `'` quotes. (See more on variable expansion below.)

- Be familiar with Bash job management: `&`, **ctrl-z**, **ctrl-c**, `jobs`, `fg`, `bg`, `kill`, etc.

- Know `ssh`, and the basics of passwordless authentication, via `ssh-agent`, `ssh-add`, etc.

- Basic file management: `ls` and `ls -l` (in particular, learn what every column in `ls -l` means), `less`, `head`, `tail` and `tail -f` (or even better, `less +F`), `ln` and `ln -s` (learn the differences and advantages of hard versus soft links), `chown`, `chmod`, `du` (for a quick summary of disk usage: `du -hs *`). For filesystem management, `df`, `mount`, `fdisk`, `mkfs`, `lsblk`. Learn what an inode is (`ls -i` or `df -i`).

- Basic network management: `ip` or `ifconfig`, `dig`, `traceroute`, `route`.

- Learn and use a version control management system, such as `git`.

- Know regular expressions well, and the various flags to `grep`/`egrep`. The `-i`, `-o`, `-v`, `-A`, `-B`, and `-C` options are worth knowing.

- Learn to use `apt-get`, `yum`, `dnf` or `pacman` (depending on distro) to find and install packages. And make sure you have `pip` to install Python-based command-line tools (a few below are easiest to install via `pip`).
