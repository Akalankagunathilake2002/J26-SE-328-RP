<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/design-tokens/opacity/ -->
# Opacity

Opacity tokens set the opacity (or transparency) of an item in increments of 10%.

## Opacity tokens

        Token
        Example
        Value

                <code></code>,

                <code></code>

                <code>''</code>

## Using opacity tokens
Your context and coding style determine how you access USWDS opacity tokens in code.

        Context
        Usage
        Example

          function

            opacity(opacity)

            opacity: opacity(<code>10</code>)

            mixin

            u-opacity(opacity)

            @include u-opacity(<code>10</code>)

          setting

            opacity

            $theme-hover-opacity: <code>50</code>

            utility

            .opacity-opacity

            .opacity-<code>50</code>
