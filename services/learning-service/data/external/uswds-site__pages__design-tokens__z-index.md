<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/design-tokens/z-index/ -->
# Z-index

Z-index tokens determine an item's position in the stacking order.

## Z-index tokens

      Token
      Value

        <code class="">'auto'</code>
        auto

        <code class="">'top'</code>
        99999

        <code class="">500</code>
        500

        <code class="">400</code>
        400

        <code class="bg-white">300</code>
        300

        <code class="bg-white">200</code>
        200

        <code class="bg-white">100</code>
        100

        <code class="bg-white">0</code>
        0

        <code class="bg-white">'bottom'</code>
        -100

## Using z-index tokens
Your context and coding style determine how you access USWDS z-index tokens in code.

        Context
        Usage
        Example

          function

            z-index(z-index)
            z(z-index)

            z-index: z-index(<code>'bottom'</code>)
            z-index: z(<code>'bottom'</code>)

            mixin

            u-z(z-index)

            @include u-z(<code>'bottom'</code>)

          setting

            z-index

            $theme-subnav-z-index: <code>'top'</code>

            utility

            .z-z-index

            .z-<code>top</code>
