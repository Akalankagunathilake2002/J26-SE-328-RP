<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/design-tokens/typesetting/line-height/ -->
# Line height

USWDS has 6 normalized line height tokens to control the amount of space between lines in a block of text.

Please see the Typesetting section for more about font size normalization and how USWDS uses tokens for typesetting. Setting line height requires both a line height token and a family token. The documentation below displays a "target line-height" rather than the final output, which will be normalized depending on the targeted font family.

## Line height tokens

        Token
        Example
        Usage
        Output

                <code class="text-no-wrap"></code>

                <code class="text-no-wrap">''</code>

            In compliance with the request of a friend of mine, who wrote me from the East, I called on good-natured, garrulous old Simon Wheeler, and inquired after my friend's friend, Leonidas W. Smiley, as requested to do, and I hereunto append the result.

            usage:

## Using line height tokens
Your context and coding style determine how you access USWDS line height tokens in code.

**Note:** Because line height is affected by font size normalization all letter spacing tokens also require a family token.

        Context
        Usage
        Example

          function

            line-height(family, line-height)
            lh(family, line-height)

            line-height: line-height(<code>'heading'</code>, <code>2</code>);
            line-height: lh(<code>'heading'</code>, <code>2</code>);

            mixin

            u-line-height(family, line-height)

            @include u-line-height(<code>'body'</code>, <code>6</code>)

          setting

            line-height

            $theme-heading-line-height: <code>2</code>

            utility

            .line-height-family-line height

            .line-height-<code>sans</code>-<code>3</code>
