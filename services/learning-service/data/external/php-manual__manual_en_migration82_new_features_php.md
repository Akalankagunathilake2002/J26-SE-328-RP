<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/migration82.new-features.php -->
# PHP: New Features (manual en migration82 new features php)

### PHP Core

#### SensitiveParameter Attribute

Added the `#[\SensitiveParameter]` attribute to redact
sensitive data in backtraces.

#### error\_log\_mode INI directive

The error\_log\_mode INI directive has been added which allows setting
the permissions for the error log file.

#### Enumerations properties in constant expressions

It is now possible to fetch properties of
Enumerations
in constant expressions.

#### Type System Improvements

It is now possible to use null and false
as stand-alone types.

The true type has been added.

It is now possible to combine intersection and union types.
The type needs to be written in DNF.

#### Constants in Traits

It is now possible to define constants in traits.

#### Readonly Classes

Support for readonly
on classes has been added.

### cURL

Added the **`CURLINFO_EFFECTIVE_METHOD`** option,
which returns the effective HTTP method in the return value of
curl\_getinfo().

Exposed multiple new constants from libcurl 7.62 to 7.80.

Added the curl\_upkeep() function to perform any connection upkeep checks.

### DBA

The LMDB Driver now accepts the **`DBA_LMDB_USE_SUB_DIR`** or
**`DBA_LMDB_NO_SUB_DIR`** flags to determine if it should
create a subdirectory or not when creating a database file.

### OCI8

Added the oci8.prefetch\_lob\_size INI directive and
oci\_set\_prefetch\_lob() function to tune LOB query
performance by reducing the number of round-trips between PHP and
Oracle Databases when fetching LOBS.
This is usable with Oracle Database 12.2 or later.

### OpenSSL

Added AEAD support for the chacha20-poly1305 algorithm.

### ODBC

Added the odbc\_connection\_string\_is\_quoted(),
odbc\_connection\_string\_should\_quote(), and
odbc\_connection\_string\_quote() functions.
These are primarily used behind the scenes in the ODBC and PDO\_ODBC extensions,
but are exposed to userland for easier unit testing, and for user
applications and libraries to perform quoting themselves.

### PCRE

Added support for the `n` (NO\_AUTO\_CAPTURE) modifier,
which makes simple `(xyz)` groups non-capturing.
Only named groups like `(?xyz)` are capturing.
This only affects which groups are capturing, it is still possible to use
numbered subpattern references, and the matches array will still contain
numbered results.

### Random

This is a new extension which organises and consolidates existing
implementations related to random number generators.
New and better RNGs are available with scope issues eliminated.

### Found A Problem?
