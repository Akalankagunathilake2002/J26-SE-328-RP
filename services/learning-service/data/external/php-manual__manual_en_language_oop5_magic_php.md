<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/language.oop5.magic.php -->
# PHP: Magic Methods

Magic methods are special methods which override PHP's default action
when certain actions are performed on an object.

**Caution**

All method names starting with `__` are reserved by PHP.
Therefore, it is not recommended to use such method names unless overriding
PHP's behavior.

The following method names are considered magical:
\_\_construct(),
\_\_destruct(),
\_\_call(),
\_\_callStatic(),
\_\_get(),
\_\_set(),
\_\_isset(),
\_\_unset(),
\_\_serialize(),
\_\_unserialize(),
\_\_sleep(),
\_\_wakeup(),
\_\_toString(),
\_\_invoke(),
\_\_set\_state(),
\_\_clone(), and
\_\_debugInfo().

**Warning**

All magic methods, with the exception of
\_\_construct(),
\_\_destruct(), and
\_\_clone(),
*must* be declared as `public`,
otherwise an **`E_WARNING`** is emitted.
Prior to PHP 8.0.0, no diagnostic was emitted for the magic methods
\_\_sleep(),
\_\_wakeup(),
\_\_serialize(),
\_\_unserialize(), and
\_\_set\_state().

**Warning**

If type declarations are used in the definition of a magic method, they
must be identical to the signature described in this document.
Otherwise, a fatal error is emitted.
Prior to PHP 8.0.0, no diagnostic was emitted.
However, \_\_construct() and
\_\_destruct() must not declare a return type;
otherwise a fatal error is emitted.

### \_\_serialize() and \_\_unserialize()

public function **\_\_serialize**(): array

public function **\_\_unserialize**(array `$data`): void

serialize() checks if the class has a function with
the magic name \_\_serialize(). If so, that function is
executed prior to any serialization. It must construct and return an associative array of key/value pairs
that represent the serialized form of the object. If no array is returned a TypeError
will be thrown.

> **Note**:
>
> If both \_\_serialize() and \_\_sleep()
> are defined in the same object, only \_\_serialize() will be called.
> \_\_sleep() will be ignored. If the object implements the Serializable
> interface, the interface's `serialize()` method will be ignored and \_\_serialize()
> used instead.

The intended use of \_\_serialize() is to define a serialization-friendly
arbitrary representation of the object. Elements of the array may correspond to properties of the object but
that is not required.

Conversely, unserialize() checks for the
presence of a function with the magic name
\_\_unserialize(). If present, this function will be passed the
restored array that was returned from \_\_serialize(). It may
then restore the properties of the object from that array as appropriate.

> **Note**:
>
> If both \_\_unserialize() and \_\_wakeup()
> are defined in the same object, only \_\_unserialize() will be called.
> \_\_wakeup() will be ignored.

> **Note**:
>
> This feature is available as of PHP 7.4.0.

**Example #1 Serialize and unserialize**

```sql
<?php
class Connection
{
    protected $link;
    private $dsn, $username, $password;

    public function __construct($dsn, $username, $password)
    {
        $this->dsn = $dsn;
        $this->username = $username;
        $this->password = $password;
        $this->connect();
    }

    private function connect()
    {
        $this->link = new PDO($this->dsn, $this->username, $this->password);
    }

    public function __serialize(): array
    {
        return [
          'dsn' => $this->dsn,
          'user' => $this->username,
          'pass' => $this->password,
        ];
    }

    public function __unserialize(array $data): void
    {
        $this->dsn = $data['dsn'];
        $this->username = $data['user'];
        $this->password = $data['pass'];

        $this->connect();
    }
}?>
```

### \_\_sleep() and \_\_wakeup()

**Warning**

This serialization mechanism is soft-deprecated as of PHP 8.5.0.
It is maintained for backward compatibility.
However, new and existing code should be migrated to use the
\_\_serialize() and
\_\_unserialize()
magic methods instead.

public function **\_\_sleep**(): array

public function **\_\_wakeup**(): void

serialize() checks if the class has a function with
the magic name \_\_sleep(). If so, that function is
executed prior to any serialization. It can clean up the object
and is supposed to return an array with the names of all variables
of that object that should be serialized.
If the method doesn't return anything then **`null`** is serialized and
**`E_NOTICE`** is issued.

> **Note**:
>
> It is not possible for \_\_sleep() to return names of
> private properties in parent classes. Doing this will result in an
> **`E_NOTICE`** level error.
> Use \_\_serialize() instead.

> **Note**:
>
> As of PHP 8.0.0, returning a value which is not an array from \_\_sleep() generates a warning. Previously, it generated a notice.

The intended use of \_\_sleep() is to commit pending
data or perform similar cleanup tasks. Also, the function is
useful if a very large object doesn't need to be saved completely.

Conversely, unserialize() checks for the
presence of a function with the magic name
\_\_wakeup(). If present, this function can
reconstruct any resources that the object may have.

The intended use of \_\_wakeup() is to
reestablish any database connections that may have been lost
during serialization and perform other reinitialization
tasks.

**Example #2 Sleep and wakeup**

```sql
<?php
class Connection
{
    protected $link;
    private $dsn, $username, $password;

    public function __construct($dsn, $username, $password)
    {
        $this->dsn = $dsn;
        $this->username = $username;
        $this->password = $password;
        $this->connect();
    }

    private function connect()
    {
        $this->link = new PDO($this->dsn, $this->username, $this->password);
    }

    public function __sleep()
    {
        return array('dsn', 'username', 'password');
    }

    public function __wakeup()
    {
        $this->connect();
    }
}?>
```

