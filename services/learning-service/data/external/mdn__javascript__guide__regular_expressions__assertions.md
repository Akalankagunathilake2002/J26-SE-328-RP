<!-- role: Full-Stack Developer -->
<!-- topic: JavaScript Guide -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_expressions/Assertions -->
# Assertions

Assertions include boundaries, which indicate the beginnings and endings of lines and words, and other patterns indicating in some way that a match is possible (including look-ahead, look-behind, and conditional expressions).

taller

```js interactive-example
const text = "A quick fox";

const regexpLastWord = /\w+$/;
console.log(text.match(regexpLastWord));
// Expected output: Array ["fox"]

const regexpWords = /\b\w+\b/g;
console.log(text.match(regexpWords));
// Expected output: Array ["A", "quick", "fox"]

const regexpFoxQuality = /\w+(?= fox)/;
console.log(text.match(regexpFoxQuality));
// Expected output: Array ["quick"]
```

## Types

### Boundary-type assertions

      Characters
      Meaning

      <code>^</code>

          Input boundary beginning assertion:
          Matches the beginning of input. If the <code>multiline</code> (m) flag is enabled,
          also matches immediately after a line break character. For example,
          <code>/^A/</code> does not match the "A" in "an A", but does match the
          first "A" in "An A".

            Note: This character has a different meaning when
            it appears at the start of a
            <a
              href="/en-US/docs/Web/JavaScript/Guide/Regular_expressions/Character_classes"
              >character class</a
            >.

      <code>$</code>

          Input boundary end assertion:
          Matches the end of input. If the <code>multiline</code> (m) flag is enabled, also
          matches immediately before a line break character. For example,
          <code>/t$/</code> does not match the "t" in "eater", but does match it
          in "eat".

      <code>\A</code>

          Buffer boundary start assertion: Matches the start of the entire string regardless of the presence of the <code>m</code> flag.
          Only valid in Unicode-aware mode.

      <code>\z</code>

          Buffer boundary end assertion: Matches the end of the entire string regardless of the presence of the <code>m</code> flag.
          Only valid in Unicode-aware mode.

      <code>\Z</code>

          Buffer boundary end assertion with optional newline: Matches the end of the entire string, but allows an optional trailing newline character sequence (either a line terminator or a <code>\r\n</code> sequence).
          Only valid in Unicode-aware mode.

      <code>\b</code>

          Word boundary assertion:
          Matches a word boundary. This is the position where a word character
          is not followed or preceded by another word-character, such as between
          a letter and a space. Note that a matched word boundary is not
          included in the match. In other words, the length of a matched word
          boundary is zero.

        Examples:

          <code>/\bm/</code> matches the "m" in "moon".

            <code>/oo\b/</code> does not match the "oo" in "moon", because "oo"
            is followed by "n" which is a word character.

            <code>/oon\b/</code> matches the "oon" in "moon", because "oon" is
            the end of the string, thus not followed by a word character.

            <code>/\w\b\w/</code> will never match anything, because a word
            character can never be followed by both a non-word and a word
            character.

          To match a backspace character (<code>[\b]</code>), see
          <a
            href="/en-US/docs/Web/JavaScript/Guide/Regular_expressions/Character_classes"
            >Character Classes</a
          >.

      <code>\B</code>

          Non-word-boundary assertion:
          Matches a non-word boundary. This is a position where the previous and
          next character are of the same type: Either both must be words, or
          both must be non-words, for example between two letters or between two
          spaces. The beginning and end of a string are considered non-words.
          Same as the matched word boundary, the matched non-word boundary is
          also not included in the match. For example,
          <code>/\Bon/</code> matches "on" in "at noon", and
          <code>/ye\B/</code> matches "ye" in "possibly yesterday".

### Other assertions

> [!NOTE]
> The `?` character may also be used as a quantifier.

      Characters
      Meaning

      <code>x(?=y)</code>

          Lookahead assertion:
          Matches "x" only if "x" is
          followed by "y". For example, <code>/Jack(?=Sprat)/</code> matches
          "Jack" only if it is followed by "Sprat".<code
            >/Jack(?=Sprat|Frost)/</code
          >
          matches "Jack" only if it is followed by "Sprat" or "Frost". However,
          neither "Sprat" nor "Frost" is part of the match results.

      <code>x(?!y)</code>

          Negative lookahead assertion:
          Matches "x" only if "x"
          is not followed by "y". For example, <code>/\d+(?!\.)/</code> matches
          a number only if it is not followed by a decimal point. <code
            >/\d+(?!\.)/.exec('3.141')</code
          >
          matches "141" but not "3".

      <code>(?<=y)x</code>

          Lookbehind assertion:
          Matches "x" only if "x" is
          preceded by "y". For example,
          <code>/(?<=Jack)Sprat/</code> matches "Sprat" only if it is
          preceded by "Jack". <code>/(?<=Jack|Tom)Sprat/</code> matches
          "Sprat" only if it is preceded by "Jack" or "Tom". However, neither
          "Jack" nor "Tom" is part of the match results.

      <code>(?<!y)x</code>

          Negative lookbehind assertion:
          Matches "x" only if
          "x" is not preceded by "y". For example,
          <code>/(?<!-)\d+/</code> matches a number only if it is not
          preceded by a minus sign. <code>/(?<!-)\d+/.exec('3')</code>
          matches "3". <code>/(?<!-)\d+/.exec('-3')</code>  match is not
          found because the number is preceded by the minus sign.

