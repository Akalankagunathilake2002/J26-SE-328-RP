<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/design-tokens/color/state-tokens/ -->
# State color tokens

USWDS state colors tokens provide flexible, accessible, customizable colors for warning, error, and other states

USWDS state color tokens are designed to be useful and effective for any project that has states or alerts. Each state token is drawn from a system color token and we only use token-based colors in official components.

## State color tokens
The state color palette is divided into five high-level role-based color families: `info`, `error`, `warning`, `success`, `emergency`, and `disabled`.

Each color family except `emergency` and `disabled` has five possible lightness grades, from `lighter` to `darker`, though not every family needs to include a color at each grade. Some grades may be set to `false` in your project's theme settings.

## State color tokens table

        Color
        Token
        Default
        Settings variable
        Value

            ''

            ''

            $theme-color-

## Using color tokens
Your context and coding style determine how you access USWDS color tokens in code.

        Context
        Usage
        Example

          function

            color(color)

            color: color(<code>'warning-dark'</code>)

            mixin
            background-color

            u-bg(color)

            @include u-bg(<code>'warning-dark'</code>)

            mixin
            color

            u-text(color)

            @include u-text(<code>'warning-dark'</code>)

            mixin
            border-color

            u-border(color)

            @include u-border(<code>'warning-dark'</code>)

            mixin
            text-decoration-color

            u-underline(color)

            @include u-underline(<code>'warning-dark'</code>)

            setting

            color

            $theme-alert-text-color: <code>'warning-dark'</code>

            mixin
            text-decoration-color

            u-underline(color)

            @include u-underline(<code>'warning-dark'</code>)

            utility
            background-color

            .bg-color

            .bg-<code>warning-light</code>

            utility
            border-color

            .border-color

            .border-<code>error</code>

            utility
            color

            .text-color

            .text-<code>error</code>

            utility
            outline-color

            .outline-color

            .outline-<code>error</code>

            utility
            text-decoration-color

            .underline-color

            .underline-<code>error</code>
