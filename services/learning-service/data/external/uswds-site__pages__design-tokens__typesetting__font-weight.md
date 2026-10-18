<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/design-tokens/typesetting/font-weight/ -->
# Font weight

USWDS has up to seven font weight theme tokens drawn from nine system tokens.

## Theme tokens
Font weight theme tokens use common names. Most projects will use only 2-4 of these tokens, with the majority set to `false`.

Customize theme font weight tokens in your project's theme settings with available system font weight tokens. All typography-related settings can be found in USWDS settings.

        Token
        Default
        Example
        Settings variable

                <code class="text-no-wrap"></code>

                <code class="text-no-wrap">''</code>

                false

                Tallahassee

              $theme-font-weight-

## System tokens
Font weight system tokens use numbers from `100`-`900` in increments of 100, with `100` as the lightest and `900` the heaviest, the same numerical system of grades used by most common typefaces.

        Token
        Example

                <code class="text-no-wrap"></code>

                <code class="text-no-wrap">''</code>

              Tallahassee

## Using weight tokens
Your context and coding style determine how you access USWDS font weight tokens in code.

        Context
        Usage
        Example

          function

            font-weight(weight)

            font-weight: font-weight(<code>'bold'</code>)

            mixin

            u-text(weight)

            @include u-text(<code>'light'</code>)

          setting

            weight

            $theme-font-weight-normal: <code>500</code>

            utility

            .text-weight

            .text-<code>light</code>
