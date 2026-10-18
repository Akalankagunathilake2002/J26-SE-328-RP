<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/design-tokens/spacing-units/ -->
# Spacing units

USWDS spacing unit tokens are based on multiples of 8px, with additional tokens for small sizes, named tokens for large sizes, and a more limited selection of negative tokens.

Any spacing value in utilities or component CSS should use the following spacing unit tokens, based on multiples of 8px. The documentation below displays a target value in pixels, but the final output for tokens above `2px` and below `-2px` is the eqivalent value in `rem`, which will vary depending on your project settings.

**Note:** Some units tokens come in two flavors: a **numeric token** (like `0.5` or `-2`) and a **string token** (like `'05'` or `'neg-2'`). _Utility classes use unquoted string tokens exclusively when they exist_ (like `.margin-x-neg-2`). Mixins and functions usually accept either, and we will note any exceptions.

## Spacing unit tokens

        Token
        Multiple
        Value
        Example

                <code></code>,

                <code></code>,

                <code></code>

                <code>''</code>

              —

## Using spacing unit tokens
Your context and coding style determine how you access USWDS spacing unit tokens in code.

Many mixins and utilities accept spacing unit tokens. See the utilities section for more on individual utilities and their matching mixins. We show only a few representative examples below.

        Context
        Usage
        Example

          function

            units(units)

            padding-top: units(<code>3</code>);
            margin-left: units(<code>-2px</code>);
            border-radius: units(<code>0.5</code>);
            min-height: units(<code>'card'</code>);

            mixin
            min-width media query

            at-media(units)

            @include at-media(<code>'mobile-lg'</code>)

            mixin
            max-width media query

            at-media-max(units)

            @include at-media-max(<code>'mobile-lg'</code>)

          setting

            units

            $theme-site-margin-mobile: <code>2</code>

            utility

            .padding-x-units
            .margin-x-units

            .padding-x-<code>2</code>
            .margin-x-<code>neg-2</code>
