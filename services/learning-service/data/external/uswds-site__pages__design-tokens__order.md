<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/design-tokens/order/ -->
# Order

Use order tokens to set the order of an item in a flex container.

## Order tokens

    Note: Ordered items are only ordered among other ordered items. Any unordered siblings will be ordered by their appearance in the DOM. Siblings sharing the same order will all appear at the specified position in the order in which they appear in the DOM.

        Token
        Example
        Value

                <code></code>,

                <code></code>

                <code>''</code>

                1

                2

                3

                4

                5

                6

                7

                8

                9

                10

                11

## Using order tokens
Your context and coding style determine how you access USWDS order tokens in code.

        Context
        Usage
        Example

          function

            order(order)

            order: order(<code>'last'</code>)

            mixin

            u-order(order)

            @include u-order(<code>'last'</code>)

            setting

            order

            $theme-nav-item-order: <code>'last'</code>

            utility

            .order-order

            .order-<code>last</code>
