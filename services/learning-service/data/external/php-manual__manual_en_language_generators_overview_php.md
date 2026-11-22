<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/language.generators.overview.php -->
# PHP: Generators overview

(PHP 5 >= 5.5.0, PHP 7, PHP 8)

Generators provide an easy way to implement simple
iterators without the
overhead or complexity of implementing a class that implements the
Iterator interface.

A generator offers a convenient way to provide data to `foreach` loops without
having to build an array in memory ahead of time, which may cause the program
to exceed a memory limit or require a considerable amount of
processing time to generate. Instead, a generator function can be used,
which is the same as a normal
function, except that instead
of
returning once, a
generator can `yield` as many times as it needs to in order to provide the
values to be iterated over.
Like with iterators, random data access is not possible.

A simple example of this is to reimplement the range()
function as a generator. The standard range() function
has to generate an array with every value in it and return it, which can
result in large arrays: for example, calling
**range(0, 1000000)** will result in well over 10 MB of
memory being used.

As an alternative, we can implement an `xrange()`
generator, which will only ever need enough memory to create an
Iterator object and track the current state of the
generator internally, which turns out to be less than 1 kilobyte.

**Example #1 Implementing range() as a generator**

```sql
<?php
function xrange($start, $limit, $step = 1) {
    if ($start <= $limit) {
        if ($step <= 0) {
            throw new LogicException('Step must be positive');
        }

        for ($i = $start; $i <= $limit; $i += $step) {
            yield $i;
        }
    } else {
        if ($step >= 0) {
            throw new LogicException('Step must be negative');
        }

        for ($i = $start; $i >= $limit; $i += $step) {
            yield $i;
        }
    }
}

/*
 * Note that both range() and xrange() result in the same
 * output below.
 */

echo 'Single digit odd numbers from range():  ';
foreach (range(1, 9, 2) as $number) {
    echo "$number ";
}
echo "\n";

echo 'Single digit odd numbers from xrange(): ';
foreach (xrange(1, 9, 2) as $number) {
    echo "$number ";
}
```

The above example will output:

```sql
Single digit odd numbers from range():  1 3 5 7 9
Single digit odd numbers from xrange(): 1 3 5 7 9
```

### Generator objects

When a generator function is called, a new object of the
internal Generator class is returned. This object
implements the Iterator interface in much the same
way as a forward-only iterator object would, and provides methods that can
be called to manipulate the state of the generator, including sending
values to and returning values from it.

### Found A Problem?
