<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/design-tokens/typesetting/measure/ -->
# Measure (line length)

USWDS has 6 measure tokens to control the reading length of lines in a block of text.

## Measure tokens

    Measure is output in <code>ex</code> units, where <code>1ex</code> is equivalent to the height of an 'x' character in the desired font. The first section of each example below is 4 alphabets long.

        Token
        Example
        Value

                <code class="text-no-wrap"></code>

                <code class="text-no-wrap">''</code>

                abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz

                You never see a frog so modest and straightforward as he was, for all he was so gifted. And when it come to fair and square jumping on a dead level, he could get over more ground at one straddle than any animal of his breed you ever see. Jumping on a dead level was his strong suit, you understand; and when it come to that, Smiley would ante up money on him as long as he had a red. Smiley was monstrous proud of his frog, and well he might be, for fellers that had traveled and been everywheres, all said he laid over any frog that ever they see.

## Using measure tokens
Your context and coding style determine how you access USWDS measure tokens in code.

        Context
        Usage
        Example

          function

            measure(measure)

            max-width: measure(<code>3</code>)

            mixin

            u-measure(measure)

            @include u-measure(<code>'none'</code>)

          setting

            measure

            $theme-text-measure: <code>5</code>

            utility

            .measure-measure

            .measure-<code>3</code>
