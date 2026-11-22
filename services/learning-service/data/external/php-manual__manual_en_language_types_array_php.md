<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/language.types.array.php -->
# PHP: Arrays

For a list of all array functions, see the array functions chapter in the documentation.

An array in PHP is actually an ordered map. A map is a type that
associates *values* to *keys*. This type
is optimized for several different uses; it can be treated as an array,
list (vector), hash table (an implementation of a map), dictionary,
collection, stack, queue, and probably more. As array values can
be other arrays, trees and multidimensional arrays
are also possible.

Explanation of those data structures is beyond the scope of this manual, but
at least one example is provided for each of them. For more information, look
towards the considerable literature that exists about this broad topic.

### Syntax

#### Specifying with array()

An array can be created using the array()
language construct. It takes any number of comma-separated
`key => value` pairs
as arguments.

```sql
array(
    key  => value,
    key2 => value2,
    key3 => value3,
    ...
)
```

The comma after the last array element is optional and can be omitted. This is usually done
for single-line arrays, i.e. `array(1, 2)` is preferred over
`array(1, 2, )`. For multi-line arrays on the other hand the trailing comma
is commonly used, as it allows easier addition of new elements at the end.

> **Note**:
>
> A short array syntax exists which replaces
> `array()` with `[]`.

**Example #1 A simple array**

```sql
<?php
$array1 = array(
    "foo" => "bar",
    "bar" => "foo",
);

// Using the short array syntax
$array2 = [
    "foo" => "bar",
    "bar" => "foo",
];

var_dump($array1, $array2);
?>
```

The key can either be an int
or a string. The value can be
of any type.

Additionally the following key casts will occur:

* Strings containing valid decimal ints, unless the number is preceded by a `+` sign, will be cast to the
  int type. E.g. the key `"8"` will actually be
  stored under `8`. On the other hand `"08"` will
  not be cast, as it isn't a valid decimal integer.
* Floats are also cast to ints, which means that the
  fractional part will be truncated. E.g. the key `8.7` will actually
  be stored under `8`.
* Bools are cast to ints, too, i.e. the key
  **`true`** will actually be stored under `1`
  and the key **`false`** under `0`.
* Null will be cast to the empty string, i.e. the key
  **`null`** will actually be stored under `""`.
* Arrays and objects *can not* be used as keys.
  Doing so will result in a warning: `Illegal offset type`.

If multiple elements in the array declaration use the same key, only the last one
will be used as all others are overwritten.

**Example #2 Type Casting and Overwriting example**

```sql
<?php
$array = array(
    1    => "a",
    "1"  => "b",
    1.5  => "c",
    true => "d",
);
var_dump($array);
?>
```

The above example will output:

```sql
array(1) {
  [1]=>
  string(1) "d"
}
```

As all the keys in the above example are cast to `1`, the value will be overwritten
on every new element and the last assigned value `"d"` is the only one left over.

PHP arrays can contain int and string keys at the same time
as PHP does not distinguish between indexed and associative arrays.

**Example #3 Mixed int and string keys**

```sql
<?php
$array = array(
    "foo" => "bar",
    "bar" => "foo",
    100   => -100,
    -100  => 100,
);
var_dump($array);
?>
```

The above example will output:

```sql
array(4) {
  ["foo"]=>
  string(3) "bar"
  ["bar"]=>
  string(3) "foo"
  [100]=>
  int(-100)
  [-100]=>
  int(100)
}
```

The key is optional. If it is not specified, PHP will
use the increment of the largest previously used int key.

**Example #4 Indexed arrays without key**

```sql
<?php
$array = array("foo", "bar", "hello", "world");
var_dump($array);
?>
```

The above example will output:

```sql
array(4) {
  [0]=>
  string(3) "foo"
  [1]=>
  string(3) "bar"
  [2]=>
  string(5) "hello"
  [3]=>
  string(5) "world"
}
```

It is possible to specify the key only for some elements and leave it out for others:

**Example #5 Keys not on all elements**

```sql
<?php
$array = array(
         "a",
         "b",
    6 => "c",
         "d",
);
var_dump($array);
?>
```

