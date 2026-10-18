<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/design-tokens/flex/ -->
# Flex

USWDS flex tokens provide simple options for setting the flex width of an item.

## Flex tokens

        Token
        Example
        Value

                <code></code>,

                <code></code>

                <code>''</code>

## Using flex tokens
Your context and coding style determine how you access USWDS flex tokens in code.

        Context
        Usage
        Example

          function

            flex(flex)

            flex: flex(<code>'fill'</code>)

          mixin

            u-flex(flex)

            @include u-flex(<code>'fill'</code>)

          setting

            flex

            $theme-nav-column-flex: <code>4</code>

            utility

            .flex-flex

            .flex-<code>fill</code>
