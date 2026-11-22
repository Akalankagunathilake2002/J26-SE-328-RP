<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/language.oop5.traits.php -->
# PHP: Traits

PHP implements a way to reuse code called Traits.

Traits are a mechanism for code reuse in single inheritance languages such as
PHP. A Trait is intended to reduce some limitations of single inheritance by
enabling a developer to reuse sets of methods freely in several independent
classes living in different class hierarchies. The semantics of the combination
of Traits and classes is defined in a way which reduces complexity, and avoids
the typical problems associated with multiple inheritance and Mixins.

A Trait is similar to a class, but only intended to group functionality in a
fine-grained and consistent way. It is not possible to instantiate a Trait on
its own. It is an addition to traditional inheritance and enables horizontal
composition of behavior; that is, the application of class members without
requiring inheritance.

**Example #1 Trait example**

```sql
<?php

trait TraitA {
    public function sayHello() {
        echo 'Hello';
    }
}

trait TraitB {
    public function sayWorld() {
        echo 'World';
    }
}

class MyHelloWorld
{
    use TraitA, TraitB; // A class can use multiple traits

    public function sayHelloWorld() {
        $this->sayHello();
        echo ' ';
        $this->sayWorld();
        echo "!\n";
    }
}

$myHelloWorld = new MyHelloWorld();
$myHelloWorld->sayHelloWorld();

?>
```

The above example will output:

```sql
Hello World!
```

### Precedence

An inherited member from a base class is overridden by a member inserted
by a Trait. The precedence order is that members from the current class
override Trait methods, which in turn override inherited methods.

> **Note**:
>
> As of PHP 8.5.0, traits are bound to a class before its parent class;
> previously they were bound after. This more closely reflects the copy and
> paste semantics of traits. In particular, when a trait and the parent class
> both declare a property or constant of the same name, the trait's
> definition now takes precedence over the inherited one, whereas earlier
> versions raised a fatal error about an incompatible composition. Method
> resolution is unaffected. See
> the migration
> guide for details.

**Example #2 Precedence Order Example**

An inherited method from a base class is overridden by the
method inserted into MyHelloWorld from the SayWorld Trait. The behavior is
the same for methods defined in the MyHelloWorld class. The precedence order
is that methods from the current class override Trait methods, which in
turn override methods from the base class.

```sql
<?php
class Base {
    public function sayHello() {
        echo 'Hello ';
    }
}

trait SayWorld {
    public function sayHello() {
        parent::sayHello();
        echo 'World!';
    }
}

class MyHelloWorld extends Base {
    use SayWorld;
}

$o = new MyHelloWorld();
$o->sayHello();
?>
```

The above example will output:

```sql
Hello World!
```

**Example #3 Alternate Precedence Order Example**

```sql
<?php
trait HelloWorld {
    public function sayHello() {
        echo 'Hello World!';
    }
}

class TheWorldIsNotEnough {
    use HelloWorld;
    public function sayHello() {
        echo 'Hello Universe!';
    }
}

$o = new TheWorldIsNotEnough();
$o->sayHello();
?>
```

The above example will output:

```sql
Hello Universe!
```

### Multiple Traits

Multiple Traits can be inserted into a class by listing them in the `use`
statement, separated by commas.

**Example #4 Multiple Traits Usage**

```sql
<?php
trait Hello {
    public function sayHello() {
        echo 'Hello ';
    }
}

trait World {
    public function sayWorld() {
        echo 'World';
    }
}

class MyHelloWorld {
    use Hello, World;
    public function sayExclamationMark() {
        echo '!';
    }
}

$o = new MyHelloWorld();
$o->sayHello();
$o->sayWorld();
$o->sayExclamationMark();
?>
```

The above example will output:

```sql
Hello World!
```

### Conflict Resolution

If two Traits insert a method with the same name, a fatal error is produced,
if the conflict is not explicitly resolved.

To resolve naming conflicts between Traits used in the same class,
the `insteadof` operator needs to be used to choose exactly
one of the conflicting methods.

Since this only allows one to exclude methods, the `as`
operator can be used to add an alias to one of the methods. Note the
`as` operator does not rename the method and it does not
affect any other method either.

**Example #5 Conflict Resolution**

In this example, Talker uses the traits A and B.
Since A and B have conflicting methods, it specifies that it uses
the variant of smallTalk from trait B, and the variant of bigTalk from
trait A.

The Aliased\_Talker makes use of the `as` operator
to be able to use B's bigTalk implementation under an additional alias
`talk`.

```sql
<?php
trait A {
    public function smallTalk() {
        echo 'a';
    }
    public function bigTalk() {
        echo 'A';
    }
}

trait B {
    public function smallTalk() {
        echo 'b';
    }
    public function bigTalk() {
        echo 'B';
    }
}

class Talker {
    use A, B {
        B::smallTalk insteadof A;
        A::bigTalk insteadof B;
    }
}

class Aliased_Talker {
    use A, B {
        B::smallTalk insteadof A;
        A::bigTalk insteadof B;
        B::bigTalk as talk;
    }
}
?>
```

### Changing Method Visibility

Using the `as` syntax, one can also adjust the visibility
of the method in the exhibiting class.

**Example #6 Changing Method Visibility**

```sql
<?php
trait HelloWorld {
    public function sayHello() {
        echo 'Hello World!';
    }
}

// Change visibility of sayHello
class MyClass1 {
    use HelloWorld { sayHello as protected; }
}

// Alias method with changed visibility
// sayHello visibility not changed
class MyClass2 {
    use HelloWorld { sayHello as private myPrivateHello; }
}
?>
```

