<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#line-tools -->
# AWS Guide: Command-Line tools

-	The **aws command-line interface** (CLI), used via the **aws** command, is the most basic way to save and automate AWS operations.
-	Don’t underestimate its power. It also has the advantage of being well-maintained — it covers a large proportion of all AWS services, and is up to date.
-	In general, whenever you can, prefer the command line to the AWS Console for performing operations.
-	🔹Even in the absence of fancier tools, you can **write simple Bash scripts** that invoke *aws* with specific arguments, and check these into Git. This is a primitive but effective way to document operations you’ve performed. It improves automation, allows code review and sharing on a team, and gives others a starting point for future work.
-	🔹For use that is primarily interactive (not scripted), consider instead using the **aws-shell** tool from AWS. It is easier to use, with auto-completion and a colorful UI, but still works on the command line. If you’re using SAWS, a previous version of the program, you should migrate to aws-shell.
