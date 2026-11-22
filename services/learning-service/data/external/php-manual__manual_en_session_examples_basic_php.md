<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/session.examples.basic.php -->
# PHP: Basic usage

Sessions are a simple way to store data for individual users against a unique session ID.
This can be used to persist state information between page requests. Session IDs are normally
sent to the browser via session cookies and the ID is used to retrieve existing session data.
The absence of an ID or session cookie lets PHP know to create a new session, and generate a new
session ID.

Sessions follow a simple workflow. When a session is started, PHP will either retrieve an
existing session using the ID passed (usually from a session cookie) or if no session is passed
it will create a new session. PHP will populate the $\_SESSION superglobal
with any session data after the session has started. When PHP shuts down, it will automatically
take the contents of the $\_SESSION superglobal, serialize it, and send it
for storage using the session save handler.

By default, PHP uses the internal `files` save handler which
is set by session.save\_handler.
This saves session data on the server at the location specified by the
session.save\_path configuration directive.

Sessions can be started manually using the session\_start() function.
If the session.auto\_start directive is set
to `1`, a session will automatically start on request startup.

Sessions normally shutdown automatically when PHP is finished executing a script, but can be
manually shutdown using the session\_write\_close() function.

**Example #1
Registering a variable with $\_SESSION.**

```sql
<?php
session_start();
if (!isset($_SESSION['count'])) {
  $_SESSION['count'] = 0;
} else {
  $_SESSION['count']++;
}
?>
```

**Example #2
Unregistering a variable with $\_SESSION.**

```sql
<?php
session_start();
unset($_SESSION['count']);
?>
```

**Caution**

Do NOT unset the whole $\_SESSION with
`unset($_SESSION)` as this will disable the
registering of session variables through the
$\_SESSION superglobal.

**Warning**

You can't use references in session variables as there is no feasible way
to restore a reference to another variable.

> **Note**:
>
> File based sessions (the default in PHP) lock the session file once a
> session is opened via session\_start() or implicitly via
> session.auto\_start. Once
> locked, no other script can access the same session file until it has been
> closed by the first script terminating or calling
> session\_write\_close().
>
> This is most likely to be an issue on Web sites that use AJAX heavily and
> have multiple concurrent requests. The easiest way to deal with it is to
> call session\_write\_close() as soon as any required
> changes to the session have been made, preferably early in the script.
> Alternatively, a different session backend that does support concurrency
> could be used.

### Found A Problem?
