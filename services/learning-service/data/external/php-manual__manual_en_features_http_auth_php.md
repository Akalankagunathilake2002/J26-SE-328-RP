<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/features.http-auth.php -->
# PHP: HTTP authentication with PHP

It is possible to use the
header() function to send an `"Authentication Required"`
message to the client browser causing it to pop up a Username/Password
input window. Once the user has filled in a username and a password,
the URL containing the PHP script will be called again with the
predefined variables
PHP\_AUTH\_USER, PHP\_AUTH\_PW,
and AUTH\_TYPE set to the username, password and
authentication type respectively. These predefined variables are found
in the $\_SERVER array. *Only*
the "Basic" authentication method is supported. See the
header() function for more information.

An example script fragment which would force client authentication
on a page is as follows:

**Example #1 Basic HTTP Authentication example**

```sql
<?php
if (!isset($_SERVER['PHP_AUTH_USER'])) {
    header('HTTP/1.1 401 Unauthorized');
    header('WWW-Authenticate: Basic realm="My Realm"');
    echo 'Text to send if user hits Cancel button';
    exit;
} else {
    echo "Hello {$_SERVER['PHP_AUTH_USER']}.";
    echo "You entered {$_SERVER['PHP_AUTH_PW']} as your password.";
}
?>
```

> **Note**:
> **Compatibility**
>
> Please be careful when coding the HTTP header lines. In order to guarantee maximum
> compatibility with all clients, the keyword "Basic" should be written with an
> uppercase "B", the realm string must be enclosed in double (not single) quotes,
> and exactly one space should precede the *401* code in the
> *HTTP/1.1 401* header line. Authentication parameters have
> to be comma-separated.

Instead of simply printing out PHP\_AUTH\_USER
and PHP\_AUTH\_PW, as done in the above example,
you may want to check the username and password for validity.
Perhaps by sending a query to a database, or by looking up the
user in a dbm file.

> **Note**:
> **Apache Configuration**
>
> PHP uses the presence of an `AuthType` directive
> to determine whether external authentication is in effect.

Note, however, that the above does not prevent someone who
controls a non-authenticated URL from stealing passwords from
authenticated URLs on the same server.

> **Note**:
> **Browser behavior**
>
> HTTP Basic authentication really is basic, and it wasn't designed to support
> logouts. Because HTTP is a stateless protocol, most browsers will cache the
> provided credentials as soon as a `2xx` status code is seen,
> and will send them in every request, until the browser is closed. There is no
> defined way for a server to request a new prompt for credentials.
> Over the years, various workarounds for this have spread as advice on the internet,
> but they all depend on how different browsers have chosen to handle undefined edge
> cases (or even violations of the HTTP standard). It is best to avoid such
> workarounds and not use Basic authentication for anything serious.

> **Note**:
> **IIS Configuration**
>
> In order to get HTTP Authentication to work on IIS server with the CGI version of
> PHP, the php.ini directive cgi.rfc2616\_headers
> must be set to `0` (the default value), and you must edit your IIS
> configuration "`Directory Security`".
> Click on "`Edit`" and only check "`Anonymous Access`",
> all other fields should be left unchecked.

### Found A Problem?
