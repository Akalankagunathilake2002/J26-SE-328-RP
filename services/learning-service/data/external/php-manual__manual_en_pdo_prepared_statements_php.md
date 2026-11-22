<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/pdo.prepared-statements.php -->
# PHP: Prepared statements and stored procedures

Many of the more mature databases support the concept of prepared
statements. What are they? They can be thought of as a kind of compiled
template for the SQL that an application wants to run, that can be customized
using variable parameters. Prepared statements offer two major benefits:

* The query only needs to be parsed (or prepared) once, but can be
  executed multiple times with the same or different parameters. When the
  query is prepared, the database will analyze, compile and optimize its
  plan for executing the query. For complex queries this process can take
  up enough time that it will noticeably slow down an application if there
  is a need to repeat the same query many times with different parameters. By
  using a prepared statement the application avoids repeating the
  analyze/compile/optimize cycle. This means that prepared statements use fewer
  resources and thus run faster.
* The parameters to prepared statements don't need to be quoted; the
  driver automatically handles this. If an application exclusively uses
  prepared statements, the developer can be sure that no SQL injection will
  occur (however, if other portions of the query are being built up with
  unescaped input, SQL injection is still possible).

Prepared statements are so useful that they are the only feature that PDO
will emulate for drivers that don't support them. This ensures that an
application will be able to use the same data access paradigm regardless of
the capabilities of the database.

**Example #1 Repeated inserts using prepared statements**

This example performs an INSERT query by substituting a `name`
and a `value` for the named placeholders.

```sql
<?php
$stmt = $dbh->prepare("INSERT INTO REGISTRY (name, value) VALUES (:name, :value)");
$stmt->bindParam(':name', $name);
$stmt->bindParam(':value', $value);

// insert one row
$name = 'one';
$value = 1;
$stmt->execute();

// insert another row with different values
$name = 'two';
$value = 2;
$stmt->execute();
?>
```

**Example #2 Repeated inserts using prepared statements**

This example performs an INSERT query by substituting a `name`
and a `value` for the positional `?` placeholders.

```sql
<?php
$stmt = $dbh->prepare("INSERT INTO REGISTRY (name, value) VALUES (?, ?)");
$stmt->bindParam(1, $name);
$stmt->bindParam(2, $value);

// insert one row
$name = 'one';
$value = 1;
$stmt->execute();

// insert another row with different values
$name = 'two';
$value = 2;
$stmt->execute();
?>
```

**Example #3 Fetching data using prepared statements**

This example fetches data based on a key value supplied by a form.
The user input is automatically quoted, so there is no risk of a
SQL injection attack.

```sql
<?php
$stmt = $dbh->prepare("SELECT * FROM REGISTRY where name = ?");
$stmt->execute([$_GET['name']]);
foreach ($stmt as $row) {
  print_r($row);
}
?>
```

**Example #4 Calling a stored procedure with an output parameter**

If the database driver supports it, an application may also bind parameters for
output as well as input. Output parameters are typically used to retrieve
values from stored procedures. Output parameters are slightly more complex
to use than input parameters, in that a developer must know how large a given
parameter might be when they bind it. If the value turns out to be larger
than the size they suggested, an error is raised.

```sql
<?php
$stmt = $dbh->prepare("CALL sp_returns_string(?)");
$stmt->bindParam(1, $return_value, PDO::PARAM_STR, 4000);

// call the stored procedure
$stmt->execute();

print "procedure returned $return_value\n";
?>
```

**Example #5 Calling a stored procedure with an input/output parameter**

Developers may also specify parameters that hold values both input and output;
the syntax is similar to output parameters. In this next example, the
string 'hello' is passed into the stored procedure, and when it returns,
hello is replaced with the return value of the procedure.

```sql
<?php
$stmt = $dbh->prepare("CALL sp_takes_string_returns_string(?)");
$value = 'hello';
$stmt->bindParam(1, $value, PDO::PARAM_STR|PDO::PARAM_INPUT_OUTPUT, 4000);

// call the stored procedure
$stmt->execute();

print "procedure returned $value\n";
?>
```

**Example #6 Invalid use of placeholder**

```sql
<?php
$stmt = $dbh->prepare("SELECT * FROM REGISTRY where name LIKE '%?%'");
$stmt->execute([$_GET['name']]);

// placeholder must be used in the place of the whole value
$stmt = $dbh->prepare("SELECT * FROM REGISTRY where name LIKE ?");
$stmt->execute(["%$_GET[name]%"]);
?>
```

### Found A Problem?
