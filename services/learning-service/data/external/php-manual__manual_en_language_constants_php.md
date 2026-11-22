<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/language.constants.php -->
# PHP: Constants

## Table of Contents

* Syntax
* Predefined constants
* Magic constants

A constant is an identifier (name) for a simple value. As the name
suggests, that value cannot change during the execution of the
script (except for
magic constants, which aren't actually constants).
Constants are case-sensitive. By convention, constant
identifiers are always uppercase.

> **Note**:
>
> Prior to PHP 8.0.0, constants defined using the define()
> function may be case-insensitive.

> **Note**:
>
> As of PHP 8.5.0, redeclaring an already-defined constant is deprecated.

The name of a constant follows the same rules as any label in PHP. A
valid constant name starts with a letter or underscore, followed
by any number of letters, numbers, or underscores. As a regular
expression, it would be expressed thusly:
`^a-zA-Z_\x80-\xff*$`

It is possible to define() constants with reserved or even
invalid names, whose value can only be retrieved with the
constant() function. However, doing so is not recommended.

**Tip**

See also the
Userland Naming Guide.

**Example #1 Valid and invalid constant names**

```sql
<?php

// Valid constant names
define("FOO",     "something");
define("FOO2",    "something else");
define("FOO_BAR", "something more");

// Invalid constant names
define("2FOO",    "something");

// This is valid, but should be avoided:
// PHP may one day provide a magical constant
// that will break your script
define("__FOO__", "something");
```

> **Note**:
>
> For our purposes here, a letter is a-z, A-Z, and the ASCII
> characters from 128 through 255 (0x80-0xff).

Like superglobals, the scope of a constant is global.
Constants can be accessed from anywhere in a script without regard to scope.
For more information on scope, read the manual section on
variable scope.

> **Note**:
>
> As of PHP 7.1.0, class constant may declare a visibility of protected
> or private, making them only available in the hierarchical scope of the
> class in which it is defined.

### Found A Problem?