The above example will output:

```sql
array(4) {
  [0]=>
  string(1) "a"
  [1]=>
  string(1) "b"
  [6]=>
  string(1) "c"
  [7]=>
  string(1) "d"
}
```

As you can see the last value `"d"` was assigned the key
`7`. This is because the largest integer key before that
was `6`.

**Example #6 Complex Type Casting and Overwriting example**

This example includes all variations of type casting of keys and overwriting
of elements.

```sql
<?php
$array = array(
    1    => 'a',
    '1'  => 'b', // the value "a" will be overwritten by "b"
    1.5  => 'c', // the value "b" will be overwritten by "c"
    -1 => 'd',
    '01'  => 'e', // as this is not an integer string it will NOT override the key for 1
    '1.5' => 'f', // as this is not an integer string it will NOT override the key for 1
    true => 'g', // the value "c" will be overwritten by "g"
    false => 'h',
    '' => 'i',
    null => 'j', // the value "i" will be overwritten by "j"
    'k', // value "k" is assigned the key 2. This is because the largest integer key before that was 1
    2 => 'l', // the value "k" will be overwritten by "l"
);

var_dump($array);
?>
```

The above example will output:

```sql
array(7) {
  [1]=>
  string(1) "g"
  [-1]=>
  string(1) "d"
  ["01"]=>
  string(1) "e"
  ["1.5"]=>
  string(1) "f"
  [0]=>
  string(1) "h"
  [""]=>
  string(1) "j"
  [2]=>
  string(1) "l"
}
```

**Example #7 Negative index example**

When assigning a negative integer key `n`, PHP will take care to
assign the next key to `n+1`.

```sql
<?php
$array = [];

$array[-5] = 1;
$array[] = 2;

var_dump($array);
?>
```

The above example will output:

```sql
array(2) {
  [-5]=>
  int(1)
  [-4]=>
  int(2)
}
```

**Warning**

Prior to PHP 8.3.0, assigning a negative integer key `n` would
assign the next key to `0`, the previous example would
therefore output:

```sql
array(2) {
  [-5]=>
  int(1)
  [0]=>
  int(2)
}
```

#### Accessing array elements with square bracket syntax

Array elements can be accessed using the `array[key]` syntax.

**Example #8 Accessing array elements**

```sql
<?php
$array = array(
    "foo" => "bar",
    42    => 24,
    "multi" => array(
         "dimensional" => array(
             "array" => "foo"
         )
    )
);

var_dump($array["foo"]);
var_dump($array[42]);
var_dump($array"multi"["array"]);
?>
```

The above example will output:

```sql
string(3) "bar"
int(24)
string(3) "foo"
```

> **Note**:
>
> Prior to PHP 8.0.0, square brackets and curly braces could be used interchangeably
> for accessing array elements (e.g. `$array[42]` and `$array{42}`
> would both do the same thing in the example above).
> The curly brace syntax was deprecated as of PHP 7.4.0 and no longer supported as of PHP 8.0.0.

**Example #9 Array dereferencing**

```sql
<?php
function getArray() {
    return array(1, 2, 3);
}

$secondElement = getArray()[1];

var_dump($secondElement);
?>
```

> **Note**:
>
> Attempting to access an array key which has not been defined is
> the same as accessing any other undefined variable:
> an **`E_WARNING`**-level error message
> (**`E_NOTICE`**-level prior to PHP 8.0.0) will be
> issued, and the result will be **`null`**.

> **Note**:
>
> Array dereferencing a scalar value which is not a string
> yields **`null`**. Prior to PHP 7.4.0, that did not issue an error message.
> As of PHP 7.4.0, this issues **`E_NOTICE`**;
> as of PHP 8.0.0, this issues **`E_WARNING`**.

#### Creating/modifying with square bracket syntax

An existing array can be modified by explicitly setting values
in it.

This is done by assigning values to the array, specifying the
key in brackets. The key can also be omitted, resulting in an empty pair of
brackets (`[]`).

```sql
$arr[key] = value;
$arr[] = value;
// key may be an int or string
// value may be any value of any type
```

