<!-- role: Full-Stack Developer -->
<!-- topic: JavaScript Guide -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_expressions/Groups_and_backreferences -->
# Groups and backreferences

Groups group multiple patterns as a whole, and capturing groups provide extra submatch information when using a regular expression pattern to match against a string. Backreferences refer to a previously captured group in the same regular expression.

JavaScript Demo: RegExp Groups and backreferences

```js interactive-example
// Groups
const imageDescription = "This image has a resolution of 1440×900 pixels.";
const regexpSize = /(\d+)×(\d+)/;
const match = imageDescription.match(regexpSize);
console.log(`Width: ${match[1]} / Height: ${match[2]}.`);
// Expected output: "Width: 1440 / Height: 900."

// Backreferences
const findDuplicates = "foo foo bar";
const regex = /\b(\w+)\s+\1\b/g;
console.log(findDuplicates.match(regex));
// Expected output: Array ["foo foo"]
```

## Types

      Characters
      Meaning

      <code>(x)</code>

          Capturing group:
          Matches <code>x</code> and
          remembers the match. For example, <code>/(foo)/</code> matches and
          remembers "foo" in "foo bar".

          A regular expression may have multiple capturing groups. In results,
          matches to capturing groups typically in an array whose members are in
          the same order as the left parentheses in the capturing group. This is
          usually just the order of the capturing groups themselves. This
          becomes important when capturing groups are nested. Matches are
          accessed using the index of the result's elements (<code
            >[1], …, [n]</code
          >) or from the predefined <code>RegExp</code> object's properties
          (<code>$1, …, $9</code>).

          Capturing groups have a performance penalty. If you don't need the
          matched substring to be recalled, prefer non-capturing parentheses
          (see below).

          <code
            ><a
              href="/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/match"
              >String.prototype.match()</a
            ></code
          >
          won't return groups if the <code>/.../g</code> flag is set. However,
          you can still use
          <code
            ><a
              href="/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/matchAll"
              >String.prototype.matchAll()</a
            ></code
          >
          to get all matches.

      <code>(?<Name>x)</code>

          Named capturing group:
          Matches "x" and stores it on
          the groups property of the returned matches under the name specified
          by <code><Name></code>. The angle brackets (<code><</code>
          and <code>></code>) are required for group name.

          For example, to extract the United States area code from a phone
          number, we could use <code>/\((?<area>\d\d\d)\)/</code>. The
          resulting number would appear under <code>matches.groups.area</code>.

      <code>(?:x)</code>

          Non-capturing group:
          Matches "x" but does not remember
          the match. The matched substring cannot be recalled from the resulting
          array's elements (<code>[1], …, [n]</code>) or from the predefined
          <code>RegExp</code> object's properties (<code>$1, …, $9</code>).

      <code>(?flags:x)</code>, <code>(?flags-flags:x)</code>

          Modifier:
          Enables or disables the specified flags only to the enclosed pattern. Only the <code>i</code>, <code>m</code>, and <code>s</code> flags can be used in a modifier.

        <code>\n</code>

          Backreference:
          Where "n" is a positive integer. Matches the same substring matched by
          the nth capturing group in the regular expression
          (counting left parentheses). For example,
          <code>/apple(,)\sorange\1/</code> matches "apple, orange," in "apple,
          orange, cherry, peach".

      <code>\k<Name></code>

          Named backreference:
          A back reference to the last substring matching the
          Named capture group specified by
          <code><Name></code>.

          For example,
          <code>/(?<title>\w+), yes \k<title>/</code> matches "Sir,
          yes Sir" in "Do you copy? Sir, yes Sir!".

            Note: <code>\k</code> is used literally here to
            indicate the beginning of a back reference to a Named capture group.

## Examples

### Using groups

In this example, we match two words in a structured format by using capturing groups to remember them. `\w+` matches one or more word characters, and the parentheses `()` create a capturing group. The `g` flag is used to match all occurrences.

```js
const personList = `First_Name: John, Last_Name: Doe
First_Name: Jane, Last_Name: Smith`;

const regexpNames = /First_Name: (\w+), Last_Name: (\w+)/g;
for (const match of personList.matchAll(regexpNames)) {
  console.log(`Hello ${match[1]} ${match[2]}`);
}
```

See more examples in the capturing group reference.

### Using named groups

This example is the same as above, but we use named capturing groups to remember the matched words instead. This way, we can access the matched words by their meanings.

```js
const personList = `First_Name: John, Last_Name: Doe
First_Name: Jane, Last_Name: Smith`;

const regexpNames =
  /First_Name: (?\w+), Last_Name: (?\w+)/g;
for (const match of personList.matchAll(regexpNames)) {
  console.log(`Hello ${match.groups.firstName} ${match.groups.lastName}`);
}
```

See more examples in the named capturing group reference.

### Using groups and back references

In this example, we first match a single or double quote character with `['"]`, remember it, match an arbitrary number of characters with `.*?` (`*?` is a non-greedy quantifier), until we match the remembered quote character again with `\1`. The `\1` is a backreference to the first capturing group, which matches the same type of quote. The result will therefore be two strings: `"'"` and `'"'`.

```js
const quote = `Single quote "'" and double quote '"'`;
const regexpQuotes = /(['"]).*?\1/g;
for (const match of quote.matchAll(regexpQuotes)) {
  console.log(match[0]);
}
```

See more examples in the backreference reference.

### Using groups and match indices

By providing the `d` flag, the indices of each capturing group is returned. This is especially useful if you are correlating each matched group with the original text — for example, to provide compiler diagnostics.

```js
const code = `function add(x, y) {
  return x + y;
}`;
const functionRegexp =
  /(function\s+)(?$_\p{ID_Start}*)/du;
const match = functionRegexp.exec(code);
const lines = code.split("\n");
lines.splice(
  1,
  0,
  " ".repeat(match.indices1 - match.indices1) +
    "^".repeat(match.indices.groups.name[1] - match.indices.groups.name[0]),
);
console.log(lines.join("\n"));
// function add(x, y) {
//          ^^^
//   return x + y;
// }
```
