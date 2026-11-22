<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/migration80.new-features.php -->
# PHP: New Features

### PHP Core

#### Named Arguments

Support for Named Arguments has been added.

#### Attributes

Support for Attributes has been added.

#### Constructor Property Promotion

Support for constructor property promotion (declaring properties in the constructor signature)
has been added.

#### Union Types

Support for union types has been added.

#### Match Expression

Support for `match` expressions has been added.

#### Nullsafe Operator

Support for the nullsafe operator (`?->`) has been added.

#### Other new Features

* The WeakMap class has been added.
* The ValueError class has been added.
* Any number of function parameters may now be replaced by a variadic argument, as long as the
  types are compatible. For example, the following code is now allowed:

  ```sql
  <?php
  class A {
       public function method(int $many, string $parameters, $here) {}
  }
  class B extends A {
       public function method(...$everything) {}
  }
  ?>
  ```
* static (as in "late static binding") can now be used as a return type:

  ```sql
  <?php
  class Test {
       public function create(): static {
            return new static();
       }
  }
  ?>
  ```
* It is now possible to fetch the class name of an object using
  `$object::class`. The result is the same as `get_class($object)`.
* `new` and `instanceof` can now be used with arbitrary expressions,
  using `new (expression)(...$args)` and `$obj instanceof (expression)`.
* Some consistency fixes to variable syntax have been applied, for example writing
  `Foo::BAR::$baz` is now allowed.
* Added Stringable interface, which is automatically implemented if
  a class defines a \_\_toString() method.
* Traits can now define abstract private methods.
  Such methods must be implemented by the class using the trait.
* `throw` can now be used as an expression.
  That allows usages like:

  ```sql
  <?php
  $fn = fn() => throw new Exception('Exception in arrow function');
  $user = $session->user ?? throw new Exception('Must have user');
  ```
* An optional trailing comma is now allowed in parameter lists.

  ```sql
  <?php
  function functionWithLongSignature(
      Type1 $parameter1,
      Type2 $parameter2, // <-- This comma is now allowed.
  ) {
  }
  ```
* It is now possible to write `catch (Exception)` to catch an exception without storing
  it in a variable.
* Support for mixed type has been added.
* Private methods declared on a parent class no longer enforce any inheritance rules on the methods
  of a child class (with the exception of final private constructors).
  The following example illustrates which restrictions have been removed:

  ```sql
  <?php
  class ParentClass {
      private function method1() {}
      private function method2() {}
      private static function method3() {}
      // Throws a warning, as "final" no longer has an effect:
      private final function method4() {}
  }
  class ChildClass extends ParentClass {
      // All of the following are now allowed, even though the modifiers aren't
      // the same as for the private methods in the parent class.
      public abstract function method1() {}
      public static function method2() {}
      public function method3() {}
      public function method4() {}
  }
  ?>
  ```
* get\_resource\_id() has been added, which returns the same value as
  `(int) $resource`. It provides the same functionality under a clearer API.
* The InternalIterator has been added.

### Date and Time

* DateTime::createFromInterface() and
  DateTimeImmutable::createFromInterface() have been added.
* The DateTime format specifier `p` has been added, which is the same as
  `P` but returns `Z` rather than `+00:00`
  for UTC.

### DOM

DOMParentNode and DOMChildNode with
new traversal and manipulation APIs have been added.

### Filter

**`FILTER_VALIDATE_BOOL`** has been added as an alias for
**`FILTER_VALIDATE_BOOLEAN`**. The new name is preferred, as it uses the canonical
type name.

### Enchant

enchant\_dict\_add(), enchant\_dict\_is\_added(), and
**`LIBENCHANT_VERSION`** have been added.

### FPM

Added a new option `pm.status_listen` that allows getting the status from
different endpoint (e.g. port or UDS file) which is useful for getting the status when all
children are busy with serving long running requests.

### Hash

HashContext objects can now be serialized.

### Internationalization Functions

The **`IntlDateFormatter::RELATIVE_FULL`**,
**`IntlDateFormatter::RELATIVE_LONG`**,
**`IntlDateFormatter::RELATIVE_MEDIUM`**, and
**`IntlDateFormatter::RELATIVE_SHORT`**
constants have been added.

### LDAP

ldap\_count\_references() has been added, which returns the number
of reference messages in a search result.

### OPcache

If the opcache.record\_warnings ini setting is
enabled, OPcache will record compile-time warnings and replay them on the next include, even if
it is served from cache.

### OpenSSL

Added Cryptographic Message Syntax (CMS) (» RFC 5652)
support composed of functions for encryption, decryption, signing, verifying and reading. The API
is similar to the API for PKCS #7 functions with an addition of new encoding constants:
**`OPENSSL_ENCODING_DER`**, **`OPENSSL_ENCODING_SMIME`**
and **`OPENSSL_ENCODING_PEM`**:

