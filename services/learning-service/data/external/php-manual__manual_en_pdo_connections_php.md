<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/pdo.connections.php -->
# PHP: Connections and Connection management

Connections are established by creating instances of the PDO base class.
It doesn't matter which driver you want to use; you always use the PDO
class name. The constructor accepts parameters for specifying the
database source (known as the DSN) and optionally for the username and
password (if any).

**Example #1 Connecting to MySQL**

```sql
<?php
$dbh = new PDO('mysql:host=localhost;dbname=test', $user, $pass);
?>
```

If there are any connection errors, a `PDOException`
object will be thrown. You may catch the exception if you want to handle
the error condition, or you may opt to leave it for an application
global exception handler that you set up via
set\_exception\_handler().

**Example #2 Handling connection errors**

```sql
<?php
try {
    $dbh = new PDO('mysql:host=localhost;dbname=test', $user, $pass);
} catch (PDOException $e) {
    // attempt to retry the connection after some timeout for example
}
```

**Warning**

Just like any other exception,
PDOException could be caught either explicitly, via
a `catch` statement, or implicitly via set\_exception\_handler().
Otherwise, the default behaviour of converting an uncaught exception to a
**`E_FATAL_ERROR`** will occur.
The fatal error will contain a backtrace that can leak connection details.
As such, the php.ini option
`display_errors`
should be set to `0` on a production server.

Upon successful connection to the database, an instance of the PDO class
is returned to your script. The connection remains active for the
lifetime of that PDO object. To close the connection, you need to
destroy the object by ensuring that all remaining references to it are
deleted—you do this by assigning **`null`** to the variable that holds the
object. If you don't do this explicitly, PHP will automatically close
the connection when your script ends.

> **Note**:
>
> If there are still other references to this PDO instance (such as from a
> PDOStatement instance, or from other variables referencing the same PDO
> instance), these have to be removed also (for instance, by assigning **`null`** to
> the variable that references the PDOStatement).

**Example #3 Closing a connection**

```sql
<?php
$dbh = new PDO('mysql:host=localhost;dbname=test', $user, $pass);
// use the connection here
$sth = $dbh->query('SELECT * FROM foo');

// and now we're done; close it
$sth = null;
$dbh = null;
?>
```

Many web applications will benefit from making persistent connections to
database servers. Persistent connections are not closed at the end of the
script, but are cached and re-used when another script requests a
connection using the same credentials. The persistent connection cache
allows you to avoid the overhead of establishing a new connection every
time a script needs to talk to a database, resulting in a faster web
application.

**Example #4 Persistent connections**

```sql
<?php
$dbh = new PDO('mysql:host=localhost;dbname=test', $user, $pass, array(
    PDO::ATTR_PERSISTENT => true
));
?>
```

The value of the **`PDO::ATTR_PERSISTENT`** option is converted
to bool (enable/disable persistent connections), unless it is a non-numeric
string, in which case it allows the use of multiple persistent connection pools.
This is useful if different connections use incompatible settings, for instance,
different values of **`PDO::MYSQL_ATTR_USE_BUFFERED_QUERY`**.

> **Note**:
>
> If you wish to use persistent connections, you must set
> **`PDO::ATTR_PERSISTENT`** in the array of driver options
> passed to the PDO constructor. If setting this attribute with
> PDO::setAttribute() after instantiation of the
> object, the driver will not use persistent connections.

**Warning**

PDO does not perform any cleanup of persistent connections. Temporary tables, locks, transactions and other stateful
changes may remain from previous usage of the connection, causing unexpected problems. See the
Persistent Database Connections section for more information.

> **Note**:
>
> If you're using the PDO ODBC driver and your ODBC libraries support ODBC
> Connection Pooling (unixODBC and Windows are two that do; there may be
> more), then it's recommended that you don't use persistent PDO
> connections, and instead leave the connection caching to the ODBC
> Connection Pooling layer. The ODBC Connection Pool is shared with other
> modules in the process; if PDO is told to cache the connection, then
> that connection would never be returned to the ODBC connection pool,
> resulting in additional connections being created to service those other
> modules.

### Found A Problem?