If $arr doesn't exist yet or is set to **`null`** or **`false`**, it will be created, so this is
also an alternative way to create an array. This practice is
however discouraged because if $arr already contains
some value (e.g. string from request variable) then this
value will stay in place and `[]` may actually stand
for string access
operator. It is always better to initialize a variable by a direct
assignment.

> **Note**:
>
> As of PHP 7.1.0, applying the empty index operator on a string throws a fatal
> error. Formerly, the string was silently converted to an array.

> **Note**:
>
> As of PHP 8.1.0, creating a new array from **`false`** value is deprecated.
> Creating a new array from **`null`** and undefined values is still allowed.

To change a certain
value, assign a new value to that element using its key. To remove a
key/value pair, call the unset() function on it.

**Example #10 Using Square Brackets with Arrays**

```sql
<?php
$arr = array(5 => 1, 12 => 2);

$arr[] = 56;    // This is the same as $arr[13] = 56;
                // at this point of the script

$arr["x"] = 42; // This adds a new element to
                // the array with key "x"

unset($arr[5]); // This removes the element from the array

var_dump($arr);

unset($arr);    // This deletes the whole array

var_dump($arr);
?>
```

> **Note**:
>
> If no key is specified, the key will be the
> maximum existing integer index + `1`. If the array has no positive
> integer indices, the key will be `0`.
> As of PHP 8.3.0, it can also be a negative integer.
>
> Note that the maximum integer key used for this *need not
> currently exist in the array*. It need only have
> existed in the array at some time since the last time the
> array was re-indexed. The following example illustrates:
>
> ```sql
> <?php
> // Create a simple array.
> $array = array(1, 2, 3, 4, 5);
> print_r($array);
>
> // Now delete every item, but leave the array itself intact:
> foreach ($array as $i => $value) {
>     unset($array[$i]);
> }
> print_r($array);
>
> // Append an item (note that the new key is 5, instead of 0).
> $array[] = 6;
> print_r($array);
>
> // Re-index:
> $array = array_values($array);
> $array[] = 7;
> print_r($array);
> ?>
> ```
>
> The above example will output:
>
> ```sql
> Array
> (
>     [0] => 1
>     [1] => 2
>     [2] => 3
>     [3] => 4
>     [4] => 5
> )
> Array
> (
> )
> Array
> (
>     [5] => 6
> )
> Array
> (
>     [0] => 6
>     [1] => 7
> )
> ```

#### Array destructuring

Arrays can be destructured using the `[]` (as of PHP 7.1.0) or
list() language constructs. These
constructs can be used to destructure an array into distinct variables.

**Example #11 Array Destructuring**

```sql
<?php
$source_array = ['foo', 'bar', 'baz'];

[$foo, $bar, $baz] = $source_array;

echo $foo, PHP_EOL;    // prints "foo"
echo $bar, PHP_EOL;    // prints "bar"
echo $baz, PHP_EOL;    // prints "baz"
?>
```

Array destructuring can be used in `foreach` to destructure
a multi-dimensional array while iterating over it.

**Example #12 Array Destructuring in Foreach**

```sql
<?php
$source_array = [
    [1, 'John'],
    [2, 'Jane'],
];

foreach ($source_array as [$id, $name]) {
    echo "{$id}: '{$name}'\n";
}
?>
```

Array elements will be ignored if the variable is not provided. Array
destructuring always starts at index `0`.

**Example #13 Ignoring Elements**

```sql
<?php
$source_array = ['foo', 'bar', 'baz'];

// Assign the element at index 2 to the variable $baz
[, , $baz] = $source_array;

echo $baz;    // prints "baz"
?>
```

As of PHP 7.1.0, associative arrays can be destructured too. This also
allows for easier selection of the right element in numerically indexed
arrays as the index can be explicitly specified.

**Example #14 Destructuring Associative Arrays**

```sql
<?php
$source_array = ['foo' => 1, 'bar' => 2, 'baz' => 3];

// Assign the element at index 'baz' to the variable $three
['baz' => $three] = $source_array;

echo $three, PHP_EOL;  // prints 3

$source_array = ['foo', 'bar', 'baz'];

// Assign the element at index 2 to the variable $baz
[2 => $baz] = $source_array;

echo $baz, PHP_EOL;    // prints "baz"
?>
```

