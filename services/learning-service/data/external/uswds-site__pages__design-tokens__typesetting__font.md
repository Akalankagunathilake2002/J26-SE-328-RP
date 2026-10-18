<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/design-tokens/typesetting/font/ -->
# Font

USWDS font tokens combine our font-family and font-size tokens into a single token that sets the font size and family together. Since USWDS font size is customized to specific font families, it’s often best to typeset them together using a font token.

The USWDS typescale is designed to display type at a consistent size regardless of the typeface. Theme font tokens use a nine-step scale drawn from a 21-step system scale. Theme and system font tokens are the only tokens we accept for setting set font family and size in official components.

Font size is output in `rem`. If you have `$theme-respect-user-font-size` set to `true` in your theme settings, the root font size is set to `100%` and typescale is calculated based on `16px`. If `$theme-respect-user-font-size` set to `false`, the root font size is set to the value of `$theme-root-font-size` and typescale is calculated based on that root.

Since both the `rem` and absolute `px` values change depending on the theme settings and the typeface, the following table displays only the `px` value of the target.

## Font normalization
To make different typefaces appear the same size at each step of the scale, the absolute size of each step in the typescale varies from typeface to typeface. Each supported typeface is regularized to a target value set by the the size of common system fonts — specifically Apple's typeface San Francisco and  Google's typeface Roboto. Optically smaller faces like Source Sans Pro will have a relatively larger rem value at each step in the scale, and optically larger faces like Merriweather will have a relatively smaller rem value. The USWDS typeface Public Sans is developed to be optically similar to system fonts.

## Theme typescale
The nine-step theme scale should be sufficient for most project needs. First, try to use the theme scale. If your projects needs require more than nine sizes, use steps from the system scale as needed.

  token
  system scale
  px
  example
  example utility

  <code>'3xs'</code>
  1
  12px

    Tallahassee

  <code>font-sans-3xs</code>

  <code>'2xs'</code>
  3
  14px

    Tallahassee

  <code>font-lang-2xs</code>

  <code>'xs'</code>
  5
  16px

    Tallahassee

  <code>font-sans-xs</code>

  <code>'sm'</code>
  6
  17px

    Tallahassee

  <code>font-lang-4</code>

  <code>'md'</code>
  7
  18px

    Tallahassee

  <code>font-sans-md</code>

  <code>'lg'</code>
  10
  24px

    Tallahassee

  <code>font-sans-lg</code>

  <code>'xl'</code>
  12
  32px

    Tallahassee

  <code>font-sans-xl</code>

  <code>'2xl'</code>
  14
  40px

    Tallahassee

  <code>font-sans-2xl</code>

  <code>'3xl'</code>
  16
  56px

    Utica

  <code>font-sans-3xl</code>

## System typescale

  token
  px
  example
  example utility

  <code>'micro'</code>
  10px

    Tallahassee

  <code>font-sans-micro</code>

  <code>1</code>
  12px

    Tallahassee

  <code>font-sans-1</code>

  <code>2</code>
  13px

    Tallahassee

  <code>font-sans-2</code>

  <code>3</code>
  14px

    Tallahassee

  <code>font-sans-3</code>

  <code>4</code>
  15px

    Tallahassee

  <code>font-sans-4</code>

  <code>5</code>
  16px

    Tallahassee

  <code>font-sans-5</code>

  <code>6</code>
  17px

    Tallahassee

  <code>font-sans-6</code>

  <code>7</code>
  18px

    Tallahassee

  <code>font-sans-7</code>

  <code>8</code>
  20px

    Tallahassee

  <code>font-sans-8</code>

  <code>9</code>
  22px

    Tallahassee

  <code>font-sans-9</code>

  <code>10</code>
  24px

    Tallahassee

  <code>font-sans-10</code>

  <code>11</code>
  28px

    Tallahassee

  <code>font-sans-11</code>

  <code>12</code>
  32px

    Tallahassee

  <code>font-sans-12</code>

  <code>13</code>
  36px

    Tallahassee

  <code>font-sans-13</code>

  <code>14</code>
  40px

    Tallahassee

  <code>font-sans-14</code>

  <code>15</code>
  48px

    Tallahassee

  <code>font-sans-15</code>

  <code>16</code>
  56px

    Tallahassee

  <code>font-sans-16</code>

  <code>17</code>
  64px

    Tallahassee

  <code>font-sans-17</code>

  <code>18</code>
  80px

    Utica

  <code>font-sans-18</code>

  <code>19</code>
  120px

    Utica

  <code>font-sans-19</code>

  <code>20</code>
  140px

    Utica

  <code>font-sans-20</code>

