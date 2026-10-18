<!-- role: DevOps Engineer -->
<!-- topic: Linux Command Line -->
<!-- source: The Art of Command Line (Joshua Levy and contributors) -->
<!-- license: CC BY-SA 4.0 -->
<!-- url: https://github.com/jlevy/the-art-of-command-line#processing-files-and-data -->
# Command Line: Processing files and data

- To locate a file by name in the current directory, `find . -iname '*something*'` (or similar). To find a file anywhere by name, use `locate something` (but bear in mind `updatedb` may not have indexed recently created files).

- For general searching through source or data files, there are several options more advanced or faster than `grep -r`, including (in rough order from older to newer) `ack`, `ag` ("the silver searcher"), and `rg` (ripgrep).

- To convert HTML to text: `lynx -dump -stdin`

- For Markdown, HTML, and all kinds of document conversion, try `pandoc`. For example, to convert a Markdown document to Word format: `pandoc README.md --from markdown --to docx -o temp.docx`

- If you must handle XML, `xmlstarlet` is old but good.

- For JSON, use `jq`. For interactive use, also see `jid` and `jiq`.

- For YAML, use `shyaml`.

- For Excel or CSV files, csvkit provides `in2csv`, `csvcut`, `csvjoin`, `csvgrep`, etc.

- For Amazon S3, `s3cmd` is convenient and `s4cmd` is faster. Amazon's `aws` and the improved `saws` are essential for other AWS-related tasks.

- Know about `sort` and `uniq`, including uniq's `-u` and `-d` options -- see one-liners below. See also `comm`.

- Know about `cut`, `paste`, and `join` to manipulate text files. Many people use `cut` but forget about `join`.

- Know about `wc` to count newlines (`-l`), characters (`-m`), words (`-w`) and bytes (`-c`).

- Know about `tee` to copy from stdin to a file and also to stdout, as in `ls -al | tee file.txt`.

- For more complex calculations, including grouping, reversing fields, and statistical calculations, consider `datamash`.

- Know that locale affects a lot of command line tools in subtle ways, including sorting order (collation) and performance. Most Linux installations will set `LANG` or other locale variables to a local setting like US English. But be aware sorting will change if you change locale. And know i18n routines can make sort or other commands run *many times* slower. In some situations (such as the set operations or uniqueness operations below) you can safely ignore slow i18n routines entirely and use traditional byte-based sort order, using `export LC_ALL=C`.

- You can set a specific command's environment by prefixing its invocation with the environment variable settings, as in `TZ=Pacific/Fiji date`.

- Know basic `awk` and `sed` for simple data munging. See One-liners for examples.

- To replace all occurrences of a string in place, in one or more files:
```sh
      perl -pi.bak -e 's/old-string/new-string/g' my-files-*.txt
```

- To rename multiple files and/or search and replace within files, try `repren`. (In some cases the `rename` command also allows multiple renames, but be careful as its functionality is not the same on all Linux distributions.)
```sh
      # Full rename of filenames, directories, and contents foo -> bar:
      repren --full --preserve-case --from foo --to bar .
      # Recover backup files whatever.bak -> whatever:
      repren --renames --from '(.*)\.bak' --to '\1' *.bak
      # Same as above, using rename, if available:
      rename 's/\.bak$//' *.bak
```

- As the man page says, `rsync` really is a fast and extraordinarily versatile file copying tool. It's known for synchronizing between machines but is equally useful locally. When security restrictions allow, using `rsync` instead of `scp` allows recovery of a transfer without restarting from scratch. It also is among the fastest ways to delete large numbers of files:
```sh
mkdir empty && rsync -r --delete empty/ some-dir && rmdir some-dir
```

- For monitoring progress when processing files, use `pv`, `pycp`, `pmonitor`, `progress`, `rsync --progress`, or, for block-level copying, `dd status=progress`.

- Use `shuf` to shuffle or select random lines from a file.

- Know `sort`'s options. For numbers, use `-n`, or `-h` for handling human-readable numbers (e.g. from `du -h`). Know how keys work (`-t` and `-k`). In particular, watch out that you need to write `-k1,1` to sort by only the first field; `-k1` means sort according to the whole line. Stable sort (`sort -s`) can be useful. For example, to sort first by field 2, then secondarily by field 1, you can use `sort -k1,1 | sort -s -k2,2`.

- If you ever need to write a tab literal in a command line in Bash (e.g. for the -t argument to sort), press **ctrl-v** **[Tab]** or write `$'\t'` (the latter is better as you can copy/paste it).

- The standard tools for patching source code are `diff` and `patch`. See also `diffstat` for summary statistics of a diff and `sdiff` for a side-by-side diff. Note `diff -r` works for entire directories. Use `diff -r tree1 tree2 | diffstat` for a summary of changes. Use `vimdiff` to compare and edit files.

- For binary files, use `hd`, `hexdump` or `xxd` for simple hex dumps and `bvi`, `hexedit` or `biew` for binary editing.

- Also for binary files, `strings` (plus `grep`, etc.) lets you find bits of text.

- For binary diffs (delta compression), use `xdelta3`.

- To convert text encodings, try `iconv`. Or `uconv` for more advanced use; it supports some advanced Unicode things. For example:
```sh
      # Displays hex codes or actual names of characters (useful for debugging):
      uconv -f utf-8 -t utf-8 -x '::Any-Hex;' < input.txt
      uconv -f utf-8 -t utf-8 -x '::Any-Name;' < input.txt
      # Lowercase and removes all accents (by expanding and dropping them):
      uconv -f utf-8 -t utf-8 -x '::Any-Lower; ::Any-NFD; [:Nonspacing Mark:] >; ::Any-NFC;'  output.txt
```

- To split files into pieces, see `split` (to split by size) and `csplit` (to split by a pattern).

- Date and time: To get the current date and time in the helpful ISO 8601 format, use `date -u +"%Y-%m-%dT%H:%M:%SZ"` (other options are problematic). To manipulate date and time expressions, use `dateadd`, `datediff`, `strptime` etc. from `dateutils`.

- Use `zless`, `zmore`, `zcat`, and `zgrep` to operate on compressed files.

- File attributes are settable via `chattr` and offer a lower-level alternative to file permissions. For example, to protect against accidental file deletion the immutable flag:  `sudo chattr +i /critical/directory/or/file`

- Use `getfacl` and `setfacl` to save and restore file permissions. For example:
```sh
   getfacl -R /some/path > permissions.txt
   setfacl --restore=permissions.txt
```

- To create empty files quickly, use `truncate` (creates sparse file), `fallocate` (ext4, xfs, btrfs and ocfs2 filesystems), `xfs_mkfile` (almost any filesystems, comes in xfsprogs package), `mkfile` (for Unix-like systems like Solaris, Mac OS).
