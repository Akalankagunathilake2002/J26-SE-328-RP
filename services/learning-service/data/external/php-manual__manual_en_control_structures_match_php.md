<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/control-structures.match.php -->
# PHP: match

(PHP 8)

The `match` expression branches evaluation based on an
identity check of a value.
Similarly to a `switch` statement, a
`match` expression has a subject expression that is
compared against multiple alternatives. Unlike `switch`,
it will evaluate to a value much like ternary expressions.
Unlike `switch`, the comparison is an identity check
(`===`) rather than a weak equality check (`==`).
Match expressions are available as of PHP 8.0.0.

**Example #1 Structure of a `match` expression**

```sql
<?php
$return_value = match (subject_expression) {
    single_conditional_expression => return_expression,
    conditional_expression1, conditional_expression2 => return_expression,
};
```

**Example #2 Basic `match` usage**

```sql
<?php
$food = 'cake';

$return_value = match ($food) {
    'apple' => 'This food is an apple',
    'bar' => 'This food is a bar',
    'cake' => 'This food is a cake',
};

var_dump($return_value);
```

The above example will output:

```sql
string(19) "This food is a cake"
```

**Example #3 Example of using `match` with comparison operators**

```sql
<?php
$age = 18;

$output = match (true) {
    $age  "Baby",
    $age  "Child",
    $age  "Teenager",
    $age >= 40 => "Adult",
    $age > 19 => "Young adult",
};

var_dump($output);
```

The above example will output:

```sql
string(8) "Teenager"
```

> **Note**:
>
> The result of a `match` expression does not need to be used.

> **Note**:
>
> When a `match` expression is used as a standalone
> expression, it *must* be terminated
> by a semicolon `;`.

The `match` expression is similar to a
`switch` statement but has some key differences:

* A `match` arm compares values strictly (`===`) instead
  of loosely as the switch statement does.
* A `match` expression returns a value.
* `match` arms do not fall through to later cases the way
  `switch` statements do.
* A `match` expression must be exhaustive.

Like `switch` statements, `match`
expressions are executed match arm by match arm.
In the beginning, no code is executed.
The conditional expressions are only evaluated if all previous conditional
expressions failed to match the subject expression.
Only the return expression corresponding to the matching conditional
expression will be evaluated.
For example:

```sql
<?php
$result = match ($x) {
    foo() => 'value',
    $this->bar() => 'value', // $this->bar() isn't called if foo() === $x
    $this->baz => beep(), // beep() isn't called unless $x === $this->baz
    // etc.
};
```

`match` expression arms may contain multiple expressions
separated by a comma. That is a logical OR, and is a shorthand for multiple
match arms with the same right-hand side.

```sql
<?php
$result = match ($x) {
    // This match arm:
    $a, $b, $c => 5,
    // Is equivalent to these three match arms:
    $a => 5,
    $b => 5,
    $c => 5,
};
```

A special case is the `default` pattern.
This pattern matches anything that wasn't previously matched.
For example:

```sql
<?php
$expressionResult = match ($condition) {
    1, 2 => foo(),
    3, 4 => bar(),
    default => baz(),
};
```

> **Note**:
>
> Multiple default patterns will raise an
> **`E_FATAL_ERROR`** error.

A `match` expression must be exhaustive. If the
subject expression is not handled by any match arm, an
UnhandledMatchError is thrown.

**Example #4 Example of an unhandled match expression**

```sql
<?php
$condition = 5;

try {
    match ($condition) {
        1, 2 => foo(),
        3, 4 => bar(),
    };
} catch (UnhandledMatchError $e) {
    var_dump($e);
}
```

The above example will output:

```sql
object(UnhandledMatchError)#1 (7) {
  ["message":protected]=>
  string(22) "Unhandled match case 5"
  ["string":"Error":private]=>
  string(0) ""
  ["code":protected]=>
  int(0)
  ["file":protected]=>
  string(6) "script"
  ["line":protected]=>
  int(5)
  ["trace":"Error":private]=>
  array(0) {
  }
  ["previous":"Error":private]=>
  NULL
}
```

### Using match expressions to handle non-identity checks

It is possible to use a `match` expression to handle
non-identity conditional cases by using `true` as the subject
expression.

**Example #5 Using a generalized match expression to branch on integer ranges**

```sql
<?php
$age = 23;

$result = match (true) {
    $age >= 65 => 'senior',
    $age >= 25 => 'adult',
    $age >= 18 => 'young adult',
    default => 'kid',
};

var_dump($result);
```

The above example will output:

```sql
string(11) "young adult"
```

**Example #6 Using a generalized match expression to branch on string content**

```sql
<?php

$text = 'Bienvenue chez nous';

$result = match (true) {
    str_contains($text, 'Welcome'), str_contains($text, 'Hello') => 'en',
    str_contains($text, 'Bienvenue'), str_contains($text, 'Bonjour') => 'fr',
    // ...
};

var_dump($result);
```

The above example will output:

```sql
string(2) "fr"
```

### Found A Problem?