Array destructuring can be used for easy swapping of two variables.

**Example #15 Swapping Two Variable**

```sql
<?php
$a = 1;
$b = 2;

[$b, $a] = [$a, $b];

echo $a, PHP_EOL;    // prints 2
echo $b, PHP_EOL;    // prints 1
?>
```

> **Note**:
>
> The spread operator (`...`) is not supported in assignments.

> **Note**:
>
> Attempting to access an array key which has not been defined is
> the same as accessing any other undefined variable:
> an **`E_WARNING`**-level error message
> (**`E_NOTICE`**-level prior to PHP 8.0.0) will be
> issued, and the result will be **`null`**.

> **Note**:
>
> Destructuring a scalar value assigns **`null`** to all variables.

### Useful functions

There are quite a few useful functions for working with arrays. See the
array functions section.

> **Note**:
>
> The unset() function allows removing keys from an
> array. Be aware that the array will *not* be
> reindexed. If a true "remove and shift" behavior is desired, the
> array can be reindexed using the
> array\_values() function.
>
> **Example #16 Unsetting Intermediate Elements**
>
> ```sql
> <?php
> $a = array(1 => 'one', 2 => 'two', 3 => 'three');
>
> /* will produce an array that would have been defined as
>    $a = array(1 => 'one', 3 => 'three');
>    and NOT
>    $a = array(1 => 'one', 2 =>'three');
> */
> unset($a[2]);
> var_dump($a);
>
> $b = array_values($a);
> // Now $b is array(0 => 'one', 1 =>'three')
> var_dump($b);
> ?>
> ```

The `foreach` control
structure exists specifically for arrays. It provides an easy
way to traverse an array.

### Array do's and don'ts

#### Why is `$foo[bar]` wrong?

Always use quotes around a string literal array index. For example,
`$foo['bar']` is correct, while
`$foo[bar]` is not. But why? It is common to encounter this
kind of syntax in old scripts:

```sql
<?php
$foo[bar] = 'enemy';
echo $foo[bar];
// etc
?>
```

This is wrong, but it works. The reason is that this code has an undefined
constant (`bar`) rather than a string (`'bar'` - notice the
quotes). It works because PHP automatically converts a
*bare string* (an unquoted string which does
not correspond to any known symbol) into a string which
contains the bare string. For instance, if there is no defined
constant named **`bar`**, then PHP will substitute in the
string `'bar'` and use that.

**Warning**

The fallback to treat an undefined constant as bare string issues an error
of level **`E_NOTICE`**.
This has been deprecated as of PHP 7.2.0, and issues an error
of level **`E_WARNING`**.
As of PHP 8.0.0, it has been removed and throws an
Error exception.

This does not mean to *always* quote the key. Do not
quote keys which are constants or
variables, as this will prevent
PHP from interpreting them.

**Example #17 Key Quoting**

```sql
<?php
error_reporting(E_ALL);
ini_set('display_errors', true);
ini_set('html_errors', false);

// Simple array:
$array = array(1, 2);
$count = count($array);

for ($i = 0; $i < $count; $i++) {
    echo "\nChecking $i: \n";
    echo "Bad: " . $array['$i'] . "\n";
    echo "Good: " . $array[$i] . "\n";
    echo "Bad: {$array['$i']}\n";
    echo "Good: {$array[$i]}\n";
}
?>
```

The above example will output:

```sql
Checking 0:
Notice: Undefined index:  $i in /path/to/script.html on line 9
Bad:
Good: 1
Notice: Undefined index:  $i in /path/to/script.html on line 11
Bad:
Good: 1

Checking 1:
Notice: Undefined index:  $i in /path/to/script.html on line 9
Bad:
Good: 2
Notice: Undefined index:  $i in /path/to/script.html on line 11
Bad:
Good: 2
```

More examples to demonstrate this behaviour:

**Example #18 More Examples**

