<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/design-tokens/shadow/ -->
# Shadow

Often used to indicate elevation, shadow tokens determine the size of a drop shadow (or `box-shadow`) around an item.

## Shadow tokens
Output values are shown in `px` below but are output in `rem` in the final CSS, based on the base font size in your project settings.

        Token
        Example
        Value

                <code></code>,

                <code></code>

                <code>''</code>

## Using shadow tokens
Your context and coding style determine how you access USWDS shadow tokens in code.

        Context
        Usage
        Example

          function

            shadow(shadow)

            box-shadow: shadow(<code>2</code>)

            mixin

            u-shadow(shadow)

            @include u-shadow(<code>2</code>)

          setting

            shadow

            $theme-subnav-shadow: <code>2</code>

            utility

            .shadow-shadow

            .shadow-<code>2</code>
