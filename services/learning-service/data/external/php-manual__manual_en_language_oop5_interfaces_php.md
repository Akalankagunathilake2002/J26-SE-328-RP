<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/language.oop5.interfaces.php -->
# PHP: Object Interfaces

Object interfaces allow you to create code which specifies which methods and properties a
class must implement, without having to define how these methods or properties are
implemented. Interfaces share a namespace with classes, traits, and enumerations, so they may
not use the same name.

Interfaces are defined in the same way as a class, but with the `interface`
keyword replacing the `class` keyword and without any of the methods having
their contents defined.

All methods declared in an interface must be public; this is the nature of an
interface.

In practice, interfaces serve two complementary purposes:

* To allow developers to create objects of different classes that may be used interchangeably
  because they implement the same interface or interfaces. A common example is multiple database access services,
  multiple payment gateways, or different caching strategies. Different implementations may
  be swapped out without requiring any changes to the code that uses them.
* To allow a function or method to accept and operate on a parameter that conforms to an
  interface, while not caring what else the object may do or how it is implemented. These interfaces
  are often named like `Iterable`, `Cacheable`, `Renderable`,
  and so on to describe the significance of the behavior.

Interfaces may define
magic methods to require implementing classes to
implement those methods.

> **Note**:
>
> Although they are supported, including constructors
> in interfaces is strongly discouraged. Doing so significantly reduces the flexibility of the object implementing the
> interface. Additionally, constructors are not enforced by inheritance rules, which can cause inconsistent
> and unexpected behavior.

### `implements`

To implement an interface, the `implements` operator is used.
All methods in the interface must be implemented within a class; failure to do
so will result in a fatal error. Classes may implement more than one interface
if desired by separating each interface with a comma.

**Warning**

A class that implements an interface may use a different name for its parameters than
the interface. However, as of PHP 8.0 the language supports named arguments, which means
callers may rely on the parameter name in the interface. For that reason, it is strongly
recommended that developers use the same parameter names as the interface being implemented.

> **Note**:
>
> Interfaces can be extended like classes using the extends
> operator.

> **Note**:
>
> The class implementing the interface must declare all methods in the interface
> with a compatible signature. A class can implement multiple interfaces
> which declare a method with the same name. In this case, the implementation must follow the
> signature compatibility rules for all the interfaces. So
> covariance and contravariance can be applied.

### Constants

It's possible for interfaces to have constants. Interface constants work exactly
like class constants.
Prior to PHP 8.1.0, they cannot be overridden by a class/interface that inherits them.

### Properties

As of PHP 8.4.0, interfaces may also declare properties.
If they do, the declaration must specify if the property is to be readable,
writeable, or both.
The interface declaration applies only to public read and write access.

A class may satisfy an interface property in multiple ways.
It may define a public property.
It may define a public
virtual property
that implements only the corresponding hook.
Or a read property may be satisfied by a `readonly` property.
However, an interface property that is settable may not be `readonly`.

**Example #1 Interface properties example**

```sql
<?php
interface I
{
    // An implementing class MUST have a publicly-readable property,
    // but whether or not it's publicly settable is unrestricted.
    public string $readable { get; }

    // An implementing class MUST have a publicly-writeable property,
    // but whether or not it's publicly readable is unrestricted.
    public string $writeable { set; }

    // An implementing class MUST have a property that is both publicly
    // readable and publicly writeable.
    public string $both { get; set; }
}

// This class implements all three properties as traditional, un-hooked
// properties. That's entirely valid.
class C1 implements I
{
    public string $readable;

    public string $writeable;

    public string $both;
}

// This class implements all three properties using just the hooks
// that are requested.  This is also entirely valid.
class C2 implements I
{
    private string $written = '';
    private string $all = '';

    // Uses only a get hook to create a virtual property.
    // This satisfies the "public get" requirement.
    // It is not writeable, but that is not required by the interface.
    public string $readable { get => strtoupper($this->writeable); }

    // The interface only requires the property be settable,
    // but also including get operations is entirely valid.
    // This example creates a virtual property, which is fine.
    public string $writeable {
        get => $this->written;
        set {
            $this->written = $value;
        }
    }

    // This property requires both read and write be possible,
    // so we need to either implement both, or allow it to have
    // the default behavior.
    public string $both {
        get => $this->all;
        set {
            $this->all = strtoupper($value);
        }
    }
}
?>
```

### Examples

**Example #2 Interface example**

```sql
<?php

// Declare the interface 'Template'
interface Template
{
    public function setVariable($name, $var);
    public function getHtml($template);
}

// Implement the interface
// This will work
class WorkingTemplate implements Template
{
    private $vars = [];

    public function setVariable($name, $var)
    {
        $this->vars[$name] = $var;
    }

    public function getHtml($template)
    {
        foreach($this->vars as $name => $value) {
            $template = str_replace('{' . $name . '}', $value, $template);
        }

        return $template;
    }
}

// This will not work
// Fatal error: Class BadTemplate contains 1 abstract methods
// and must therefore be declared abstract (Template::getHtml)
class BadTemplate implements Template
{
    private $vars = [];

    public function setVariable($name, $var)
    {
        $this->vars[$name] = $var;
    }
}
?>
```

**Example #3 Extendable Interfaces**

```sql
<?php
interface A
{
    public function foo();
}

interface B extends A
{
    public function baz(Baz $baz);
}

// This will work
class C implements B
{
    public function foo()
    {
    }

    public function baz(Baz $baz)
    {
    }
}

// This will not work and result in a fatal error
class D implements B
{
    public function foo()
    {
    }

    public function baz(Foo $foo)
    {
    }
}
?>
```

**Example #4 Variance compatibility with multiple interfaces**

```sql
<?php
class Foo {}
class Bar extends Foo {}

interface A {
    public function myfunc(Foo $arg): Foo;
}

interface B {
    public function myfunc(Bar $arg): Bar;
}

class MyClass implements A, B
{
    public function myfunc(Foo $arg): Bar
    {
        return new Bar();
    }
}
?>
```

**Example #5 Multiple interface inheritance**

```sql
<?php
interface A
{
    public function foo();
}

interface B
{
    public function bar();
}

interface C extends A, B
{
    public function baz();
}

class D implements C
{
    public function foo()
    {
    }

    public function bar()
    {
    }

    public function baz()
    {
    }
}
?>
```

**Example #6 Interfaces with constants**

```sql
<?php
interface A
{
    const B = 'Interface constant';
}

// Prints: Interface constant
echo A::B;

class B implements A
{
    const B = 'Class constant';
}

// Prints: Class constant
// Prior to PHP 8.1.0, this will however not work because it was not
// allowed to override constants.
echo B::B;
?>
```

**Example #7 Interfaces with abstract classes**

```sql
<?php
interface A
{
    public function foo(string $s): string;

    public function bar(int $i): int;
}

// An abstract class may implement only a portion of an interface.
// Classes that extend the abstract class must implement the rest.
abstract class B implements A
{
    public function foo(string $s): string
    {
        return $s . PHP_EOL;
    }
}

class C extends B
{
    public function bar(int $i): int
    {
        return $i * 2;
    }
}
?>
```

**Example #8 Extending and implementing simultaneously**

```sql
<?php

class One
{
    /* ... */
}

interface Usable
{
    /* ... */
}

interface Updatable
{
    /* ... */
}

// The keyword order here is important. 'extends' must come first.
class Two extends One implements Usable, Updatable
{
    /* ... */
}
?>
```

An interface, together with type declarations, provides a good way to make sure
that a particular object contains particular methods. See
instanceof operator and
type declarations.

### Found A Problem?
