<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/pdo.transactions.php -->
# PHP: Transactions and auto-commit

Now that you're connected via PDO, you must understand how PDO
manages transactions before you start issuing queries. If you've never
encountered transactions before, they offer 4 major features: Atomicity,
Consistency, Isolation and Durability (ACID). In layman's terms, any work
carried out in a transaction, even if it is carried out in stages, is
guaranteed to be applied to the database safely, and without interference
from other connections, when it is committed. Transactional work can also
be automatically undone at your request (provided you haven't already
committed it), which makes error handling in your scripts easier.

Transactions are typically implemented by "saving-up" your batch of
changes to be applied all at once; this has the nice side effect of
drastically improving the efficiency of those updates. In other words,
transactions can make your scripts faster and potentially more robust
(you still need to use them correctly to reap that benefit).

Unfortunately, not every database supports transactions, so PDO needs to
run in what is known as "auto-commit" mode when you first open the
connection. Auto-commit mode means that every query that you run has its
own implicit transaction, if the database supports it, or no transaction
if the database doesn't support transactions. If you need a transaction,
you must use the PDO::beginTransaction() method to
initiate one. If the underlying driver does not support transactions, a
PDOException will be thrown (regardless of your error handling settings:
this is always a serious error condition). Once you are in a transaction,
you may use PDO::commit() or
PDO::rollBack() to finish it, depending on the success
of the code you run during the transaction.

**Warning**

PDO only checks for transaction capabilities on driver level. If certain
runtime conditions mean that transactions are unavailable,
PDO::beginTransaction() will still return **`true`**
without error if the database server accepts the request to start a
transaction.

An example of this would be trying to use transactions on MyISAM tables on
a MySQL database.

**Warning**

*Implicit Commits with DDL Statements:*
Some databases automatically issue an
implicit `COMMIT` when a database definition language (DDL)
statement, such as `DROP TABLE` or `CREATE TABLE`,
is executed within a transaction. This means that any prior changes made within the
same transaction will be *automatically committed* and cannot
be rolled back.

`MySQL` and `Oracle` are example databases that
exhibit this behavior.

**Example #1 Implicit Commit Example**

```sql
<?php
$pdo->beginTransaction();
$pdo->exec("INSERT INTO users (name) VALUES ('Rasmus')");
$pdo->exec("CREATE TABLE test (id INT PRIMARY KEY)"); // Implicit COMMIT occurs here
$pdo->rollBack(); // This will NOT undo the INSERT/CREATE for MySQL or Oracle
?>
```

*Best Practice:* Avoid executing DDL statements inside transactions
if using databases that enforce this behavior. If necessary, separate DDL operations
from transactional logic.

When the script ends or when a connection is about to be closed, if you
have an outstanding transaction, PDO will automatically roll it back.
This is a safety measure to help avoid inconsistency in the cases where
the script terminates unexpectedly--if you didn't explicitly commit the
transaction, then it is assumed that something went awry, so the rollback
is performed for the safety of your data.

**Warning**

The automatic rollback only happens if you initiate the transaction via
PDO::beginTransaction(). If you manually issue a
query that begins a transaction PDO has no way of knowing about it and
thus cannot roll it back if something bad happens.

**Example #2 Executing a batch in a transaction**

In the following sample, let's assume that we are creating a set of
entries for a new employee, who has been assigned an ID number of 23.
In addition to entering the basic data for that person, we also need to
record their salary. It's pretty simple to make two separate updates,
but by enclosing them within the
PDO::beginTransaction() and
PDO::commit() calls, we are guaranteeing that no one
else will be able to see those changes until they are complete. If
something goes wrong, the catch block rolls back all changes made
since the transaction was started, and then prints out an error
message.

```sql
<?php
try {
  $dbh = new PDO('odbc:SAMPLE', 'db2inst1', 'ibmdb2',
      array(PDO::ATTR_PERSISTENT => true));
  echo "Connected\n";
} catch (Exception $e) {
  die("Unable to connect: " . $e->getMessage());
}

try {
  $dbh->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

  $dbh->beginTransaction();
  $dbh->exec("insert into staff (id, first, last) values (23, 'Joe', 'Bloggs')");
  $dbh->exec("insert into salarychange (id, amount, changedate)
      values (23, 50000, NOW())");
  $dbh->commit();

} catch (Exception $e) {
  $dbh->rollBack();
  echo "Failed: " . $e->getMessage();
}
?>
```

You're not limited to making updates in a transaction; you can also issue
complex queries to extract data, and possibly use that information to
build up more updates and queries; while the transaction is active, you
are guaranteed that no one else can make changes while you are in the
middle of your work. For further reading on transactions, refer to the
documentation provided by your database server.

### Found A Problem?
