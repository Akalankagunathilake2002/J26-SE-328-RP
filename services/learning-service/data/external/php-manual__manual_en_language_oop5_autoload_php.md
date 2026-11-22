<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/language.oop5.autoload.php -->
# PHP: Autoloading Classes

Many developers writing object-oriented applications create
one PHP source file per class definition. One of the biggest
annoyances is having to write a long list of needed includes
at the beginning of each script (one for each class).

The spl\_autoload\_register() function registers any number of
autoloaders, enabling classes and interfaces to be automatically loaded
if they are currently not defined. By registering autoloaders, PHP is given
a last chance to load the class or interface before it fails with an error.

Any class-like construct may be autoloaded the same way. That includes classes,
interfaces, traits, and enumerations.

**Caution**

Prior to PHP 8.0.0, it was possible to use \_\_autoload()
to autoload classes and interfaces. However, it is a less flexible
alternative to spl\_autoload\_register() and
\_\_autoload() is deprecated as of PHP 7.2.0, and removed
as of PHP 8.0.0.

> **Note**:
>
> spl\_autoload\_register() may be called multiple times in order
> to register multiple autoloaders. Throwing an exception from an autoload function,
> however, will interrupt that process and not allow further autoload functions to
> run. For that reason, throwing exceptions from an autoload function is strongly
> discouraged.

**Example #1 Autoload example**

This example attempts to load the classes `MyClass1`
and `MyClass2` from the files MyClass1.php
and MyClass2.php respectively.

```sql
<?php
spl_autoload_register(function ($class_name) {
    include $class_name . '.php';
});

$obj  = new MyClass1();
$obj2 = new MyClass2();
?>
```

**Example #2 Autoload other example**

This example attempts to load the interface `ITest`.

```sql
<?php

spl_autoload_register(function ($name) {
    var_dump($name);
});

class Foo implements ITest {
}

/*
string(5) "ITest"

Fatal error: Interface 'ITest' not found in ...
*/
?>
```

**Example #3 Using Composer's autoloader**

» Composer generates a `vendor/autoload.php`
which is set up to automatically load packages that are being managed
by Composer. By including this file, those packages can be used without
any additional work.

```sql
<?php
require __DIR__ . '/vendor/autoload.php';

$uuid = Ramsey\Uuid\Uuid::uuid7();

echo "Generated new UUID -> ", $uuid->toString(), "\n";
?>
```

### See Also

* unserialize()
* unserialize\_callback\_func
* unserialize\_max\_depth
* spl\_autoload\_register()
* spl\_autoload()
* \_\_autoload()

### Found A Problem?