### Traits Composed from Traits

Just as classes can make use of traits, so can other traits. By using one
or more traits in a trait definition, it can be composed partially or
entirely of the members defined in those other traits.

**Example #7 Traits Composed from Traits**

```sql
<?php
trait Hello {
    public function sayHello() {
        echo 'Hello ';
    }
}

trait World {
    public function sayWorld() {
        echo 'World!';
    }
}

trait HelloWorld {
    use Hello, World;
}

class MyHelloWorld {
    use HelloWorld;
}

$o = new MyHelloWorld();
$o->sayHello();
$o->sayWorld();
?>
```

The above example will output:

```sql
Hello World!
```

### Abstract Trait Members

Traits support the use of abstract methods in order to impose requirements
upon the exhibiting class. Public, protected, and private methods are supported.
Prior to PHP 8.0.0, only public and protected abstract methods were supported.

**Caution**

As of PHP 8.0.0, the signature of a concrete method must follow the
signature compatibility rules.
Previously, its signature might be different.

**Example #8 Express Requirements by Abstract Methods**

```sql
<?php
trait Hello {
    public function sayHelloWorld() {
        echo 'Hello'.$this->getWorld();
    }
    abstract public function getWorld();
}

class MyHelloWorld {
    private $world;
    use Hello;
    public function getWorld() {
        return $this->world;
    }
    public function setWorld($val) {
        $this->world = $val;
    }
}
?>
```

### Static Trait Members

Traits can define static variables, static methods and static properties.

> **Note**:
>
> As of PHP 8.1.0, calling a static method, or accessing a static property directly on a trait is deprecated.
> Static methods and properties should only be accessed on a class using the trait.

**Example #9 Static Variables**

```sql
<?php

trait Counter
{
    public function inc()
    {
        static $c = 0;
        $c = $c + 1;
        echo "$c\n";
    }
}

class C1
{
    use Counter;
}

class C2
{
    use Counter;
}

$o = new C1();
$o->inc();
$p = new C2();
$p->inc();

?>
```

The above example will output:

```sql
1
1
```

**Example #10 Static Methods**

```sql
<?php

trait StaticExample
{
    public static function doSomething()
    {
        return 'Doing something';
    }
}

class Example
{
    use StaticExample;
}

echo Example::doSomething();

?>
```

The above example will output:

```sql
Doing something
```

**Example #11 Static Properties**

**Caution**

Prior to PHP 8.3.0, static properties defined in a trait were shared
across all classes in the same inheritance hierarchy which used that trait.
As of PHP 8.3.0, if a child class uses a trait with a static property,
it will be considered distinct from the one defined in the parent class.

```sql
<?php

trait T
{
    public static $counter = 1;
}

class A
{
    use T;

    public static function incrementCounter()
    {
        static::$counter++;
    }
}

class B extends A
{
    use T;
}

A::incrementCounter();

echo A::$counter, "\n";
echo B::$counter, "\n";

?>
```

Output of the above example in PHP 8.3:

```sql
2
1
```

### Properties

Traits can also define properties.

**Example #12 Defining Properties**

```sql
<?php

trait PropertiesTrait
{
    public $x = 1;
}

class PropertiesExample
{
    use PropertiesTrait;
}

$example = new PropertiesExample();
$example->x;

?>
```

If a trait defines a property then a class can not define a property with
the same name unless it is compatible (same visibility and type,
readonly modifier, and initial value), otherwise a fatal error is issued.

**Example #13 Conflict Resolution**

```sql
<?php
trait PropertiesTrait {
    public $same = true;
    public $different1 = false;
    public bool $different2;
    public bool $different3;
}

class PropertiesExample {
    use PropertiesTrait;
    public $same = true;
    public $different1 = true; // Fatal error
    public string $different2; // Fatal error
    readonly protected bool $different3; // Fatal error
}
?>
```

### Constants

Traits can, as of PHP 8.2.0, also define constants.

**Example #14 Defining Constants**

```sql
<?php
trait ConstantsTrait {
    public const FLAG_MUTABLE = 1;
    final public const FLAG_IMMUTABLE = 5;
}

class ConstantsExample {
    use ConstantsTrait;
}

$example = new ConstantsExample;
echo $example::FLAG_MUTABLE;
?>
```

The above example will output:

```sql
1
```

If a trait defines a constant then a class can not define a constant with
the same name unless it is compatible (same visibility, initial value, and
finality), otherwise a fatal error is issued.

**Example #15 Conflict Resolution**

```sql
<?php
trait ConstantsTrait {
    public const FLAG_MUTABLE = 1;
    final public const FLAG_IMMUTABLE = 5;
}

class ConstantsExample {
    use ConstantsTrait;
    public const FLAG_IMMUTABLE = 5; // Fatal error
}
?>
```

### Final methods

As of PHP 8.3.0, the final
modifier can be applied using the `as` operator
to methods imported from traits. This can be used to prevent child classes
from overriding the method. However, the class that uses the trait can still
override the method.

**Example #16 Defining a method coming from a trait as `final`**

```sql
<?php

trait CommonTrait
{
    public function method()
    {
        echo 'Hello';
    }
}

class FinalExampleA
{
    use CommonTrait {
        CommonTrait::method as final; // The 'final' prevents child classes from overriding the method
    }
}

class FinalExampleB extends FinalExampleA
{
    public function method() {}
}

?>
```

The above example will output
something similar to:

```sql
Fatal error: Cannot override final method FinalExampleA::method() in ...
```

### Found A Problem?
