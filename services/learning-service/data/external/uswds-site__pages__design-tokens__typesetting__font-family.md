<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/design-tokens/typesetting/font-family/ -->
# Font family

USWDS font family tokens allow designers and developers to set font family either by the type of font or the role the font plays in the design.

ol ol {
    list-style: lower-roman;
  }

Please see the Typesetting section for more about font size normalization and how USWDS uses `size` and `family` tokens for typesetting.

## Available fonts
The following fonts have normalization metadata in USWDS, and are available to settings variables as tokens:

        Token
        Value

                <code class="text-no-wrap"></code>

                <code class="text-no-wrap">''</code>

              "",

## Type-based tokens
Type based tokens set the font family value based on the _type_ of the requested font: **icon**, **language**, **monospaced**, **sans-serif**, **serif**, and **condensed** families.

        Token
        Default
        Settings variable

                <code class="text-no-wrap"></code>

                <code class="text-no-wrap">''</code>

                ''

                false

              $theme-font-type-

## Role-based tokens
Role-based tokens set the font family value based on the _role_ the face plays in the project: **heading**, **body**, **ui**, **code**, and **alternate**.

        Token
        Default
        Settings variable

                <code class="text-no-wrap"></code>

                <code class="text-no-wrap">''</code>

                ''

                false

              $theme-font-role-

## Customizing family tokens
Customize the values of type and role family tokens with available font tokens in your project's settings configuration.

**First, use font tokens to define the $theme-font-type- settings variables.**  These settings define the value of the type family tokens. Set any unused types to `false`.

```sass
@use "uswds-core" with (
  $theme-font-type-cond:   false,
  $theme-font-type-icon:   false,
  $theme-font-type-lang:   false,
  $theme-font-type-mono:   'roboto-mono',
  $theme-font-type-sans:   'source-sans-pro',
  $theme-font-type-serif:  'merriweather',
);
```

**Then use the type tokens you just set to define the $theme-font-role- settings variables.** These settings define the value of the role family tokens. Set any unused types to `false`.

```sass
@use "uswds-core" with (
  $theme-font-role-ui:       'sans',
  $theme-font-role-heading:  'serif',
  $theme-font-role-body:     'sans',
  $theme-font-role-code:     'mono',
  $theme-font-role-alt:      'serif',
);
```

## Using family tokens
Your context and coding style determine how you access USWDS family tokens in code.

    Context
    Usage
    Example

    function

    family(family)
    font-family: family(<code>'body'</code>);

      mixin
      font-family

    u-font-family(family)
    @include u-font-family(<code>'sans'</code>)

      mixin
      font-family
      font-size

    u-font(family, size)
    @include u-font(<code>'body'</code>, <code>'2xl'</code>)

    setting
    family
    $theme-prose-font-family: <code>'body'</code>;

    utility
      font-family

    .font-family-family
    .font-family-<code>body</code>

    utility
      font-family
      font-size

    .font-family-size
    .font-<code>body</code>-<code>2xl</code>

## Adding fonts to USWDS

If you need to use a font that isn’t included in USWDS Available Fonts, you can add a new font to your USWDS project. There are two typical scenarios for this:

1. Adding a font from a hosting service
1. Adding a self-hosted font

### Adding a font from a hosting service

If you’re importing a font from an open source font web directory, the steps will generally look like this:

1. In your HTML files, add a reference to the JavaScript and/or CSS files provided by the font hosting service.

### Adding a self-hosted font
If you want to add a font that will be hosted in your project, you’ll need to:

1. Copy font files into your fonts directory
1. Configure `$theme-font-[font type]-custom-src` to:
    1. Tell the system where to find your font files
    1. Specify which font weights you want the system to use
    1. Declare the file name for each font weight

    In the code example, we tell the Design System to look in the `lato` font directory to create `@font-face` rules for the following font files: `Lato-Regular.ttf`, `Lato-Bold.ttf`,`Lato-Italic.ttf`, and `Lato-BoldItalic.ttf`.

    ```sass
    $theme-font-serif-custom-src: (
      dir: "lato", // the name of your font family directory
      roman: (
        100: false,
        200: false,
        300: false,
        400: "Lato-Regular", // the font file name, without the extension
        500: false,
        600: false,
        700: "Lato-Bold",
        800: false,
        900: false,
      ),
      italic: (
        100: false,
        200: false,
        300: false,
        400: "Lato-Bold",
        500: false,
        600: false,
        700: "Lato-BoldItalic",
        800: false,
        900: false,
      ),
    ),
    ```

**Note:** It is possible to add **custom font metadata** in your USWDS settings. See the inline documentation in _settings-typography.scss for more details.
