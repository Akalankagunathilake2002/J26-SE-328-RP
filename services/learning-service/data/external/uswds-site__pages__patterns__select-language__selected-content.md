<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/patterns/select-a-language/selected-content/ -->
# Selected multilingual content

This pattern helps users, especially those with limited English proficiency, find content in their preferred language when only selected pieces of content have been translated. For example, the site may be available in several languages, but specific information — fact sheets, overviews, videos, instructions — might be available in additional languages.

## About this pattern

### What problem does this solve?

Inconsistent placement of language selection components prevent users, especially people with limited English-language skills, from easily finding and accessing content in other languages. When only select content is available in languages other than English, this problem can be compounded as users are forced to navigate to a specific section of the site to discover the content.

### When to use this pattern

Use this pattern if your site offers a select set of content available in additional languages. Note: while this situation could apply to a single language or two language site, this pattern specifically describes a site with three or more languages as well as a small subset of content that is available in additional languages.

### When to consider something else

If your site is available in two or more languages and all content is available in each language, see related patterns Select from two languages or Select from three or more languages.

### What's the solution?

Place the language selector button at the top right of the screen above site navigation to allow the user to access a dropdown with links to content in other languages.

## Guidance

          What to do

            Place the language menu button in the upper corner of the screen for consistency. If possible, flip the arrangement of the header for right-to-left languages. The language button should be positioned at the top right of the page for left-to-right languages and on the top left for right-to-left languages.
            Make the language access button a single, independent element.
            Include the language dropdown in the header so that it remains visible and in the same position as the user scrolls up and down a webpage if the website has a “sticky” or “fixed” header.
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
            Use a label like "Featured content in additional languages" or "Selected content in additional languages" as the last entry of the menu to link to the landing page for your additional language content.

          What not to do

            Do not create a dead end for users by taking them to a page with little or no meaningful content.
            Strongly consider whether including icons or graphics on the language selection button offers communication value, as these may represent different concepts to different cultures.
            Do not use flags or country codes to indicate languages. Flags do not map to languages; Arabic, for example, is spoken in many countries. The country code <code>ES</code> may not be universally understood to indicate Spanish.
            Avoid auto-redirecting language based on detecting location or browser settings. This can be confusing and disorienting.
            Do not combine this element with other navigation items.

      Pattern preview

      Pattern code

### Considerations

Use this pattern when your site supports three or more languages, but offers a limited amount of content in additional languages. Multilingual sites with select content in additional languages generally take one of two structural approaches:

- **Topic-driven approach.** A landing page is arranged topically, with links to specific content in the larger set of supported languages. This is generally recommended for sites that have rich topical content in a variety of supported languages.
- **Language-driven approach.** A landing page is arranged by language, showcasing the specific additional languages and the content available in that language. This is generally recommended for sites that have a disparate set of content available in additional languages.
- Regardless of how the information is structured, consider providing **prominent in-page notices and links** where appropriate within your site to help surface this additional language content.

### Usability guidance

- **Ensure there’s enough color contrast** between the button, the text inside the button, and the site background to ensure readability.
- Provide a **visual indicator that the text is a link**. For example, permanently underline text or when hovering.

### Accessibility

- **Customization.** As you customize, make sure you follow accessibility guidelines for buttons.
- If the text will be visually presented as a button but coded as a link, it is recommended to **add ARIA role="button" so that screen readers announce it as a button**. Additionally, JavaScript will also need to be added so that keyboard users can activate the button using both the Enter and Spacebar keys. See Understanding Success Criterion 4.1.2 - Understanding WCAG 2.0 for more information.
- **Use the HTML `lang` attributes** to set the language of the page (``, for example). See H57: Using the language attribute on the HTML element for more information.
- All logically related items/links must be presented as an **HTML unordered list**.

## Related components, patterns, and templates

- Header component
- Language selector component
- Select from three or more languages pattern
- Select from two languages pattern

## References

- Community research explores ways to improve access to multilingual content. (August 9, 2022) Retrieved on August 24, 2022, from
- Designing a perfect language selector UX. (May 4, 2022) Retrieved on July 21, 2022, from
- Flag problems. (August 1, 1996) Retrieved on July 22, 2022, from
- Top 10 Best practices for multilingual websites. (June 21, 2022) Retrieved on July 21, 2022, from
- White paper on best practices for multilingual access to digital libraries. (June 23, 2016) Retrieved on July 21, 2022, from

## Disclaimer

Links to nongovernment sources are made for educational or source citation purposes only, and do not represent an endorsement of the organizations by the General Services Administration. The General Services Administration does not assume any responsibility for the content, operation, or policies of other entities' websites.
