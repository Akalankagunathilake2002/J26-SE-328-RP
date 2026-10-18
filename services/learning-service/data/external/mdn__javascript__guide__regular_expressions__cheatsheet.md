<!-- role: Full-Stack Developer -->
<!-- topic: JavaScript Guide -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_expressions/Cheatsheet -->
# Regular expression syntax cheat sheet

This page provides an overall cheat sheet of all the capabilities of `RegExp` syntax by aggregating the content of the articles in the `RegExp` guide. If you need more information on a specific topic, please follow the link on the corresponding heading to access the full article or head to the guide.

## Character classes

Character classes distinguish kinds of characters such as, for example, distinguishing between letters and digits.

      Characters
      Meaning

        <code>[xyz][a-c]</code>

          Character class:
          Matches any one of the enclosed characters. You can
          specify a range of characters by using a hyphen, but if the hyphen
          appears as the first or last character enclosed in the square brackets,
          it is taken as a literal hyphen to be included in the character class
          as a normal character.

          For example, <code>[abcd]</code> is the same as <code>[a-d]</code>.
          They match the "b" in "brisket", and the "c" in "chop".

          For example, <code>[abcd-]</code> and <code>[-abcd]</code> match the
          "b" in "brisket", the "c" in "chop", and the "-" (hyphen) in
          "non-profit".

          For example, <code>[\w-]</code> is the same as
          <code>[A-Za-z0-9_-]</code>. They both match the "b" in "brisket", the
          "c" in "chop", and the "n" in "non-profit".

          <code>[^xyz][^a-c]</code>

          Negated character class:
          Matches anything that is not enclosed in the square brackets. You can specify a range
          of characters by using a hyphen, but if the hyphen appears as the
          first character after the <code>^</code> or the last character enclosed in the square brackets, it is taken as
          a literal hyphen to be included in the character class as a normal
          character. For example, <code>[^abc]</code> is the same as
          <code>[^a-c]</code>. They initially match "o" in "bacon" and "h" in
          "chop".

            Note: The ^ character may also indicate the
            <a
              href="/en-US/docs/Web/JavaScript/Guide/Regular_expressions/Assertions"
              >beginning of input</a
            >.

      <code>.</code>

          Wildcard:
          Matches any single character except line terminators:
          <code>\n</code>, <code>\r</code>, <code>\u2028</code> or
          <code>\u2029</code>. For example, <code>/.y/</code> matches "my" and
          "ay", but not "yes", in "yes make my day", as there is no character before "y" in "yes". If the <code>dotAll</code> (s) flag is enabled, also matches line terminators.
          Inside a character class, the dot loses its special meaning and
          matches a literal dot.

      <code>\d</code>

          Digit character class escape:
          Matches any digit (Arabic numeral). Equivalent to <code>[0-9]</code>.
          For example, <code>/\d/</code> or <code>/[0-9]/</code> matches "2" in
          "B2 is the suite number".

      <code>\D</code>

          Non-digit character class escape:
          Matches any character that is not a digit (Arabic numeral). Equivalent
          to <code>[^0-9]</code>. For example, <code>/\D/</code> or
          <code>/[^0-9]/</code> matches "B" in "B2 is the suite number".

      <code>\w</code>

          Word character class escape:
          Matches any alphanumeric character from the basic Latin alphabet,
          including the underscore. Equivalent to <code>[A-Za-z0-9_]</code>. For
          example, <code>/\w/</code> matches "a" in "apple", "5" in "$5.28", "3"
          in "3D" and "m" in "Émanuel".

      <code>\W</code>

          Non-word character class escape:
          Matches any character that is not a word character from the basic
          Latin alphabet. Equivalent to <code>[^A-Za-z0-9_]</code>. For example,
          <code>/\W/</code> or <code>/[^A-Za-z0-9_]/</code> matches "%" in "50%"
          and "É" in "Émanuel".

      <code>\s</code>

          White space character class escape:
          Matches a single white space character, including space, tab, form
          feed, line feed, and other Unicode spaces. Equivalent to
          <code>[\f\n\r\t\v\u0020\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]</code>. For example, <code>/\s\w*/</code> matches " bar" in "foo bar".

      <code>\S</code>

          Non-white space character class escape:
          Matches a single character other than white space. Equivalent to
          <code>[^\f\n\r\t\v\u0020\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]</code>. For example, <code>/\S\w*/</code> matches "foo" in "foo bar".

      <code>\t</code>
      Matches a horizontal tab.

      <code>\r</code>
      Matches a carriage return.

      <code>\n</code>
      Matches a linefeed.

      <code>\v</code>
      Matches a vertical tab.

      <code>\f</code>
      Matches a form-feed.

      <code>[\b]</code>

        Matches a backspace. If you're looking for the word-boundary assertion
        (<code>\b</code>), see
        <a
          href="/en-US/docs/Web/JavaScript/Guide/Regular_expressions/Assertions"
          >Assertions</a
        >.

      <code>\0</code>
      Matches a NUL character. Do not follow this with another digit.

        <code>\cX</code>

          Matches a control character using
          <a href="https://en.wikipedia.org/wiki/Caret_notation"
            >caret notation</a
          >, where "X" is a letter from A–Z or a–z (corresponding to code points
          <code>U+0001</code>–<code>U+001A</code>). For example,
          <code>/\cM\cJ/</code> matches "\r\n".

        <code>\xhh</code>

        Hex escape:
        Matches the character with the code <code>hh</code> (two
        hexadecimal digits).

        <code>\uHHHH</code>

        Unicode escape:
        Matches a UTF-16 code-unit with the value <code>HHHH</code> (four hexadecimal digits).

        <code>\u{H…H}</code>

        Unicode code point escape:
        Matches the character with the Unicode value <code>U+H…H</code> (1 to 6 hexadecimal digits).
        Only valid in Unicode-aware mode.

        <code>\p{UnicodeProperty}</code>,
        <code>\P{UnicodeProperty}</code>

          Unicode character class escape:
          Matches a character based on its Unicode character properties: for example, emoji characters, or Japanese
          katakana characters, or Chinese/Japanese Han/Kanji characters,
          etc.).
          Only valid in Unicode-aware mode.

      <code>\</code>

          Indicates that the following character should be treated specially, or
          "escaped". It behaves one of two ways.

            For characters that are usually treated literally, indicates that
            the next character is special and not to be interpreted literally.
            For example, <code>/b/</code> matches the character "b". By placing
            a backslash in front of "b", that is by using <code>/\b/</code>, the
            character becomes special to mean match a word boundary.

            For characters that are usually treated specially, indicates that
            the next character is not special and should be interpreted
            literally. For example, "*" is a special character that means 0 or
            more occurrences of the preceding character should be matched; for
            example, <code>/a*/</code> means match 0 or more "a"s. To match
            <code>*</code> literally, precede it with a backslash; for example,
            <code>/a\*/</code> matches "a*".

            Note: To match this character literally, escape it
            with itself. In other words to search for <code>\</code> use
            <code>/\\/</code>.

        <code>x|y</code>

          Disjunction:
          Matches either "x" or "y". Each component, separated by a pipe (<code>|</code>), is called an alternative. For example,
          <code>/green|red/</code> matches "green" in "green apple" and "red" in
          "red apple".

            Note: A disjunction is another way to specify "a set of choices", but it's not a character class. Disjunctions are not atoms — you need to use a group to make it part of a bigger pattern. <code>[abc]</code> is functionally equivalent to <code>(?:a|b|c)</code>.

