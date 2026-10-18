<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/design-tokens/typesetting/font-size/ -->
# Font size

Font size tokens determine how big or small the referenced text will appear on the screen. The USWDS typescale includes nine regularized theme tokens drawn from 21 system tokens.

Please see the Typesetting section for more about font size normalization and how USWDS uses tokens for typesetting. The documentation below displays a value in pixels, rather than the actual final output, which will be normalized depending on the typeface and output in `rem` customized to your project settings.

## Theme tokens
The following chart shows the USWDS default settings for the nine theme size tokens. Customize the output to your project needs in USWDS settings configuration  by setting the variables listed in the default settings chart. If your project requires more than nine sizes, use system size tokens as needed.

        Token
        Default
        Example
        Value
        Settings variable

                <code class="text-no-wrap"></code>

                <code class="text-no-wrap">''</code>

              <code></code>

              Tallahassee

              $theme-type-scale-

## System tokens

        Token
        Value
        Example

                <code class="text-no-wrap"></code>

                <code class="text-no-wrap">''</code>

              Tallahassee

## Using size tokens
Your context and coding style determine how you access USWDS font size tokens in code. Because of font size normalization, font size functions, utilities, and mixins also require a family token.

        Context
        Usage
        Example

            function

            size(family, size)

            font-size: size(<code>'body'</code>, <code>'2xl'</code>)

            mixin
            font-size

            u-font-size(family, size)

            @include u-font-size(<code>'body'</code>, <code>'2xl'</code>)

            mixin
            font-family
            font-size

            u-font(family, size)

            @include u-font(<code>'body'</code>, <code>'2xl'</code>)

            setting

            size

          $theme-h1-font-size: <code>'2xl'</code>

            utility
            font-family
            font-size

            .font-family-size

            .font-<code>body</code>-<code>2xl</code>