## Setting theme typeface families
Since typescale is tied to the specific typeface, any technique that directly outputs a specific size must use both a typescale token and a type family token. Type family tokens are set with variables in your project's theme settings.

The following typefaces have been regularized and are available in settings to the type-based settings variables:

  token
  font stack

  <code>'system'</code>
  -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'

  <code>'public-sans'</code>
  'Public Sans Web', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'

  <code>'source-sans-pro'</code>
  'Source Sans Pro','Helvetica Neue', 'Helvetica', 'Roboto', 'Arial', sans-serif

  <code>'helvetica'</code>
  'Helvetica Neue', 'Helvetica', 'Roboto', 'Arial', sans-serif

  <code>'georgia'</code>
  'Georgia', 'Cambria', 'Times New Roman', 'Times', serif

  <code>'merriweather'</code>
  'Merriweather Web', 'Georgia', 'Cambria', 'Times New Roman', 'Times', serif

  <code>'roboto-mono'</code>
  'Roboto Mono Web', 'Bitstream Vera Sans Mono', 'Consolas', 'Courier', monospace

  <code>'tahoma'</code>
  'Tahoma', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'

### Type-based family tokens
Each project can choose a family from the available typefaces for monospaced, sans-serif, serif, and condensed families. The value of any of these families can be set to `false` if that family isn't used in your project.

  token
  description
  settings variable

  <code>'mono'</code>
  project monospace typeface
  $theme-font-mono

  <code>'sans'</code>
  project sans-serif typeface
  $theme-font-sans

  <code>'serif'</code>
  project serif typeface
  $theme-font-serif

  <code>'cond'</code>
  project condensed typeface
  $theme-font-cond

```
$theme-font-mono:   'roboto-mono';
$theme-font-sans:   'source-sans-pro';
$theme-font-serif:  'merriweather';
$theme-font-cond:   false;
```

### Role-based family tokens
Next, set role-based tokens with the type-based theme variables.

  token
  description
  settings variable

  <code>'heading'</code>
  project heading typeface
  $theme-font-heading

  <code>'body'</code>
  project body typeface
  $theme-font-body

  <code>'code'</code>
  project code typeface
  $theme-font-code

  <code>'alt'</code>
  alternate project typeface
  $theme-font-alt

```
$theme-font-heading:  $theme-font-serif;
$theme-font-ui:       $theme-font-serif;
$theme-font-body:     $theme-font-sans;
$theme-font-code:     $theme-font-mono;
$theme-font-alt:      $theme-font-sans;
```

## Using typescale in utilities, settings, and component Sass
You'll access USWDS typecale units using a few different techniques, depending on your situation and coding style.

### Settings

Use the scale token when assigning a typescale unit to a settings variable.

```
$theme-type-scale-3xs:      1;
$theme-type-scale-2xs:      3;
$theme-type-scale-xs:       5;
$theme-type-scale-sm:       6;
$theme-type-scale-md:       7;
$theme-type-scale-lg:       10;
$theme-type-scale-xl:       12;
$theme-type-scale-2xl:      14;
$theme-type-scale-3xl:      16;
$theme-h1-font-size:        '2xl';
```

### Utilities

The `font` utility requires both an unquoted family token and an unquoted scale token in the form `font-[family]-[size]`.

_The `font` utilities set both the font size and family._

```
.font-sans-3xs
.font-body-md
.font-sans-micro
.font-mono-sm
```

### Functions

Use the `font-size()` function to set the font size. The function requires both a  family token and a scale token in the form `font-size([family], [scale])`.

_The `scale()` function is only for font-size._

```
font-size: font-size('mono', 'sm');
font-size: font-size('body', 8);
```

### Utility mixins

Use the `u-font()` mixin to set both the font size and the font family. The mixin requires both a family token and a scale token in the form `@include u-font([family], [scale])`.

Use the `u-font-size()` mixin to set the font size only. The mixin requires both a  family token and a scale token in the form `@include u-font-size([family], [scale])`.

Use the `u-font-family()` mixin to set the font family only. The mixin requires a  family token in the form `@include u-font-family([family])`.

_Use `u-font()` instead of using both `u-font-family()` and `u-font-size()` on a single selector, but avoid using it unneccessarily to avoid duplicate code._

```
@include u-font('heading', 'xl')

@include u-font-family('sans')
@include u-font-size('sans', 12)

@include u-font-family('body')
@include u-font-size('body', 'sm')
```