* openssl\_cms\_encrypt() encrypts the message in the file with the certificates
  and outputs the result to the supplied file.
* openssl\_cms\_decrypt() that decrypts the S/MIME message in the file and outputs
  the results to the supplied file.
* openssl\_cms\_read() that exports the CMS file to an array
  of PEM certificates.
* openssl\_cms\_sign() that signs the MIME message in the file with a cert and key
  and output the result to the supplied file.
* openssl\_cms\_verify() that verifies that the data block is intact, the signer
  is who they say they are, and returns the certs of the signers.

### Regular Expressions (Perl-Compatible)

preg\_last\_error\_msg() has been added, which returns a human-readable message for the last
PCRE error. It complements preg\_last\_error(), which returns an integer enum value
instead.

### Reflection

* The following methods can now return information about default values of
  parameters of internal functions:

  + ReflectionParameter::isDefaultValueAvailable()
  + ReflectionParameter::getDefaultValue()
  + ReflectionParameter::isDefaultValueConstant()
  + ReflectionParameter::getDefaultValueConstantName()

### SQLite3

SQLite3::setAuthorizer() and respective class constants have been added
to set a userland callback that will be used to authorize or not an action on the database.

### Standard Library

* str\_contains(), str\_starts\_with() and
  str\_ends\_with() have been added, which check whether `haystack` contains,
  starts with or ends with `needle`, respectively.
* fdiv() has been added, which performs a floating-point division under IEEE 754 semantics.
  Division by zero is considered well-defined and will return one of `Inf`,
  `-Inf` or `NaN`.
* get\_debug\_type() has been added, which returns a type useful for error messages. Unlike
  gettype(), it uses canonical type names, returns class names for objects, and
  indicates the resource type for resources.
* printf() and friends now support the `%h` and
  `%H` format specifiers. These are the same as `%g` and
  `%G`, but always use `"."` as the decimal separator, rather
  than determining it through the **`LC_NUMERIC`** locale.
* printf() and friends now support using `"*"` as width or
  precision, in which case the width/precision is passed as an argument to printf. This also allows
  using precision `-1` with `%g`, `%G`,
  `%h` and `%H`. For example, the following code can be used to
  reproduce PHP's default floating point formatting:

  ```sql
  <?php
  printf("%.*H", (int) ini_get("precision"), $float);
  printf("%.*H", (int) ini_get("serialize_precision"), $float);
  ?>
  ```
* proc\_open() now supports pseudo-terminal (PTY) descriptors. The following
  attaches `stdin`, `stdout` and `stderr` to the
  same PTY:

  ```sql
  <?php
  $proc = proc_open($command, [['pty'], ['pty'], ['pty']], $pipes);
  ?>
  ```
* proc\_open() now supports socket pair descriptors. The following attaches a
  distinct socket pair to `stdin`, `stdout` and
  `stderr`:

  ```sql
  <?php
  $proc = proc_open($command, [['socket'], ['socket'], ['socket']], $pipes);
  ?>
  ```

  Unlike pipes, sockets do not suffer from blocking I/O issues on Windows. However, not all
  programs may work correctly with stdio sockets.
* Sorting functions are now stable, which means that equal-comparing elements will retain their
  original order.
* array\_diff(), array\_intersect() and their variations can
  now be used with a single array as argument. This means that usages like the following are now
  possible:

  ```sql
  <?php
  // OK even if $excludes is empty:
  array_diff($array, ...$excludes);
  // OK even if $arrays only contains a single array:
  array_intersect(...$arrays);
  ?>
  ```
* The `flag` parameter of ob\_implicit\_flush() was changed
  to accept a bool rather than an int.

### Tokenizer

PhpToken adds an object-based interface to the tokenizer. It provides a
more uniform and ergonomic representation, while being more memory efficient and faster.

### Zip

* The Zip extension has been updated to version 1.19.1.
* New ZipArchive::setMtimeName() and
  ZipArchive::setMtimeIndex() to set the modification time of an entry.
* New ZipArchive::registerProgressCallback() to provide updates during archive close.
* New ZipArchive::registerCancelCallback() to allow cancellation during archive
  close.
* New ZipArchive::replaceFile() to replace an entry content.
* New ZipArchive::isCompressionMethodSupported() to check optional compression
  features.
* New ZipArchive::isEncryptionMethodSupported() to check optional encryption
  features.
* The ZipArchive::lastId property to get the index value of
  the last added entry has been added.
* Errors can now be checked after an archive has been closed using the
  ZipArchive::status and
  ZipArchive::statusSys properties, or the
  ZipArchive::getStatusString() method.
* The `'remove_path'` option of ZipArchive::addGlob() and
  ZipArchive::addPattern() is now treated as an arbitrary string prefix (for
  consistency with the `'add_path'` option), whereas formerly it was treated as a
  directory name.
* Optional compression / encryption features are now listed in phpinfo.

### Found A Problem?