## Examples

### General boundary-type overview example

```js
// Using Regex boundaries to fix buggy string.
buggyMultiline = `tey, ihe light-greon apple
tangs on ihe greon traa`;

// 1) Use ^ to fix the matching at the beginning of the string, and right after newline.
buggyMultiline = buggyMultiline.replace(/^t/gim, "h");
console.log(1, buggyMultiline); // fix 'tey' => 'hey' and 'tangs' => 'hangs' but do not touch 'traa'.

// 2) Use $ to fix matching at the end of the text.
buggyMultiline = buggyMultiline.replace(/aa$/gim, "ee.");
console.log(2, buggyMultiline); // fix 'traa' => 'tree.'.

// 3) Use \b to match characters right on border between a word and a space.
buggyMultiline = buggyMultiline.replace(/\bi/gim, "t");
console.log(3, buggyMultiline); // fix 'ihe' => 'the' but do not touch 'light'.

// 4) Use \B to match characters inside borders of an entity.
fixedMultiline = buggyMultiline.replace(/\Bo/gim, "e");
console.log(4, fixedMultiline); // fix 'greon' => 'green' but do not touch 'on'.
```

### Matching the beginning of input using a ^ control character

Use `^` for matching at the beginning of input. In this example, we can get the fruits that start with 'A' by a `/^A/` regex. For selecting appropriate fruits we can use the `filter` method with an arrow function.

```js
const fruits = ["Apple", "Watermelon", "Orange", "Avocado", "Strawberry"];

// Select fruits started with 'A' by /^A/ Regex.
// Here '^' control symbol used only in one role: Matching beginning of an input.

const fruitsStartsWithA = fruits.filter((fruit) => /^A/.test(fruit));
console.log(fruitsStartsWithA); // [ 'Apple', 'Avocado' ]
```

In the second example `^` is used both for matching at the beginning of input and for creating negated or complemented character class when used within character classes.

```js
const fruits = ["Apple", "Watermelon", "Orange", "Avocado", "Strawberry"];

// Selecting fruits that do not start by 'A' with a /^[^A]/ regex.
// In this example, two meanings of '^' control symbol are represented:
// 1) Matching beginning of the input
// 2) A negated or complemented character class: [^A]
// That is, it matches anything that is not enclosed in the square brackets.

const fruitsStartsWithNotA = fruits.filter((fruit) => /^[^A]/.test(fruit));

console.log(fruitsStartsWithNotA); // [ 'Watermelon', 'Orange', 'Strawberry' ]
```

See more examples in the input boundary assertion reference.

### Matching a word boundary

In this example, we match fruit names containing a word that ends in "en" or "ed".

```js
const fruitsWithDescription = ["Red apple", "Orange orange", "Green Avocado"];

// Select descriptions that contains 'en' or 'ed' words endings:
const enEdSelection = fruitsWithDescription.filter((description) =>
  /(?:en|ed)\b/.test(description),
);

console.log(enEdSelection); // [ 'Red apple', 'Green Avocado' ]
```

See more examples in the word boundary assertion reference.

### Lookahead assertion

In this example, we match the word "First" only if it is followed by the word "test", but we do not include "test" in the match results.

```js
const regex = /First(?= test)/g;

console.log("First test".match(regex)); // [ 'First' ]
console.log("First peach".match(regex)); // null
console.log("This is a First test in a year.".match(regex)); // [ 'First' ]
console.log("This is a First peach in a month.".match(regex)); // null
```

See more examples in the lookahead assertion reference.

### Basic negative lookahead assertion

For example, `/\d+(?!\.)/` matches a number only if it is not followed by a decimal point. `/\d+(?!\.)/.exec('3.141')` matches "141" but not "3".

```js
console.log(/\d+(?!\.)/g.exec("3.141")); // [ '141', index: 2, input: '3.141' ]
```

See more examples in the lookahead assertion reference.

### Different meaning of '?!' combination usage in assertions and character classes

The `?!` combination has different meanings in assertions like `/x(?!y)/` and character classes like `[^?!]`.

```js
const orangeNotLemon =
  "Do you want to have an orange? Yes, I do not want to have a lemon!";

// Different meaning of '?!' combination usage in Assertions /x(?!y)/ and Ranges /[^?!]/
const selectNotLemonRegex = /[^?!]+have(?! a lemon)[^?!]+[?!]/gi;
console.log(orangeNotLemon.match(selectNotLemonRegex)); // [ 'Do you want to have an orange?' ]

const selectNotOrangeRegex = /[^?!]+have(?! an orange)[^?!]+[?!]/gi;
console.log(orangeNotLemon.match(selectNotOrangeRegex)); // [ ' Yes, I do not want to have a lemon!' ]
```

### Lookbehind assertion

In this example, we replace the word "orange" with "apple" only if it is preceded by the word "ripe".

```js
const oranges = ["ripe orange A", "green orange B", "ripe orange C"];

const newFruits = oranges.map((fruit) =>
  fruit.replace(/(?<=ripe )orange/, "apple"),
);
console.log(newFruits); // ['ripe apple A', 'green orange B', 'ripe apple C']
```

See more examples in the lookbehind assertion reference.
