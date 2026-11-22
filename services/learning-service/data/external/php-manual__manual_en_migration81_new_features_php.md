<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/migration81.new-features.php -->
# PHP: New Features (manual en migration81 new features php)

### PHP Core

#### Integer Octal Literal Prefix

Octal integers can now use an explicit
`0o`/`0O`
prefix in integer literals,
similarly to binary and hexadecimal integer literals.

```sql
<?php
014;  // Non-prefix octal literal
0o14; // Prefixed octal literal
?>
```

#### Array Unpacking with String Keys

Added support for array unpacking with strings keys.

```sql
<?php
$arr1 = [1, 'a' => 'b'];
$arr2 = [...$arr1, 'c' => 'd']; //[1, 'a' => 'b', 'c' => 'd']
?>
```

#### Named Argument After Argument Unpacking

It is now possible to specify named arguments after an argument unpack.
e.g.
foo(...$args, named: $arg).

#### full-path Key for File Uploads

File uploads now provide an additional `full_path` key,
which contains the full path (rather than just the basename) of the uploaded file.
This is intended for use in conjunction with "upload webkitdirectory".

#### Enumerations

Support for Enumerations has been added.

#### Fibers

Support for Fibers has been added.

#### First Class Callable Syntax

Closures for callables can now be created using the syntax `myFunc(...)`,
which is identical to `Closure::fromCallable('myFunc')`.

> **Note**:
>
> The `...` is part of the syntax, and not an omission.

#### Intersection Types

Support for intersection types has been added.

**Caution**

Intersection types cannot be used together with
union types

#### Never type

A new return only type never has been added.
This indicates that a function either exit(),
throws an exception, or doesn't terminate.

#### `new` in Initializers

It is now possible to use `new ClassName()` expressions as the
default value of a parameter, static variable, global constant initializers,
and as attribute arguments.
Objects can also be passed to define() now.

#### Readonly properties

Support for readonly has been added.

#### Final class constants

Added support for the final modifier for class constants.
Also, interface constants become overridable by default.

### CURL

Added the **`CURLOPT_DOH_URL`** option.

Added options for blob certificate when libcurl >= 7.71.0:

* **`CURLOPT_ISSUERCERT_BLOB`**
* **`CURLOPT_PROXY_ISSUERCERT`**
* **`CURLOPT_PROXY_ISSUERCERT_BLOB`**
* **`CURLOPT_PROXY_SSLCERT_BLOB`**
* **`CURLOPT_PROXY_SSLKEY_BLOB`**
* **`CURLOPT_SSLCERT_BLOB`**
* **`CURLOPT_SSLKEY_BLOB`**

Added CURLStringFile, which can be used to post
a file from a string rather than a file:

```sql
<?php
$file = new CURLStringFile($data, 'filename.txt', 'text/plain');
curl_setopt($curl, CURLOPT_POSTFIELDS, ['file' => $file]);
?>
```

### FPM

Added openmetrics status format. It can be used by Prometheus to fetch FPM
metrics.

Added new pool option for the dynamic process manager called
`pm.max_spawn_rate`. It allows to start a number of children
at a faster rate when dynamic pm is selected.
The default value is `32` which was the previous
hard coded value.

### GD

Avif support is now available through
imagecreatefromavif() and
imageavif(),
if libgd has been built with Avif support.

### Hash

The following functions hash(),
hash\_file(), and hash\_init()
now support an additional optional `options`
argument, which can be used to pass algorithm specific data.

#### MurmurHash3

Added support for `MurmurHash3` with streaming
support. The following variants are implemented:

* murmur3a, 32-bit hash
* murmur3c, 128-bit hash for x86
* murmur3f, 128-bit hash for x64

The initial hash state can be passed through the `seed`
key in the `options` array, for example:

```sql
<?php
$h = hash("murmur3f", $data, options: ["seed" => 42]);
echo $h, "\n";
?>
```

A valid seed value is within the range from `0`
to the platform defined **`UINT_MAX`**, usually
`4294967295`.

#### xxHash

Added support for `xxHash`.
The following variants are implemented:

* xxh32, 32-bit hash
* xxh64, 64-bit hash
* xxh3, 64-bit hash
* xxh128, 128-bit hash

The initial hash state can be passed through the `seed`
key in the `options` array, for example:

```sql
<?php
$h = hash("xxh3", $data, options: ["seed" => 42]);
echo $h, "\n";
?>
```

Secret usage is supported through passing the `secret`
key in the `options` array, too:

```sql
<?php
$h = hash("xxh3", $data, options: ["secret" => "at least 136 bytes long secret here"]);
echo $h, "\n";
?>
```

The quality of the custom secret is crucial for the quality of the resulting hash.
It is highly recommended for the secret to use the best possible entropy.

### MySQLi

#### New INI directive `mysqli.local_infile_directory`

The mysqli.local\_infile\_directory
INI directive has been added, which can be used to specify a directory from
which files are allowed to be loaded. It is only meaningful if
mysqli.allow\_local\_infile
is not enabled, as all directories are allowed in that case.

#### Binding parameters in execute

It is now possible to bind parameters by passing them as an array to
mysqli\_stmt::execute(). All values will be bound as
strings. Only list arrays are allowed. This new feature is not available
when MySQLi is compiled with libmysqlclient.

```sql
<?php
$stmt = $mysqli->prepare('INSERT INTO users(id, name) VALUES(?,?)');
$stmt->execute([1, $username]);
?>
```

#### New method mysqli\_result::fetch\_column()

mysqli\_result::fetch\_column()
has been added to allow fetching a single scalar value from the result set.
The new method accepts an optional 0-based `column`
parameter of type int specifying which column to fetch from.

```sql
<?php
$result = $mysqli->query('SELECT username FROM users WHERE id = 123');
echo $result->fetch_column();
?>
```

### PDO

The **`PDO::MYSQL_ATTR_LOCAL_INFILE_DIRECTORY`** attribute
has been added, which can be used to specify a directory from which files
are allowed to be loaded.
It is only meaningful if **`PDO::MYSQL_ATTR_LOCAL_INFILE`**
is not enabled, as all directories are allowed in that case.

### PDO\_SQLite

SQLite's `"file:"` DSN syntax is now supported,
which allows specifying additional flags.
This feature is not available if open\_basedir is set.

```sql
<?php
new PDO('sqlite:file:path/to/sqlite.db?mode=ro')
?>
```

### POSIX

Added **`POSIX_RLIMIT_KQUEUES`** and **`POSIX_RLIMIT_NPTS`**.
These rlimits are only available on FreeBSD.

### Standard

fputcsv() now accepts a new
`eol` argument which allows to define a custom
End of Line sequence, the default remains the same and is `"\n"`.

### SPL

SplFileObject::fputcsv() now accepts a new
`eol` argument which allows to define a custom
End of Line sequence, the default remains the same and is `"\n"`.

### Found A Problem?
