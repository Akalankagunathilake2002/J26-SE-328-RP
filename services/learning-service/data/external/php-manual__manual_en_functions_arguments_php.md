<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/functions.arguments.php -->
# PHP: Function parameters and arguments

The function parameters are declared in the function signature.
Information may be passed to functions via the argument list,
which is a comma-delimited list of expressions. The arguments are
evaluated from left to right and the result is assigned to the parameters of
the function, before the function is actually called
(*eager* evaluation).

PHP supports passing arguments by value (the default), passing by
reference, and default argument
values. Variable-length
argument lists and Named Arguments
are also supported.

> **Note**:
>
> As of PHP 7.3.0, it is possible to have a trailing comma in the argument
> list for a function calls:
>
> ```sql
> <?php
> $v = foo(
>     $arg_1,
>     $arg_2,
> );
> ```

As of PHP 8.0.0, the list of function parameters may include a trailing comma, which
will be ignored. That is particularly useful in cases where the list of parameters is
long or contains long variable names, making it convenient to list parameters vertically.

**Example #1 Function parameter list with trailing comma**

```sql
<?php
function takes_many_args(
    $first_arg,
    $second_arg,
    $a_very_long_argument_name,
    $arg_with_default = 5,
    $again = 'a default string', // This trailing comma was not permitted before 8.0.0.
)
{
    // ...
}
```

### Passing arguments by reference

By default, function arguments are passed by value (so that if
the value of the argument within the function is changed, it does
not get changed outside of the function). To allow a function to modify its
arguments, they must be passed by reference.

To have an argument to a function always passed by reference, prepend an
ampersand (&) to the parameter name in the function definition:

**Example #2 Passing function arguments by reference**

```sql
<?php
function add_some_extra(&$string)
{
    $string .= 'and something extra.';
}
$str = 'This is a string, ';
add_some_extra($str);
echo $str;    // outputs 'This is a string, and something extra.'
```

It is an error to pass a constant expression as an argument to a parameter
that expects to be passed by reference.

### Default parameter values

A function may define default values for parameters using syntax similar
to assigning a variable. The default is used only when the parameter's argument is
not passed. Note that passing **`null`** does *not*
assign the default value.

**Example #3 Use of default parameters in functions**

```sql
<?php
function makecoffee($type = "cappuccino")
{
    return "Making a cup of $type.\n";
}
echo makecoffee();
echo makecoffee(null);
echo makecoffee("espresso");
```

The above example will output:

```sql
Making a cup of cappuccino.
Making a cup of .
Making a cup of espresso.
```

Default parameter values may be scalar values, arrays,
the special type **`null`**, and as of PHP 8.1.0, objects using the
new ClassName() syntax.

**Example #4 Using non-scalar types as default values**

```sql
<?php
function makecoffee($types = array("cappuccino"), $coffeeMaker = NULL)
{
    $device = is_null($coffeeMaker) ? "hands" : $coffeeMaker;
    return "Making a cup of ".join(", ", $types)." with $device.\n";
}
echo makecoffee();
echo makecoffee(array("cappuccino", "lavazza"), "teapot");
```

The above example will output:

```sql
Making a cup of cappuccino with hands.
Making a cup of cappuccino, lavazza with teapot.
```

**Example #5 Using objects as default values (as of PHP 8.1.0)**

```sql
<?php
class DefaultCoffeeMaker {
    public function brew() {
        return "Making coffee.\n";
    }
}
class FancyCoffeeMaker {
    public function brew() {
        return "Crafting a beautiful coffee just for you.\n";
    }
}
function makecoffee($coffeeMaker = new DefaultCoffeeMaker)
{
    return $coffeeMaker->brew();
}
echo makecoffee();
echo makecoffee(new FancyCoffeeMaker);
```

The above example will output:

```sql
Making coffee.
Crafting a beautiful coffee just for you.
```

The default value must be a constant expression, not (for
example) a variable, a class member or a function call.

Note that any optional parameters should be specified after any
required parameters, otherwise they cannot be omitted from calls.
Consider the following example:

**Example #6 Incorrect usage of default function parameters**

```sql
<?php
function makeyogurt($container = "bowl", $flavour)
{
    return "Making a $container of $flavour yogurt.\n";
}

echo makeyogurt("raspberry"); // "raspberry" is $container, not $flavour
```

The above example will output:

```sql
Deprecated: makeyogurt(): Optional parameter $container declared before required parameter $flavour is implicitly treated as a required parameter in script on line 2

Fatal error: Uncaught ArgumentCountError: Too few arguments to function makeyogurt(), 1 passed in script on line 7 and exactly 2 expected in script:2
Stack trace:
# script(7): makeyogurt('raspberry')
# {main}
  thrown in script on line 2
```

Now, compare the above with this:

**Example #7 Correct usage of default function parameters**

```sql
<?php
function makeyogurt($flavour, $container = "bowl")
{
    return "Making a $container of $flavour yogurt.\n";
}

echo makeyogurt("raspberry"); // "raspberry" is $flavour
```

The above example will output:

```sql
Making a bowl of raspberry yogurt.
```

As of PHP 8.0.0, named arguments
can be used to skip over multiple optional parameters.

**Example #8 Correct usage of default function parameters**

```sql
<?php
function makeyogurt($container = "bowl", $flavour = "raspberry", $style = "Greek")
{
    return "Making a $container of $flavour $style yogurt.\n";
}

echo makeyogurt(style: "natural");
```

The above example will output:

```sql
Making a bowl of raspberry natural yogurt.
```

