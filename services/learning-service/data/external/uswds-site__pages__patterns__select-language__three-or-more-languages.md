<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/patterns/select-a-language/three-or-more-languages/ -->
# Three or more languages

This pattern helps users, especially those with limited English proficiency, select their preferred language when visiting a website available in three or more languages, like English, Spanish, and Arabic.

## About this pattern

### What problem does this solve?

Inconsistent placement and treatment of language selection interface components can be a barrier to users, especially those with limited English-language skills, preventing them from easily finding and accessing content in other languages.

### When to use this pattern

Use this pattern when the content is available in three or more languages and all content is available in each language.

### When to consider something else

When content is available in only two languages, see the Select from two languages pattern. When only selected multilingual content is available in some languages, see the Selected content available pattern.

### What's the solution?

Place the language selector menu at the top of the screen above site navigation, allowing site visitors to use a dropdown menu to select their language of choice. Place the language selector on the top right for left-to-right languages and on the top left for right-to-left languages if possible.

## Guidance

          What to do

            Place the language menu button in the upper corner of the screen for consistency. If possible, flip the arrangement of the header for right-to-left languages. The language button should be positioned at the top right of the page for left-to-right languages and on the top left for right-to-left languages.
            Make the language access button a single, independent element.
            Include the language dropdown in the header so that it remains visible and in the same position as the user scrolls up and down a webpage if the website has a “sticky” or “fixed” header.
            Take users to an equivalent page that includes the same or similar content.
            Label the dropdown menu <code>Languages</code>.
            Capitalize the name of each language (for example, English, Español).
            Do order the languages alphabetically by the common, native language name. For example:
            العربية (Arabic)
            简体字 (Chinese - Simplified)
            English
            Español (Spanish)
            Français (French)
            Italiano (Italian)
            Pусский (Russian)

          What not to do

              Do not create a dead end for users by taking them to a page with little or no meaningful content.
              Strongly consider whether including icons or graphics on the language selection button offers communication value, as these may represent different concepts to different cultures.
              Do not use flags or country codes to indicate languages. Flags do not map to languages; Arabic, for example, is spoken in many countries. The country code <code>ES</code> may not be universally understood to indicate Spanish.
              Avoid auto-redirecting language based on detecting location or browser settings. This can be confusing and disorienting.
              Do not combine this element with other navigation items.

      Pattern preview

      Pattern code

### Usability guidance

- Consider including a **prominent in-page notice or link** in addition to the link in the header, in order to increase visibility for the user.
- **Ensure there’s enough color contrast** between the button, the text inside the button, and the site background to ensure readability.

### Accessibility

- If the text will be visually presented as a button but coded as a link, it is recommended to **add ARIA role="button"** so that screen readers announce it as a button. Additionally, JavaScript will also need to be added so that keyboard users can activate the button using both the Enter and Spacebar keys. See Understanding Success Criterion 4.1.2 - Understanding WCAG 2.0 for more information.
- **Use the HTML `lang` attributes** to set the language of the page (``, for example). See H57: Using the language attribute on the HTML element for more information.
- **All logically related items and links** must be presented as an HTML unordered list.

## See pattern in use

- Vote.gov

## Related components, patterns, and templates

- Button component
- Header component
- Language selector component
- Find selected multilingual content pattern
- Select from two languages pattern

## References

- Community research explores ways to improve access to multilingual content. (August 9, 2022) Retrieved on August 24, 2022, from
- Designing a perfect language selector UX. (May 4, 2022) Retrieved on July 21, 2022, from
- Flag problems. (August 1, 1996) Retrieved on July 22, 2022, from
- Top 10 Best practices for multilingual websites. (June 21, 2022) Retrieved on July 21, 2022, from
- White paper on best practices for multilingual access to digital libraries. (June 23, 2016) Retrieved on July 21, 2022, from

## Disclaimer

Links to nongovernment sources are made for educational or source citation purposes only, and do not represent an endorsement of the organizations by the General Services Administration. The General Services Administration does not assume any responsibility for the content, operation, or policies of other entities' websites.