### \_\_toString()

public function **\_\_toString**(): string

The \_\_toString() method allows a class to decide
how it will react when it is treated like a string. For example,
what `echo $obj;` will print.

**Warning**

As of PHP 8.0.0, the return value follows standard PHP type semantics,
meaning it will be coerced into a string if possible and if
strict typing
is disabled.

A Stringable object will
*not* be accepted by a string type declaration if
strict typing
is enabled. If such behaviour is wanted the type declaration must accept
Stringable and string via a union type.

As of PHP 8.0.0, any class that contains a \_\_toString()
method will also implicitly implement the Stringable interface, and will
thus pass type checks for that interface. Explicitly implementing the interface anyway is
recommended.

In PHP 7.4, the returned value *must* be a
string, otherwise an Error is thrown.

Prior to PHP 7.4.0, the returned value *must* be a
string, otherwise a fatal **`E_RECOVERABLE_ERROR`**
is emitted.

**Warning**

It was not possible to throw an exception from within a
\_\_toString()
method prior to PHP 7.4.0. Doing so will result in a fatal error.

**Example #3 Simple example**

```sql
<?php
// Declare a simple class
class TestClass
{
    public $foo;

    public function __construct($foo)
    {
        $this->foo = $foo;
    }

    public function __toString()
    {
        return $this->foo;
    }
}

$class = new TestClass('Hello');
echo $class;
?>
```

The above example will output:

```sql
Hello
```

### \_\_invoke()

function **\_\_invoke**( `...$values`): mixed

The \_\_invoke() method is called when a script tries to
call an object as a function.

**Example #4 Using \_\_invoke()**

```sql
<?php
class CallableClass
{
    public function __invoke($x)
    {
        var_dump($x);
    }
}
$obj = new CallableClass;
$obj(5);
var_dump(is_callable($obj));
?>
```

The above example will output:

```sql
int(5)
bool(true)
```

**Example #5 Using \_\_invoke()**

```sql
<?php
class Sort
{
    private $key;

    public function __construct(string $key)
    {
        $this->key = $key;
    }

    public function __invoke(array $a, array $b): int
    {
        return $a[$this->key]  $b[$this->key];
    }
}

$customers = [
    ['id' => 1, 'first_name' => 'John', 'last_name' => 'Do'],
    ['id' => 3, 'first_name' => 'Alice', 'last_name' => 'Gustav'],
    ['id' => 2, 'first_name' => 'Bob', 'last_name' => 'Filipe']
];

// sort customers by first name
usort($customers, new Sort('first_name'));
print_r($customers);

// sort customers by last name
usort($customers, new Sort('last_name'));
print_r($customers);
?>
```

The above example will output:

```sql
Array
(
    [0] => Array
        (
            [id] => 3
            [first_name] => Alice
            [last_name] => Gustav
        )

    [1] => Array
        (
            [id] => 2
            [first_name] => Bob
            [last_name] => Filipe
        )

    [2] => Array
        (
            [id] => 1
            [first_name] => John
            [last_name] => Do
        )

)
Array
(
    [0] => Array
        (
            [id] => 1
            [first_name] => John
            [last_name] => Do
        )

    [1] => Array
        (
            [id] => 2
            [first_name] => Bob
            [last_name] => Filipe
        )

    [2] => Array
        (
            [id] => 3
            [first_name] => Alice
            [last_name] => Gustav
        )

)
```

### \_\_set\_state()

static function **\_\_set\_state**(array `$properties`): object

This static method is called
for classes exported by var\_export().

The only parameter of this method is an array containing exported
properties in the form `['property' => value, ...]`.

**Example #6 Using \_\_set\_state()**

```sql
<?php

class A
{
    public $var1;
    public $var2;

    public static function __set_state($an_array)
    {
        $obj = new A;
        $obj->var1 = $an_array['var1'];
        $obj->var2 = $an_array['var2'];
        return $obj;
    }
}

$a = new A;
$a->var1 = 5;
$a->var2 = 'foo';

$b = var_export($a, true);
var_dump($b);
eval('$c = ' . $b . ';');
var_dump($c);
?>
```

The above example will output:

```sql
string(60) "A::__set_state(array(
   'var1' => 5,
   'var2' => 'foo',
))"
object(A)#2 (2) {
  ["var1"]=>
  int(5)
  ["var2"]=>
  string(3) "foo"
}
```

> **Note**:
>
> When exporting an object, var\_export() does not check
> whether \_\_set\_state() is
> implemented by the object's class, so re-importing objects will result in an Error exception,
> if \_\_set\_state() is not implemented. Particularly, this affects some
> internal classes.
>
> It is the responsibility of the programmer to verify that only objects
> whose class implements **\_\_set\_state()** will
> be re-imported.

### \_\_debugInfo()

function **\_\_debugInfo**(): array

This method is called by var\_dump() when dumping an
object to get the properties that should be shown. If the method isn't
defined on an object, then all public, protected and private properties
will be shown.

As of PHP 8.5.0, returning **`null`** from \_\_debugInfo()
is deprecated. Return an empty array instead.

**Example #7 Using \_\_debugInfo()**

```sql
<?php
class C {
    private $prop;

    public function __construct($val) {
        $this->prop = $val;
    }

    public function __debugInfo() {
        return [
            'propSquared' => $this->prop ** 2,
        ];
    }
}

var_dump(new C(42));
?>
```

The above example will output:

```sql
object(C)#1 (1) {
  ["propSquared"]=>
  int(1764)
}
```

### Found A Problem?
