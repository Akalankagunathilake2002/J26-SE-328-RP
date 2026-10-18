<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/design-tokens/color/system-tokens/ -->
# System color tokens

USWDS system color tokens are the complete palette of color tokens from which any project can build a theme palette.

vivid

            Color
            Token
            Family
            Grade
            Variant
            Hex

## Using color tokens
Your context and coding style determine how you access USWDS color tokens in code.

        Context
        Usage
        Example

          function

            color: color(color)

            color: color(<code>'gray-30'</code>)

            mixin
            background-color

            @include u-bg(color)

            @include u-bg(<code>'gray-30'</code>)

            mixin
            color

            @include u-text(color)

            @include u-text(<code>'gray-30'</code>)

            mixin
            border-color

            @include u-border(color)

            @include u-border(<code>'gray-30'</code>)

            mixin
            text-decoration-color

            @include u-underline(color)

            @include u-underline(<code>'gray-30'</code>)

            setting

            $theme-variable: color

            $theme-color-disabled: <code>'gray-30'</code>

            utility
            background-color

            .bg-color

            .bg-<code>gray-30</code>

            utility
            border-color

            .border-color

            .border-<code>gray-30</code>

            utility
            color

            .text-color

            .text-<code>gray-30</code>

            utility
            outline-color

            .outline-color

            .outline-<code>gray-30</code>

            utility
            text-decoration-color

            .underline-color

            .underline-<code>gray-30</code>
