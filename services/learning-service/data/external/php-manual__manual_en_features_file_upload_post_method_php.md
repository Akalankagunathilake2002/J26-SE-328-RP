<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/features.file-upload.post-method.php -->
# PHP: POST method uploads

This feature lets people upload both text and binary files.
With PHP's authentication and file manipulation functions,
you have full control over who is allowed to upload and
what is to be done with the file once it has been uploaded.

PHP is capable of receiving file uploads from any RFC-1867
compliant browser.

> **Note**:
> **Related Configurations Note**
>
> See also the file\_uploads,
> upload\_max\_filesize,
> upload\_tmp\_dir,
> post\_max\_size and
> max\_input\_time directives
> in php.ini

PHP also supports PUT-method file uploads as used by
Netscape Composer and W3C's
Amaya clients. See the PUT Method
Support for more details.

**Example #1 File Upload Form**

A file upload screen can be built by creating a special form which
looks something like this:

```sql

    Send this file:

```

The `__URL__` in the above example should be replaced,
and point to a PHP file.

The `MAX_FILE_SIZE` hidden field (measured in bytes) must
precede the file input field, and its value is the maximum filesize accepted by PHP.
This form element should always be used as it saves users the trouble of
waiting for a big file being transferred only to find that it was too
large and the transfer failed. Keep in mind: fooling this setting on the
browser side is quite easy, so never rely on files with a greater size
being blocked by this feature. It is merely a convenience feature for
users on the client side of the application. The PHP settings (on the server
side) for maximum-size, however, cannot be fooled.

> **Note**:
>
> Be sure your file upload form has attribute `enctype="multipart/form-data"`
> otherwise the file upload will not work.

The global $\_FILES will contain all the uploaded file information.
Its contents from the example form are as follows. Note that this assumes the use of
the file upload name *userfile*, as used in the example
script above. This can be any name.

$\_FILES'userfile'
:   The original name of the file on the client machine.

$\_FILES'userfile'
:   The mime type of the file, if the browser provided this
    information. An example would be
    `"image/gif"`. This mime type is however
    not checked on the PHP side and therefore do not take its value
    for granted.

$\_FILES'userfile'
:   The size, in bytes, of the uploaded file.

$\_FILES'userfile'
:   The temporary filename of the file in which the uploaded file
    was stored on the server.

$\_FILES'userfile'
:   The error code
    associated with this file upload.

$\_FILES'userfile'
:   The full path as submitted by the browser. This value does not always contain a real directory structure, and cannot be trusted.
    Available as of PHP 8.1.0.

Files will, by default be stored in the server's default temporary
directory, unless another location has been given with the upload\_tmp\_dir directive in
php.ini. The server's default directory can
be changed by setting the environment variable
TMPDIR in the environment in which PHP runs.
Setting it using putenv() from within a PHP
script will not work. This environment variable can also be used
to make sure that other operations are working on uploaded files,
as well.

**Example #2 Validating file uploads**

See also the function entries for is\_uploaded\_file()
and move\_uploaded\_file() for further information. The
following example will process the file upload that came from a form.

```sql
<?php
$uploaddir = '/var/www/uploads/';
$uploadfile = $uploaddir . basename($_FILES'userfile');

echo '<pre>';
if (move_uploaded_file($_FILES'userfile', $uploadfile)) {
    echo "File is valid, and was successfully uploaded.\n";
} else {
    echo "Possible file upload attack!\n";
}

echo 'Here is some more debugging info:';
print_r($_FILES);

print "</pre>";

?>
```

The PHP script which receives the uploaded file should implement
whatever logic is necessary for determining what should be done
with the uploaded file. You can, for example, use the
$\_FILES'userfile' variable
to throw away any files that are either too small or too big. You
could use the
$\_FILES'userfile' variable
to throw away any files that didn't match a certain type criteria, but
use this only as first of a series of checks, because this value
is completely under the control of the client and not checked on the PHP
side.
Also, you could use $\_FILES'userfile'
and plan your logic according to the error codes.
Whatever the logic, you should either delete the file from the
temporary directory or move it elsewhere.

If no file is selected for upload in your form, PHP will return
$\_FILES'userfile' as 0, and
$\_FILES'userfile' as none.

The file will be deleted from the temporary directory at the end
of the request if it has not been moved away or renamed.

**Example #3 Uploading array of files**

PHP supports HTML array feature
even with files.

```sql

Pictures:

```

```sql
<?php
foreach ($_FILES"pictures" as $key => $error) {
    if ($error == UPLOAD_ERR_OK) {
        $tmp_name = $_FILES"pictures"[$key];
        // basename() may prevent filesystem traversal attacks;
        // further validation/sanitization of the filename may be appropriate
        $name = basename($_FILES"pictures"[$key]);
        move_uploaded_file($tmp_name, "data/$name");
    }
}
?>
```

File upload progress bar can be implemented using Session Upload Progress.

### Found A Problem?