```sql
<?php
// Show all errors
error_reporting(E_ALL);

$arr = array('fruit' => 'apple', 'veggie' => 'carrot');

// Correct
echo $arr['fruit'], PHP_EOL;  // apple
echo $arr['veggie'], PHP_EOL; // carrot

// Incorrect. This does not work and throws a PHP Error because
// of an undefined constant named fruit
//
// Error: Undefined constant "fruit"
try {
    echo $arr[fruit];
} catch (Error $e) {
    echo get_class($e), ': ', $e->getMessage(), PHP_EOL;
}

// This defines a constant to demonstrate what's going on.  The value 'veggie'
// is assigned to a constant named fruit.
define('fruit', 'veggie');

// Notice the difference now
echo $arr['fruit'], PHP_EOL;  // apple
echo $arr[fruit], PHP_EOL;    // carrot

// The following is okay, as it's inside a string. Constants are not looked for
// within strings, so no error occurs here
echo "Hello $arr[fruit]", PHP_EOL;      // Hello apple

// With one exception: braces surrounding arrays within strings allows constants
// to be interpreted
echo "Hello {$arr[fruit]}", PHP_EOL;    // Hello carrot
echo "Hello {$arr['fruit']}", PHP_EOL;  // Hello apple

// Concatenation is another option
echo "Hello " . $arr['fruit'], PHP_EOL; // Hello apple
?>
```

```sql
<?php
// This will not work, and will result in a parse error, such as:
// Parse error: parse error, expecting T_STRING' or T_VARIABLE' or T_NUM_STRING'
// This of course applies to using superglobals in strings as well
print "Hello $arr['fruit']";
print "Hello $_GET['foo']";
?>
```

As stated in the syntax
section, what's inside the square brackets ('`[`' and
'`]`') must be an expression. This means that code like
this works:

```sql
<?php
echo $arr[somefunc($bar)];
?>
```

This is an example of using a function return value as the array index. PHP
also knows about constants:

```sql
<?php
$error_descriptions[E_ERROR]   = "A fatal error has occurred";
$error_descriptions[E_WARNING] = "PHP issued a warning";
$error_descriptions[E_NOTICE]  = "This is just an informal notice";
?>
```

Note that **`E_ERROR`** is also a valid identifier, just like
`bar` in the first example. But the last example is in fact
the same as writing:

```sql
<?php
$error_descriptions[1] = "A fatal error has occurred";
$error_descriptions[2] = "PHP issued a warning";
$error_descriptions[8] = "This is just an informal notice";
?>
```

because **`E_ERROR`** equals `1`, etc.

##### So why is it bad then?

At some point in the future, the PHP team might want to add another
constant or keyword, or a constant in other code may interfere. For
example, it is already wrong to use the words `empty` and
`default` this way, since they are
reserved keywords.

> **Note**:
>
> To reiterate, inside a double-quoted string, it's valid to
> not surround array indexes with quotes so `"$foo[bar]"`
> is valid. See the above examples for details on why as well as the section
> on variable parsing in
> strings.

### Converting to array

For any of the types int, float,
string, bool and resource,
converting a value to an array results in an array with a single
element with index zero and the value of the scalar which was converted. In
other words, `(array) $scalarValue` is exactly the same as
`array($scalarValue)`.

If an object is converted to an array, the result
is an array whose elements are the object's
properties. The keys are the member variable names, with a few notable
exceptions: integer properties are inaccessible;
private variables have the class name prepended to the variable
name; protected variables have a '\*' prepended to the variable name. These
prepended values have `NUL` bytes on either side.
Uninitialized typed properties
are silently discarded.

**Example #19 Converting to an Array**

```sql
<?php

class A {
    private $B;
    protected $C;
    public $D;
    function __construct()
    {
        $this->{1} = null;
    }
}

var_export((array) new A());
?>
```

The above example will output:

```sql
array (
  '' . "\0" . 'A' . "\0" . 'B' => NULL,
  '' . "\0" . '*' . "\0" . 'C' => NULL,
  'D' => NULL,
  1 => NULL,
)
```

These `NUL` can result in some unexpected behaviour:

**Example #20 Casting an Object to an Array**

