<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/language.namespaces.rationale.php -->
# PHP: Overview

(PHP 5 >= 5.3.0, PHP 7, PHP 8)

What are namespaces? In the broadest definition namespaces are a way of encapsulating
items. This can be seen as an abstract concept in many places. For example, in any
operating system directories serve to group related files, and act as a namespace for
the files within them. As a concrete example, the file `foo.txt` can
exist in both directory `/home/greg` and in `/home/other`,
but two copies of `foo.txt` cannot co-exist in the same directory. In
addition, to access the `foo.txt` file outside of the
`/home/greg` directory, we must prepend the directory name to the file
name using the directory separator to get `/home/greg/foo.txt`. This
same principle extends to namespaces in the programming world.

In the PHP world, namespaces are designed to solve two problems that authors
of libraries and applications encounter when creating re-usable code elements
such as classes or functions:

1. Name collisions between code you create, and
   internal PHP classes/functions/constants or third-party classes/functions/constants.
2. Ability to alias (or shorten) Extra\_Long\_Names designed to alleviate the first problem,
   improving readability of source code.

PHP Namespaces provide a way in which to group related classes, interfaces,
functions and constants. Here is an example of namespace syntax in PHP:

**Example #1 Namespace syntax example**

```sql
<?php
namespace my\name; // see "Defining Namespaces" section

class MyClass {}
function myfunction() {}
const MYCONST = 1;

$a = new MyClass;
print $a::class . "\n";
$c = new \my\name\MyClass; // see "Global Space" section
print $c::class . "\n";

$a = strlen('hi'); // see "Using namespaces: fallback to global
                   // function/constant" section
print $a . "\n";

$d = namespace\MYCONST; // see "namespace operator and __NAMESPACE__
                        // constant" section
print $d . "\n";
$d = __NAMESPACE__ . '\MYCONST';
echo constant($d); // see "Namespaces and dynamic language features" section
```

> **Note**:
>
> Namespace names are case-insensitive.

> **Note**:
>
> The Namespace name `PHP`, and compound names starting
> with this name (like `PHP\Classes`) are reserved for internal language use
> and should not be used in the userspace code.

### Found A Problem?