## Assertions

Assertions include boundaries, which indicate the beginnings and endings of lines and words, and other patterns indicating in some way that a match is possible (including look-ahead, look-behind, and conditional expressions).

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

## Groups and backreferences

Groups and backreferences indicate groups of expression characters.

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

## Quantifiers

Quantifiers indicate numbers of characters or expressions to match.

> [!NOTE]
> In the following, _item_ refers not only to singular characters, but also includes character classes and groups and backreferences.

      Characters
      Meaning

        <code>x*</code>

          Matches the preceding item "x" 0 or more times. For example,
          <code>/bo*/</code> matches "boooo" in "A ghost booooed" and "b" in "A
          bird warbled", but nothing in "A goat grunted".

        <code>x+</code>

          Matches the preceding item "x" 1 or more times. Equivalent to
          <code>{1,}</code>. For example, <code>/a+/</code> matches the "a" in
          "candy" and all the "a"'s in "caaaaaaandy".

        <code>x?</code>

          Matches the preceding item "x" 0 or 1 times. For example,
          <code>/e?le?/</code> matches the "el" in "angel" and the "le" in
          "angle."

          If used immediately after any of the quantifiers <code>*</code>,
          <code>+</code>, <code>?</code>, or <code>{}</code>, makes the
          quantifier non-greedy (matching the minimum number of times), as
          opposed to the default, which is greedy (matching the maximum number
          of times).

        <code>x{n}</code>

          Where "n" is a non-negative integer, matches exactly "n" occurrences of
          the preceding item "x". For example, <code>/a{2}/</code> doesn't match
          the "a" in "candy", but it matches all of the "a"'s in "caandy", and
          the first two "a"'s in "caaandy".

        <code>x{n,}</code>

          Where "n" is a non-negative integer, matches at least "n" occurrences of
          the preceding item "x". For example, <code>/a{2,}/</code> doesn't
          match the "a" in "candy", but matches all of the a's in "caandy" and
          in "caaaaaaandy".

        <code>x{n,m}</code>

          Where "n" and "m" are non-negative integers and <code>m >= n</code>,
          matches at least "n" and at most "m" occurrences of the preceding
          item "x". For example, <code>/a{1,3}/</code> matches nothing in
          "cndy", the "a" in "candy", the two "a"'s in "caandy", and the first
          three "a"'s in "caaaaaaandy". Notice that when matching "caaaaaaandy",
          the match is "aaa", even though the original string had more "a"s in
          it.

          <code>x*?</code><code>x+?</code><code
            >x??</code
          ><code>x{n}?</code><code>x{n,}?</code
          ><code>x{n,m}?</code>

          By default quantifiers like <code>*</code> and <code>+</code> are
          "greedy", meaning that they try to match as many times as
          possible. The <code>?</code> character after the quantifier makes the
          quantifier "non-greedy": meaning that it will stop as soon as it finds the minimum number of matches. For example, given a string like "some <foo> <bar>
          new </bar> </foo> thing":

            <code>/<.*>/</code> will match "<foo> <bar> new
            </bar> </foo>"

          <code>/<.*?>/</code> will match "<foo>"

            Note: Adding <code>?</code> after <code>{n}</code> is syntactically valid but practically useless.
            Since <code>{n}</code> always matches exactly n times, <code>x{n}?</code> behaves the same as <code>x{n}</code>.
