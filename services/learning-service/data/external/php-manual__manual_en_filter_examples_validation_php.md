<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/filter.examples.validation.php -->
# PHP: Validation

**Example #1 Validating email addresses with filter\_var()**

```sql
<?php
$email_a = 'joe@example.com';
$email_b = 'bogus';

if (filter_var($email_a, FILTER_VALIDATE_EMAIL)) {
    echo "Email address '$email_a' is considered valid.\n";
}
if (filter_var($email_b, FILTER_VALIDATE_EMAIL)) {
    echo "Email address '$email_b' is considered valid.\n";
} else {
    echo "Email address '$email_b' is considered invalid.\n";
}
?>
```

The above example will output:

```sql
Email address 'joe@example.com' is considered valid.
Email address 'bogus' is considered invalid.
```

**Example #2 Validating IP addresses with filter\_var()**

```sql
<?php
$ip_a = '127.0.0.1';
$ip_b = '42.42';

if (filter_var($ip_a, FILTER_VALIDATE_IP)) {
    echo "IP address '$ip_a' is considered valid.";
}
if (filter_var($ip_b, FILTER_VALIDATE_IP)) {
    echo "IP address '$ip_b' is considered valid.";
}
?>
```

The above example will output:

```sql
IP address '127.0.0.1' is considered valid.
```

**Example #3 Passing options to filter\_var()**

```sql
<?php
$int_a = '1';
$int_b = '-1';
$int_c = '4';
$options = array(
    'options' => array(
        'min_range' => 0,
        'max_range' => 3,
    )
);
if (filter_var($int_a, FILTER_VALIDATE_INT, $options) !== FALSE) {
    echo "Integer A '$int_a' is considered valid (between 0 and 3).\n";
}
if (filter_var($int_b, FILTER_VALIDATE_INT, $options) !== FALSE) {
    echo "Integer B '$int_b' is considered valid (between 0 and 3).\n";
}
if (filter_var($int_c, FILTER_VALIDATE_INT, $options) !== FALSE) {
    echo "Integer C '$int_c' is considered valid (between 0 and 3).\n";
}

$options'options' = 1;
if (($int_c = filter_var($int_c, FILTER_VALIDATE_INT, $options)) !== FALSE) {
    echo "Integer C '$int_c' is considered valid (between 0 and 3).";
}
?>
```

The above example will output:

```sql
Integer A '1' is considered valid (between 0 and 3).
Integer C '1' is considered valid (between 0 and 3).
```

### Found A Problem?
