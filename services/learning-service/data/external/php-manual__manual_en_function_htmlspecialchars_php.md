<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/function.htmlspecialchars.php -->
# PHP: htmlspecialchars

(PHP 4, PHP 5, PHP 7, PHP 8)

htmlspecialchars — Convert special characters to HTML entities

### Description

function **htmlspecialchars**(
    string `$string`,
    int `$flags` = ENT\_QUOTES | ENT\_SUBSTITUTE | ENT\_HTML401,
    ?string `$encoding` = **`null`**,
    bool `$double_encode` = **`true`**
): string

Certain characters have special significance in HTML, and should
be represented by HTML entities if they are to preserve their
meanings. This function returns a string with these
conversions made. If you require all input substrings that have associated
named entities to be translated, use htmlentities()
instead.

If the input string passed to this function and the final document share the
same character set, this function is sufficient to prepare input for
inclusion in most contexts of an HTML document. If, however, the input can
represent characters that are not coded in the final document character set
and you wish to retain those characters (as numeric or named entities),
both this function and htmlentities() (which only encodes
substrings that have named entity equivalents) may be insufficient.
You may have to use mb\_encode\_numericentity() instead.

**Performed translations**

| Character | Replacement |
| --- | --- |
| `&` (ampersand) | `&` |
| `"` (double quote) | `"`, unless **`ENT_NOQUOTES`** is set |
| `'` (single quote) | `'` (for **`ENT_HTML401`**) or `'` (for **`ENT_XML1`**, **`ENT_XHTML`** or **`ENT_HTML5`**), but only when **`ENT_QUOTES`** is set |
| `<` (less than) | `<` |
| `>` (greater than) | `>` |

### Parameters

`string`
:   The string being converted.

`flags`
:   A bitmask of one or more of the following flags, which specify how to handle quotes,
    invalid code unit sequences and the used document type. The default is
    `ENT_QUOTES | ENT_SUBSTITUTE | ENT_HTML401`.

    **Available `flags` constants**

    | Constant Name | Description |
    | --- | --- |
    | **`ENT_COMPAT`** | Will convert double-quotes and leave single-quotes alone. |
    | **`ENT_QUOTES`** | Will convert both double and single quotes. |
    | **`ENT_NOQUOTES`** | Will leave both double and single quotes unconverted. |
    | **`ENT_IGNORE`** | Silently discard invalid code unit sequences instead of returning an empty string. Using this flag is discouraged as it » may have security implications. |
    | **`ENT_SUBSTITUTE`** | Replace invalid code unit sequences with a Unicode Replacement Character U+FFFD (UTF-8) or � (otherwise) instead of returning an empty string. |
    | **`ENT_DISALLOWED`** | Replace invalid code points for the given document type with a Unicode Replacement Character U+FFFD (UTF-8) or � (otherwise) instead of leaving them as is. This may be useful, for instance, to ensure the well-formedness of XML documents with embedded external content. |
    | **`ENT_HTML401`** | Handle code as HTML 4.01. |
    | **`ENT_XML1`** | Handle code as XML 1. |
    | **`ENT_XHTML`** | Handle code as XHTML. |
    | **`ENT_HTML5`** | Handle code as HTML 5. |

`encoding`
:   An optional argument defining the encoding used when converting characters.

    If omitted, `encoding` defaults to the value of the
    default\_charset configuration
    option.

    Although this argument is technically optional, you are highly encouraged to
    specify the correct value for your code
    if the default\_charset
    configuration option may be set incorrectly for the given input.

    For the purposes of this function, the encodings
    `ISO-8859-1`, `ISO-8859-15`,
    `UTF-8`, `cp866`,
    `cp1251`, `cp1252`, and
    `KOI8-R` are effectively equivalent, provided the
    `string` itself is valid for the encoding, as
    the characters affected by **htmlspecialchars()** occupy
    the same positions in all of these encodings.

    The following character sets are supported:

    **Supported charsets**

    | Charset | Aliases | Description |
    | --- | --- | --- |
    | ISO-8859-1 | ISO8859-1 | Western European, Latin-1. |
    | ISO-8859-5 | ISO8859-5 | Little used cyrillic charset (Latin/Cyrillic). |
    | ISO-8859-15 | ISO8859-15 | Western European, Latin-9. Adds the Euro sign, French and Finnish letters missing in Latin-1 (ISO-8859-1). |
    | UTF-8 |  | ASCII compatible multi-byte 8-bit Unicode. |
    | cp866 | ibm866, 866 | DOS-specific Cyrillic charset. |
    | cp1251 | Windows-1251, win-1251, 1251 | Windows-specific Cyrillic charset. |
    | cp1252 | Windows-1252, 1252 | Windows specific charset for Western European. |
    | KOI8-R | koi8-ru, koi8r | Russian. |
    | BIG5 | 950 | Traditional Chinese, mainly used in Taiwan. |
    | GB2312 | 936 | Simplified Chinese, national standard character set. |
    | BIG5-HKSCS |  | Big5 with Hong Kong extensions, Traditional Chinese. |
    | Shift\_JIS | SJIS, SJIS-win, cp932, 932 | Japanese |
    | EUC-JP | EUCJP, eucJP-win | Japanese |
    | MacRoman |  | Charset that was used by Mac OS. |
    | `''` |  | An empty string activates detection from script encoding (Zend multibyte), default\_charset and current locale (see nl\_langinfo() and setlocale()), in this order. Not recommended. |

    > **Note**:
    >
    > Any other character sets are not recognized. The default encoding will be
    > used instead and a warning will be emitted.

