<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/design-tokens/typesetting/overview/ -->
# Using type

Typesetting in USWDS means understanding the relationship between font family, font size, and line height.

## Normalization
Typefaces vary in optical size. This means that at any specific pixel value, an optically small typeface like Source Sans Pro will appear smaller than an optically large typeface like Merriweather. Optical size is a function of internal font metrics and typeface design choices like x-height.

### Fonts at native size

USWDS 3 is designed so each size token outputs a consistent optical size regardless of the typeface. This makes our guidance more reliable and our theming more flexible.

### Fonts with normalization applied

To make different typefaces appear the same size (here called the _target size_) at each step of the scale (below, we see the output of size token `10`), the absolute size of each token's output varies depending on the font family.

Each supported typeface is normalized to a target value determined by the optical size of common system fonts — specifically Apple's typeface San Francisco and Google's typeface Roboto.

    For size token <code>10</code> (24px) we see the following normalized ouput:

        Supported typeface
        Normalization
        Final output (px)

### Rem-based font sizing
In USWDS, the final font size is output not in pixels but in `rem` (a multiple of the page's root font size). If you have `$theme-respect-user-font-size` set to `true` in your theme settings, the root font size is set to `100%` and typescale is calculated based on `16px`. If `$theme-respect-user-font-size` set to `false`, the root font size is set to the value of `$theme-root-font-size` and typescale is calculated based on that root.

Since both the `rem` and absolute `px` values change depending on the theme settings and the typeface, our documentation displays only the `px` value of the target.

### Normalization and line height
USWDS has six target line heights in its line-height token system. These targets are unitless numbers, multipliers of the font size of the affected text. For example, if the target line height were `2` in text with a target font size of `16px`, the final line height would be the `target line height * target font size` or `2 * 16px` or `32px`.

Since we use normalization on font sizing, we must also normalize line height to hit the target line height:

    For size token <code>10</code> (24px) and line-height token <code>3</code> ( / px) we see the following normalized ouput:

        Supported typeface
        Normalization
        Final size (px)
        Final line height
        Final line height (px)

## Typesetting with tokens
USWDS uses **functions**, **mixins**, and **utility classes** to style its components with design tokens. Because we use normalized values, as described above, font size and line height functions, mixins, and utility classes differ from many others in the system by requiring _two_ tokens: a family token and either a size or a line-height token.

The individual design token sections go into this in more detail, but here's a summary:

### Font family

        Token
        Function
        Mixin
        Utility class

            family

            family(family)

            u-font-family(family)

            .font-family-family

            'body'

            family('body')

            u-font-family('body')

            .font-family-body

            'sans'

            family('sans')

            u-font-family('sans')

            .font-family-sans

### Font size

        Token
        Function
        Mixin
        Utility class

            family, size

            size(family, size)

            u-font-size(family, size)

            .font-size-family-size

            'ui', 'micro'

            size('ui', 'micro')

            u-font-size('ui', 'micro')

            —

            'sans', 6

            size('sans', 6)

            u-font-size('sans', 6)

            —

### Family and size together

        Token
        Function
        Mixin
        Utility class

            family, size

            —

            u-font(family, size)

            .font-family-size

            'ui', 'micro'

            —

            u-font('ui', 'micro')

            .font-ui-micro

            'sans', 6

            —

            u-font('sans', 6)

            .font-sans-6

### Line height

        Token
        Function
        Mixin
        Utility class

            family, line-height

            line-height(family, line-height)

            u-line-height(family, line-height)

            .line-height-family-line-height

            'ui', 1

            line-height('ui', 1)

            u-line-height('ui', 1)

            line-height-ui-1

            'sans', 3

            line-height('sans', 3)

            u-line-height('sans', 3)

            .line-height-sans-3

### Family, size, and line height together
The `typeset()` mixin allows you to set family, size, and line height all in one line. It accepts the tokens listed as well as a special `null` value. If either of the three properties get `null` instead of a token, the system will use a default value from typography settings: either `$theme-body-font-family`, `$theme-body-font-size`, or `$theme-body-line-height` depending on the property passed the `null` value.

We use the `typeset()` mixin on all our components to get the effect of default `` element styling without having to explicitly style the `` element.

        Token
        Function
        Mixin
        Utility class

            family, size, line-height

            —

            typeset(family, size, line-height)

            —

            'ui', 'micro', 1

            —

            typeset('ui', 'micro', 1)

            —

            'ui', null, 3

            —

            typeset('ui', null, 3)

            —

            'ui', xs, null

            —

            typeset('ui', xs)

            —

            'ui', null, null

            —

            typeset('ui')

            —

See this example:

#### Example: Settings and typesetting

```scss
// In your settings configuration:

@use "uswds-core" with (
  $theme-respect-user-font-size: true,
  $theme-font-type-sans: "public-sans",
  $theme-font-role-ui: "sans",
  $theme-type-scale-sm: 5,
  $theme-body-font-size: "sm",
  $theme-body-line-height: 5
);

// in component code:

.usa-component {
  @include typeset('ui');
}

// is the equivalent of:

.usa-component {
  font-family: family('ui');
  font-size: size('ui', $theme-body-font-size);
  line-height: line-height('ui', $theme-body-line-height);
}

// compiles as:

.usa-component {
  font-family: 'Public Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';
  font-size: 1rem;
  line-height: 1.62;
}

```