As of PHP 8.0.0, declaring mandatory parameters after optional parameters
is *deprecated*. This can generally be resolved by
dropping the default value, since it will never be used.
One exception to this rule are parameters of the form
`Type $param = null`, where the **`null`** default makes the type implicitly
nullable. This usage is deprecated as of PHP 8.4.0, and an explicit
nullable type
should be used instead.

**Example #9 Declaring optional parameters after mandatory parameters**

```sql
<?php
function foo($a = [], $b) {}     // Default not used; deprecated as of PHP 8.0.0
function foo($a, $b) {}          // Functionally equivalent, no deprecation notice

function bar(A $a = null, $b) {} // As of PHP 8.1.0, $a is implicitly required
                                 // (because it comes before the required one),
                                 // but implicitly nullable (deprecated as of PHP 8.4.0),
                                 // because the default parameter value is null
function bar(?A $a, $b) {}       // Recommended
```

> **Note**:
>
> As of PHP 7.1.0, omitting a parameter which does not specify a default
> throws an ArgumentCountError; in previous versions
> it raised a Warning.

> **Note**:
>
> Parameters that expect the argument by reference may have a default value.

### Variable-length argument lists

PHP has support for variable-length argument lists in
user-defined functions by using the
`...` token.

Parameter lists may include the
`...` token to denote that the function accepts a
variable number of arguments. The arguments will be passed into the
given variable as an array:

**Example #10 Using `...` to access variable arguments**

```sql
<?php
function sum(...$numbers) {
    $acc = 0;
    foreach ($numbers as $n) {
        $acc += $n;
    }
    return $acc;
}

echo sum(1, 2, 3, 4);
```

The above example will output:

```sql
10
```

`...` can also be used when calling functions to unpack
an array or Traversable variable or
literal into the argument list:

**Example #11 Using `...` to provide arguments**

```sql
<?php
function add($a, $b) {
    return $a + $b;
}

echo add(...[1, 2])."\n";

$a = [1, 2];
echo add(...$a);
```

The above example will output:

```sql
3
3
```

You may specify normal positional parameters before the
`...` token. In this case, only the trailing arguments
that don't match a positional argument will be added to the array
generated by `...`.

It is also possible to add a
type declaration before the
`...` token. If this is present, then all arguments
captured by `...` must match that parameter type.

**Example #12 Type declared variable arguments**

```sql
<?php
function total_intervals($unit, DateInterval ...$intervals) {
    $time = 0;
    foreach ($intervals as $interval) {
        $time += $interval->$unit;
    }
    return $time;
}

$a = new DateInterval('P1D');
$b = new DateInterval('P2D');
echo total_intervals('d', $a, $b).' days';

// This will fail, since null isn't a DateInterval object.
echo total_intervals('d', null);
```

The above example will output:

```sql
3 days
Fatal error: Uncaught TypeError: total_intervals(): Argument #2 must be of type DateInterval, null given, called in script on line 15 and defined in script:2
Stack trace:
# script(15): total_intervals('d', NULL)
# {main}
  thrown in script on line 2
```

Finally, variable arguments can also be passed
by reference by
prefixing the `...` with an ampersand
(`&`).

### Named Arguments

PHP 8.0.0 introduced named arguments as an extension of the existing
positional parameters. Named arguments allow passing arguments to a
function based on the parameter name, rather than the parameter position.
This makes the meaning of the argument self-documenting, makes the
arguments order-independent and allows skipping default values arbitrarily.

Named arguments are passed by prefixing the value with the parameter name
followed by a colon. Using reserved keywords as parameter names is allowed.
The parameter name must be an identifier, specifying dynamically
is not allowed.

**Example #13 Named argument syntax**

```sql
<?php
myFunction(paramName: $value);
array_foobar(array: $value);

// NOT supported.
function_name($variableStoringParamName: $value);
```

**Example #14 Positional arguments versus named arguments**

```sql
<?php
// Using positional arguments:
array_fill(0, 100, 50);

// Using named arguments:
array_fill(start_index: 0, count: 100, value: 50);
```

The order in which the named arguments are passed does not matter.

**Example #15 Same example as above with a different order of parameters**

```sql
<?php
array_fill(value: 50, count: 100, start_index: 0);
```

Named arguments can be combined with positional arguments. In this case,
the named arguments must come after the positional arguments.
It is also possible to specify only some of the optional arguments of a
function, regardless of their order.

**Example #16 Combining named arguments with positional arguments**

```sql
<?php
htmlspecialchars($string, double_encode: false);
// Same as
htmlspecialchars($string, ENT_QUOTES | ENT_SUBSTITUTE | ENT_HTML401, 'UTF-8', false);
```

Passing an argument to the same named parameter multiple times results in an
Error exception.

**Example #17 Error thrown when passing an argument to the same named parameter multiple times**

```sql
<?php
function foo($param) { ... }

foo(param: 1, param: 2);
// Error: Named parameter $param overwrites previous argument

foo(1, param: 2);
// Error: Named parameter $param overwrites previous argument
```

As of PHP 8.1.0, it is possible to use named arguments after unpacking the arguments.
A named argument *must not* override an already unpacked argument.

**Example #18 Use named arguments after unpacking**

```sql
<?php
function foo($a, $b, $c = 3, $d = 4) {
  return $a + $b + $c + $d;
}

var_dump(foo(...[1, 2], d: 40)); // 46
var_dump(foo(...['b' => 2, 'a' => 1], d: 40)); // 46

var_dump(foo(...[1, 2], b: 20)); // Fatal error. Named parameter $b overwrites previous argument
```

Some internal functions document an alternative signature, such as
session\_set\_save\_handler(), whose parameter names do not
exist in the function itself. These names cannot be used as named
arguments and result in an error.

### Found A Problem?
