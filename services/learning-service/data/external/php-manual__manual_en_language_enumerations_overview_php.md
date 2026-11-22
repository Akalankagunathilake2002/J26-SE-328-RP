<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/language.enumerations.overview.php -->
# PHP: Enumerations overview

(PHP 8 >= 8.1.0)

Enumerations, or "Enums", allow a developer to define a custom type that is limited to one
of a discrete number of possible values. That can be especially helpful when defining a
domain model, as it enables "making invalid states unrepresentable."

Enums appear in many languages with a variety of different features. In PHP,
Enums are a special kind of object. The Enum itself is a class, and its possible
cases are all single-instance objects of that class. That means Enum cases are
valid objects and may be used anywhere an object may be used, including type checks.

The most popular example of enumerations is the built-in boolean type, which is an
enumerated type with legal values **`true`** and **`false`**.
Enums allows developers to define their own arbitrarily robust enumerations.

### Found A Problem?
