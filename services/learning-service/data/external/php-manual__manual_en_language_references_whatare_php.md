<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/language.references.whatare.php -->
# PHP: What References Are

References in PHP are a means to access the same variable content
by different names. They are not like C pointers; for instance,
you cannot perform pointer arithmetic using them, they are not
actual memory addresses, and so on. See
What References Are Not for more
information. Instead, they are
symbol table
aliases. Note that in PHP, variable name and variable content are different, so the same
content can have different names. The closest analogy is with
Unix filenames and files - variable names are directory entries,
while variable content is the file itself. References can be
likened to hardlinking in Unix filesystem.

### Found A Problem?
