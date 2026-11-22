<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/security.variables.php -->
# PHP: User Submitted Data

The greatest weakness in many PHP programs is not inherent in the
language itself, but merely an issue of code not being written with
security in mind. For this reason, you should always take the time
to consider the implications of a given piece of code, to ascertain
the possible damage if an unexpected variable is submitted to it.

**Example #1 Dangerous Variable Usage**

```sql
<?php
// remove a file from the user's home directory... or maybe
// somebody else's?
unlink ($evil_var);

// Write logging of their access... or maybe an /etc/passwd entry?
fwrite ($fp, $evil_var);

// Execute something trivial.. or rm -rf *?
system ($evil_var);
exec ($evil_var);

?>
```

You should always carefully examine your code to make sure that any
variables being submitted from a web browser are being properly
checked, and ask yourself the following questions:

* Will this script only affect the intended files?
* Can unusual or undesirable data be acted upon?
* Can this script be used in unintended ways?
* Can this be used in conjunction with other scripts in a negative
  manner?
* Will any transactions be adequately logged?

By adequately asking these questions while writing the script,
rather than later, you prevent an unfortunate rewrite when you
need to increase your security. By starting out with this mindset,
you won't guarantee the security of your system, but you can help
improve it.

Improve security by disabling convenience settings that obscure input
data's origin, validity, or integrity. Implicit variable creation and
unchecked input can lead to vulnerabilities like injection attacks and
data manipulation.

Features like `register_globals` and
`magic_quotes` (both removed in PHP 5.4.0) once contributed
to these risks by automatically creating variables from user input and
escaping data inconsistently. While no longer in PHP, similar risks persist
if input handling is mismanaged.

Enable error\_reporting(E\_ALL) to
help detect uninitialized variables and validate input. Use strict types
(declare(strict\_types=1),
introduced in PHP 7) to enforce type safety, prevent unintended type conversions,
and improve overall security.

### Found A Problem?
