<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/design-tokens/typesetting/letterspacing/ -->
# Letterspacing

USWDS has 6 letterspacing tokens to control the amount of space between individual letterforms.

**Note:** Some letterspacing tokens come in two flavors: a **numeric token** (like `0.5` or `-2`) and a **string token** (like `'05'` or `'neg-2'`). _Utility classes use string tokens exclusively when they exist_ (like `.margin-x-neg-2`). Mixins and functions usually accept either, and we will note any exceptions.

## Letterspacing tokens

        Token
        Example
        Value

                <code></code>,

                <code></code>

                <code>''</code>

              Tallahassee

## Using letterspacing tokens
Your context and coding style determine how you access USWDS letterspacing tokens in code.

        Context
        Usage
        Example

          function

            letter-spacing(letterspacing)
            ls(letterspacing)

            letter-spacing: letter-spacing(<code>-2</code>);
            letter-spacing: ls(<code>-2</code>);

            mixin

            u-text('ls-letterspacing')

            @include u-text(<code>'ls-neg-2'</code>)

            utility

            .text-ls-letterspacing

            .text-ls-<code>neg-2</code>
