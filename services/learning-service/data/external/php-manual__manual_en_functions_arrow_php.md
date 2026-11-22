<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/functions.arrow.php -->
# PHP: Arrow Functions

Arrow functions were introduced in PHP 7.4 as a more concise syntax for
anonymous functions.

Both anonymous functions and arrow functions are implemented using the
Closure class.

Arrow functions have the basic form
`fn (argument_list) => expr`.

Arrow functions support the same features as
anonymous functions,
except that using variables from the parent scope is always automatic.

When a variable used in the expression is defined in the parent scope
it will be implicitly captured by-value.
In the following example, the functions $fn1 and
$fn2 behave the same way.

**Example #1 Arrow functions capture variables by value automatically**

```sql
<?php
$y = 1;

$fn1 = fn($x) => $x + $y;
// equivalent to using $y by value:
$fn2 = function ($x) use ($y) {
    return $x + $y;
};

var_export($fn1(3));
```

The above example will output:

```sql
4
```

This also works if the arrow functions are nested:

**Example #2 Arrow functions capture variables by value automatically, even when nested**

```sql
<?php
$z = 1;
$fn = fn($x) => fn($y) => $x * $y + $z;
// Outputs 51
var_export($fn(5)(10));
```

Similarly to anonymous functions,
the arrow function syntax allows arbitrary function signatures,
including parameter and return types, default values, variadics,
as well as by-reference passing and returning.
All of the following are valid examples of arrow functions:

**Example #3 Examples of arrow functions**

```sql
<?php
fn(array $x) => $x;
static fn($x): int => $x;
fn($x = 42) => $x;
fn(&$x) => $x;
fn&($x) => $x;
fn($x, ...$rest) => $rest;
```

Arrow functions use by-value variable binding.
This is roughly equivalent to performing a `use($x)` for every
variable $x used inside the arrow function.
A by-value binding means that it is not possible to modify any values
from the outer scope.
Anonymous functions
can be used instead for by-ref bindings.

**Example #4 Values from the outer scope cannot be modified by arrow functions**

```sql
<?php
$x = 1;
$fn = fn() => $x++; // Has no effect
$fn();
var_export($x);  // Outputs 1
```

### Changelog

| Version | Description |
| --- | --- |
| 7.4.0 | Arrow functions became available. |

### Notes

> **Note**:
>
> It is possible to use func\_num\_args(),
> func\_get\_arg(), and func\_get\_args()
> from within an arrow function.

### Found A Problem?
