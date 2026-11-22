<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/language.oop5.static.php -->
# PHP: Static Keyword

**Tip**

This page describes the use of the `static` keyword to
define static methods and properties. `static` can also
be used to
define static variables,
define static anonymous functions
and for
late static bindings.
Please refer to those pages for information on those meanings of
`static`.

Declaring class properties or methods as static makes them accessible
without needing an instantiation of the class.
These can also be accessed statically within an instantiated class object.

### Static methods

Because static methods are callable without an instance of
the object created, the pseudo-variable $this is
not available inside methods declared as static.

**Warning**

Calling non-static methods statically throws an Error.

Prior to PHP 8.0.0, calling non-static methods statically was deprecated, and
generated an **`E_DEPRECATED`** warning.

**Example #1 Static method example**

```sql
<?php
class Foo {
    public static function aStaticMethod() {
        // ...
    }
}

Foo::aStaticMethod();
$classname = 'Foo';
$classname::aStaticMethod();
?>
```

### Static properties

Static properties are accessed using the
Scope Resolution Operator
(`::`) and cannot be accessed through the object operator
(`->`).

It's possible to reference the class using a variable.
The variable's value cannot be a keyword (e.g. `self`,
`parent` and `static`).

**Example #2 Static property example**

```sql
<?php
class Foo
{
    public static $my_static = 'foo';

    public function staticValue() {
        return self::$my_static;
    }
}

class Bar extends Foo
{
    public function fooStatic() {
        return parent::$my_static;
    }
}

print Foo::$my_static . "\n";

$foo = new Foo();
print $foo->staticValue() . "\n";
print $foo->my_static . "\n";      // Undefined "Property" my_static

print $foo::$my_static . "\n";
$classname = 'Foo';
print $classname::$my_static . "\n";

print Bar::$my_static . "\n";
$bar = new Bar();
print $bar->fooStatic() . "\n";
?>
```

Output of the above example in PHP 8 is similar to:

```sql
foo
foo

Notice: Accessing static property Foo::$my_static as non static in /in/V0Rvv on line 23

Warning: Undefined property: Foo::$my_static in /in/V0Rvv on line 23

foo
foo
foo
foo
```

### Found A Problem?