`double_encode`
:   When `double_encode` is turned off PHP will not
    encode existing html entities, the default is to convert everything.

### Return Values

The converted string.

If the input `string` contains an invalid code unit
sequence within the given `encoding` an empty string
will be returned, unless either the **`ENT_IGNORE`** or
**`ENT_SUBSTITUTE`** flags are set.

### Changelog

| Version | Description |
| --- | --- |
| 8.1.0 | `flags` changed from **`ENT_COMPAT`** to **`ENT_QUOTES`** | **`ENT_SUBSTITUTE`** | **`ENT_HTML401`**. |

### Examples

**Example #1 **htmlspecialchars()** example**

```sql
<?php
$new = htmlspecialchars("Test", ENT_QUOTES);
echo $new; // <a href='test'>Test</a>
?>
```

**Example #2 **`ENT_IGNORE`** and **`ENT_SUBSTITUTE`** with invalid UTF-8 sequences**

```sql
<?php
// "\x80" is not a valid UTF-8 byte sequence.
$input = "atta\x80ck";

// ENT_IGNORE silently drops the invalid byte - output: "attack"
echo bin2hex(htmlspecialchars($input, ENT_QUOTES | ENT_IGNORE, 'UTF-8')), "\n";
// 61747461636b

// ENT_SUBSTITUTE replaces the invalid byte with U+FFFD - output: "atta" + replacement char + "ck"
echo bin2hex(htmlspecialchars($input, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8')), "\n";
// 61747461efbfbd636b
?>
```

### Notes

> **Note**:
>
> Note that this function does not translate anything beyond what
> is listed above. For full entity translation, see
> htmlentities().

> **Note**:
>
> In case of an ambiguous `flags` value, the following rules apply:
>
> * When neither of **`ENT_COMPAT`**, **`ENT_QUOTES`**,
>   **`ENT_NOQUOTES`** is present, the default is **`ENT_NOQUOTES`**.
> * When more than one of **`ENT_COMPAT`**, **`ENT_QUOTES`**,
>   **`ENT_NOQUOTES`** is present, **`ENT_QUOTES`** takes the
>   highest precedence, followed by **`ENT_COMPAT`**.
> * When neither of **`ENT_HTML401`**, **`ENT_HTML5`**,
>   **`ENT_XHTML`**, **`ENT_XML1`** is present, the default is
>   **`ENT_HTML401`**.
> * When more than one of **`ENT_HTML401`**, **`ENT_HTML5`**,
>   **`ENT_XHTML`**, **`ENT_XML1`** is present,
>   **`ENT_HTML5`** takes the highest precedence,
>   followed by **`ENT_XHTML`**, **`ENT_XML1`** and **`ENT_HTML401`**.
> * When more than one of **`ENT_DISALLOWED`**, **`ENT_IGNORE`**,
>   **`ENT_SUBSTITUTE`** are present, **`ENT_IGNORE`** takes the
>   highest precedence, followed by **`ENT_SUBSTITUTE`**.

### See Also

* get\_html\_translation\_table() - Returns the translation table used by htmlspecialchars and htmlentities
* htmlspecialchars\_decode() - Convert special HTML entities back to characters
* strip\_tags() - Strip HTML and PHP tags from a string
* htmlentities() - Convert all applicable characters to HTML entities
* nl2br() - Inserts HTML line breaks before all newlines in a string

### Found A Problem?
