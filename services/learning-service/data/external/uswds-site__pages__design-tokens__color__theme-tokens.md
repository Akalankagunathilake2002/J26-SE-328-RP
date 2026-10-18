<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/design-tokens/color/theme-tokens/ -->
# Theme color tokens

USWDS theme color tokens provide flexible, accessible, customizable color choices for your project.

USWDS theme color tokens are designed to be useful and effective for small and large projects.  Each theme token is drawn from a system color token and we only use token-based colors in official components.

## About theme color tokens
USWDS theme color tokens are divided into five high-level role-based color families: `base`, `primary`, `secondary`, `accent-warm`, and `accent-cool`.

**Base** is a project's neutral color, typically some tint of gray, and usually used as the text color throughout.

**Primary**, **secondary**, and **accent** colors can be thought of as falling into a proportional 60/30/10 relationship: about 60% of your site’s color would be the primary color family, about 30% would be the secondary color family, and about 10% would be the accent color families (`accent-warm` and `accent-cool`). Note that these proportions are for non-base colors. In many cases, the neutral base text color will be the predominant tone on your site.

Each color family has seven possible lightness grades, from `lightest` to `darkest`, though not every family needs to include a color at each grade. Some grades may be set to `false` in your project's theme settings. The default USWDS theme palette does not use every grade for every family. The `primary` and `secondary` families also have a `vivid` grade available.

## Theme color tokens table

        Color
        Token
        Default
        Settings variable
        Value

            ''

            ''

            $theme-color-

## Using theme color tokens
Your context and coding style determine how you access USWDS theme color tokens in code.

For example, all three of the following examples result in the same output:

```
// function
div {
  background-color: color("primary");
}

// mixin
div {
  @include u-bg("primary");
}

// utility
...

```

        Context
        Usage
        Example

          function

            color(color)

            color: color(<code>'primary-vivid'</code>)

            mixin
            background-color

            u-bg(color)

            @include u-bg(<code>'primary-vivid'</code>)

            mixin
            color

            u-text(color)

            @include u-text(<code>'primary-vivid'</code>)

            mixin
            border-color

            u-border(color)

            @include u-border(<code>'primary-vivid'</code>)

            mixin
            text-decoration-color

            u-underline(color)

            @include u-underline(<code>'primary-vivid'</code>)

            setting

            color

            $theme-link-color: <code>'primary-vivid'</code>

            utility
            background-color

            .bg-color

            .bg-<code>base-lighter</code>

            utility
            border-color

            .border-color

            .border-<code>primary</code>

            utility
            color

            .text-color

            .text-<code>primary</code>

            utility
            outline-color

            .outline-color

            .outline-<code>primary</code>

            utility
            text-decoration-color

            .underline-color

            .underline-<code>primary-vivid</code>
