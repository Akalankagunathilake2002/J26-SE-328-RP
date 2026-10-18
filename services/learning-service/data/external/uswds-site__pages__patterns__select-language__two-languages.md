<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/patterns/select-a-language/two-languages/ -->
# Two languages

This pattern helps users, especially those with limited English proficiency, select their preferred language when visiting a website in two languages, like English and Spanish.

## About this pattern

### What problem does this solve?

Inconsistent placement and language selection interface components can be a barrier to users with limited English-language skills, preventing them from easily finding and accessing content in another language.

### When to use this pattern

Use this pattern when the content is available in two languages.

### When to consider something else

- When content is available in three or more languages, see the Select from three or more languages pattern.
- When only selected multilingual content is available in some languages, see the Selected content available pattern.

### What's the solution?

Place the language selector button at the top of the screen above site navigation to allow the user to toggle between two languages. Place the toggle on the top right of the page for left-to-right-languages and on the top left of the page for right-to-left languages, if possible.

## Guidance

          What to do

            Place the language menu button in the upper corner of the screen for consistency. If possible, flip the arrangement of the header for right-to-left languages. The language button should be positioned at the top right of the page for left-to-right languages and on the top left for right-to-left languages.
            Make the language access button a single, independent element.
            Include the language toggle in the header so that it remains visible and in the same position as the user scrolls up and down a webpage if the website has a “sticky” or “fixed” header.
            Take users to an equivalent page that includes the same or similar content.
            Capitalize the name of each language (for example, English, Español).
            Strongly consider labeling the name in the common, native language like Español (Spanish) or 简体字 (Chinese - Simplified).

          What not to do

            Do not create a dead end for users by taking them to a page with little or no meaningful content.
            Strongly consider whether including icons or graphics on the language selection button offers communication value, as these may represent different concepts to different cultures.
            Do not use flags or country codes to indicate languages. Flags do not map to languages; Arabic, for example, is spoken in many countries. The country code <code>ES</code> may not be universally understood to indicate Spanish.
            Avoid auto-redirecting language based on detecting location or browser settings. This can be confusing and disorienting.
            Do not combine this element with other navigation items.

      Pattern preview

      Pattern code

### Usability guidance

- **Ensure there’s enough color contrast** between the button, the text inside the button, and the site background to ensure readability.

### Accessibility

- **Customization.** As you customize, make sure you follow accessibility guidelines for buttons.
- If the text will be visually presented as a button but coded as a link, it is recommended to **add ARIA role="button"** so that screen readers announce it as a button. Additionally, JavaScript will also need to be added so that keyboard users can activate the button using both the Enter and Spacebar keys. See Understanding Success Criterion 4.1.2 - Understanding WCAG 2.0 for more information.
- **Use the HTML `lang` attributes** to set the language of the page (``, for example). See H57: Using the language attribute on the HTML element for more information.
- Consider including a **prominent in-page notice or link** in addition to the link in the header, in order to increase visibility for the user.

## See pattern in use

- USA.gov

## Related components, patterns, and templates

- Button component
- Header component
- Language selector component
- Find selected multilingual content pattern
- Select from three or more languages pattern

## References

- Community research explores ways to improve access to multilingual content. (August 9, 2022) Retrieved on August 24, 2022, from
- Designing a perfect language selector UX. (May 4, 2022) Retrieved on July 21, 2022, from
- Flag problems. (August 1, 1996) Retrieved on July 22, 2022, from
- Top 10 Best practices for multilingual websites. (June 21, 2022) Retrieved on July 21, 2022, from
- White paper on best practices for multilingual access to digital libraries. (June 23, 2016) Retrieved on July 21, 2022, from

## Disclaimer

Links to nongovernment sources are made for educational or source citation purposes only, and do not represent an endorsement of the organizations by the General Services Administration. The General Services Administration does not assume any responsibility for the content, operation, or policies of other entities' websites.