```sql
<?php

class A {
    private $A; // This will become '\0A\0A'
}

class B extends A {
    private $A; // This will become '\0B\0A'
    public $AA; // This will become 'AA'
}

var_dump((array) new B());
?>
```

Output of the above example in PHP 8.0:

```sql
array(3) {
  ["BA"]=>
  NULL
  ["AA"]=>
  NULL
  ["AA"]=>
  NULL
}
```

Output of the above example in PHP 8.1:

```sql
array(3) {
  ["AA"]=>
  NULL
  ["BA"]=>
  NULL
  ["AA"]=>
  NULL
}
```

The above will appear to have two keys named 'AA', although one of them is
actually named '\0A\0A'.

Converting **`null`** to an array results in an empty
array.

### Comparing

It is possible to compare arrays with the array\_diff()
function and with
array operators.

### Array unpacking

An array prefixed by `...` will be expanded in place during array definition.
Only arrays and objects which implement Traversable can be expanded.
Array unpacking with `...` is available as of PHP 7.4.0. This is also called
the spread operator.

It's possible to expand multiple times, and add normal elements before or after the `...` operator:

**Example #21 Simple array unpacking**

```sql
<?php
// Using short array syntax.
// Also, works with array() syntax.
$arr1 = [1, 2, 3];
$arr2 = [...$arr1]; // [1, 2, 3]
$arr3 = [0, ...$arr1]; // [0, 1, 2, 3]
$arr4 = [...$arr1, ...$arr2, 111]; // [1, 2, 3, 1, 2, 3, 111]
$arr5 = [...$arr1, ...$arr1]; // [1, 2, 3, 1, 2, 3]

function getArr() {
  return ['a', 'b'];
}
$arr6 = [...getArr(), 'c' => 'd']; // ['a', 'b', 'c' => 'd']

var_dump($arr1, $arr2, $arr3, $arr4, $arr5, $arr6);
?>
```

Unpacking an array with the `...` operator follows the semantics of the array\_merge() function.
That is, later string keys overwrite earlier ones and integer keys are renumbered:

**Example #22 Array unpacking with duplicate key**

```sql
<?php
// string key
$arr1 = ["a" => 1];
$arr2 = ["a" => 2];
$arr3 = ["a" => 0, ...$arr1, ...$arr2];
var_dump($arr3); // ["a" => 2]

// integer key
$arr4 = [1, 2, 3];
$arr5 = [4, 5, 6];
$arr6 = [...$arr4, ...$arr5];
var_dump($arr6); // [1, 2, 3, 4, 5, 6]
// Which is [0 => 1, 1 => 2, 2 => 3, 3 => 4, 4 => 5, 5 => 6]
// where the original integer keys have not been retained.
?>
```

> **Note**:
>
> Keys that are neither integers nor strings throw a TypeError.
> Such keys can only be generated by a Traversable object.

> **Note**:
>
> Prior to PHP 8.1, unpacking an array which has a string key is not supported:
>
> ```sql
> <?php
>
> $arr1 = [1, 2, 3];
> $arr2 = ['a' => 4];
> $arr3 = [...$arr1, ...$arr2];
> // Fatal error: Uncaught Error: Cannot unpack array with string keys in example.php:5
>
> $arr4 = [1, 2, 3];
> $arr5 = [4, 5];
> $arr6 = [...$arr4, ...$arr5]; // works. [1, 2, 3, 4, 5]
> ?>
> ```

### Examples

The array type in PHP is very versatile. Here are some examples:

**Example #23 Array Versatility**

```sql
<?php
// This:
$a = array( 'color' => 'red',
            'taste' => 'sweet',
            'shape' => 'round',
            'name'  => 'apple',
            4        // key will be 0
          );

$b = array('a', 'b', 'c');

var_dump($a, $b);

// . . .is completely equivalent with this:
$a = array();
$a['color'] = 'red';
$a['taste'] = 'sweet';
$a['shape'] = 'round';
$a['name']  = 'apple';
$a[]        = 4;        // key will be 0

$b = array();
$b[] = 'a';
$b[] = 'b';
$b[] = 'c';

// After the above code is executed, $a will be the array
// array('color' => 'red', 'taste' => 'sweet', 'shape' => 'round',
// 'name' => 'apple', 0 => 4), and $b will be the array
// array(0 => 'a', 1 => 'b', 2 => 'c'), or simply array('a', 'b', 'c').

var_dump($a, $b);
?>
```

