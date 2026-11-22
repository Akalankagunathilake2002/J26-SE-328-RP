<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/features.cookies.php -->
# PHP: Cookies

PHP transparently supports HTTP cookies. Cookies are a mechanism for
storing data in the remote browser and thus tracking or identifying return
users. You can set cookies using the setcookie() or
setrawcookie()
function. Cookies are part of the HTTP header, so
setcookie() must be called before any output is sent to
the browser. This is the same limitation that header()
has. You can use the output buffering
functions to delay the script output until you have decided whether
or not to set any cookies or send any headers.

Any cookies sent to the server from the client will automatically be included into
a $\_COOKIE auto-global
array if variables\_order
contains "C". If you wish to assign multiple values to a single
cookie, just add `[]` to the cookie name.

For more details, including notes on browser bugs, see the
setcookie() and setrawcookie()
functions.

### Found A Problem?