**Example #24 Using array()**

```sql
<?php
// Array as (property-)map
$map = array( 'version'    => 4,
              'OS'         => 'Linux',
              'lang'       => 'english',
              'short_tags' => true
            );
var_dump($map);

// strictly numerical keys
// this is the same as array(0 => 7, 1 => 8, ...)
$array = array( 7,
                8,
                0,
                156,
                -10
              );
var_dump($array);

$switching = array(         10, // key = 0
                    5    =>  6,
                    3    =>  7,
                    'a'  =>  4,
                            11, // key = 6 (maximum of integer-indices was 5)
                    '8'  =>  2, // key = 8 (integer!)
                    '02' => 77, // key = '02'
                    0    => 12  // the value 10 will be overwritten by 12
                  );
var_dump($switching);

// empty array
$empty = array();
var_dump($empty);
?>
```

**Example #25 Collection**

```sql
<?php
$colors = array('red', 'blue', 'green', 'yellow');

foreach ($colors as $color) {
    echo "Do you like $color?\n";
}

?>
```

The above example will output:

```sql
Do you like red?
Do you like blue?
Do you like green?
Do you like yellow?
```

Changing the values of the array directly is possible
by passing them by reference.

**Example #26 Changing element in the loop**

```sql
<?php
$colors = array('red', 'blue', 'green', 'yellow');

foreach ($colors as &$color) {
    $color = mb_strtoupper($color);
}
unset($color); /* ensure that following writes to
$color will not modify the last array element */

print_r($colors);
?>
```

The above example will output:

```sql
Array
(
    [0] => RED
    [1] => BLUE
    [2] => GREEN
    [3] => YELLOW
)
```

This example creates a one-based array.

**Example #27 One-based index**

```sql
<?php
$firstquarter = array(1 => 'January', 'February', 'March');
print_r($firstquarter);
?>
```

The above example will output:

```sql
Array
(
    [1] => January
    [2] => February
    [3] => March
)
```

**Example #28 Filling an array**

```sql
<?php
// fill an array with all items from a directory
$handle = opendir('.');
while (false !== ($file = readdir($handle))) {
    $files[] = $file;
}
closedir($handle);

var_dump($files);
?>
```

Arrays are ordered. The order can be changed using various
sorting functions. See the array functions
section for more information. The count() function can be
used to count the number of items in an array.

**Example #29 Sorting an array**

```sql
<?php
sort($files);
print_r($files);
?>
```

Because the value of an array can be anything, it can also be
another array. This enables the creation of recursive and
multi-dimensional arrays.

**Example #30 Recursive and multi-dimensional arrays**

```sql
<?php
$fruits = array ( "fruits"  => array ( "a" => "orange",
                                       "b" => "banana",
                                       "c" => "apple"
                                     ),
                  "numbers" => array ( 1,
                                       2,
                                       3,
                                       4,
                                       5,
                                       6
                                     ),
                  "holes"   => array (      "first",
                                       5 => "second",
                                            "third"
                                     )
                );
var_dump($fruits);

// Some examples to address values in the array above
echo $fruits"holes";    // prints "second"
echo $fruits"fruits"; // prints "orange"
unset($fruits"holes");  // remove "first"

// Create a new multi-dimensional array
$juices"apple" = "good";
var_dump($juices);
?>
```

Array assignment always involves value copying. Use the
reference operator to copy an
array by reference.

**Example #31 Array Copying**

```sql
<?php
$arr1 = array(2, 3);
$arr2 = $arr1;
$arr2[] = 4; // $arr2 is changed,
             // $arr1 is still array(2, 3)

$arr3 = &$arr1;
$arr3[] = 4; // now $arr1 and $arr3 are the same

var_dump($arr1, $arr2, $arr3);
?>
```

### Found A Problem?
