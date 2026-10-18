<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/patterns/complete-a-complex-form/keep-a-record/ -->
# Keep a record

Help users feel confident in their form submission by providing a record to download or print. A printed or downloaded record of their answers provides a reference for future use, and helps users confirm their successful form submission.

## About this pattern

### What problem does this solve?

Hitting the “Submit” button on a form can be terrifying, especially if the form is complex or contains deeply personal information. Providing the user with a record of the answers provided, questions skipped, and the URL and date stamp of form submission can reduce fear, increase confidence, and improve the user’s trust in your program.

This record also provides a quick reference to submitted answers that might influence eligibility, helping program support personnel work with users to identify potential misunderstandings or mistakes for easier resolution and improved service.

### When to use this pattern

Use this pattern when you are collecting information from users that extends beyond basic contact information, especially if you are collecting information in a long, complex form.

### What’s the solution

Provide the user with a printable record of their answers using a print style sheet designed to provide a streamlined record of the user’s submission, while conserving paper and ink.

## Guidance

          What to do

            Use a print style sheet to create a summary of submitted information in a print-optimized format.
            Do optimize for print by removing unnecessary graphics, minimizing color usage, and making effective use of page dimensions.
            Provide a “title block” that includes the site name, URL, date, and record of successful submission.
            Add any next steps, time frames, or reference numbers like case or record identifiers to the title block, if possible.
            Include a complete recap of all questions and their submitted answers.
            Consider whether any of the submitted values might benefit from partial masking when printed (e.g., a Social Security Number field). If you do mask, display no more than the last four (4) digits to ensure the user can still recognize their entry as the proper value.
            Include a “Print” button on the summary page.
            Strongly consider building in PDF generation. Print-to-PDF functionality is not widely understood in general, and can be particularly cumbersome on mobile devices.
            Do use good semantic structures to aid in creating more accessible PDFs.

          What not to do

            Don't arbitrarily choose which questions and answers are displayed on the record of submitted information. If a question was important enough to ask, it's important enough to keep in the user's record of their form submission.
            Don't include images that are not important to understanding the content.
            Do not print-disable pages or try to suppress page numbering.

      Pattern preview

### Usability guidance

#### Test broadly

- **Test print outputs.** Test printing using a variety of printers, print-to-PDF options, and assistive output devices, using representative browser and operating system combinations based on your site's visitor data prior to launch. Remember that mobile device users will have additional challenges printing or saving to PDF so some on-screen guidance may be necessary.

#### Optimize for print

- **Keep it simple.** Remove unnecessary headers, footers, images, and iconography. Ensure design elements that should be printed have transparent backgrounds.
- **Consider swapping web resolution logos with print resolution logos if you’re using raster files (gif or jpg images).** This will ensure that your logo is legible and not pixelated. Better yet, consider using scalable vector graphic (svg) format logos, which are both efficient and resolution independent. While many images can and should be stripped in a print style sheet, your program name and logo are important indicators of the importance of the document, especially in the absence of design elements and color.
- **Prioritize readability.** If possible, use a white background and dark serif font to optimize readability. When targeting print output, set the font size in points (`12 pt`) rather than screen units (`px`, `em`, or `rem`). Use 12 point or larger text for all content. Some users will struggle to read smaller text, especially if they are under stress.
- Consider using a fixed-width font or the `pre` element for identifiers like case numbers, to ensure numbers and letters can be differentiated easily.
- **Ensure useful links are preserved.** Force underlines on all anchor tags to clearly indicate a link in print, and use the CSS pseudo-element to display the full URL after anchored text hyperlinks. Avoid displaying URLs for links that are fragment identifiers (for example, #login-form) or that are generated using the javascript: pseudo protocol (for example, `javascript:alert("Your session appears to be inactive...");`.
- **Be mindful of costs associated with printing.**
  - Consider whether you need color to communicate critical information, such as in a chart.
  - Fine tune page margins to maximize space and minimize pages printed, but do not make the margins smaller than 0.5 inches to ensure printer support.
  - If user-uploaded images are an essential part of your form, consider the best way to represent them to the user. This might include listing filenames or providing thumbnails, rather than printing full-size images.
  - Prevent images you do print from being cut off or extending wider than a standard portrait-oriented letter-size page.
- **Avoid widowed or orphaned content.** Widows and orphans can be disorienting and sometimes alarming if a user doesn’t see a phrase in context. Avoid splitting headings onto more than one page, and keep lists on the same page as much as possible.
- **Tables require special care.** While tables should not be used for layout, they are appropriate for tabular data and may be the clearest and most space-conscious way to display questions and answers in a printed summary.
  - Print table headers on every page. Avoid splitting tables across pages if possible by utilizing page-break-after or page-break-before CSS properties.
  - Avoid splitting a table row onto more than one page.

### Accessibility

- **Use semantic structures.** While digital teams cannot control how individual users print to PDF because of the wide variety of built-in and add-on tools used for PDF production, good semantic structures will help ensure that PDFs are as usable as possible with screen readers. Test printing on braille printers is also recommended.

## Related components, patterns, and templates

- Progress easily through a form pattern
- Understand expectations and establish trust pattern

## References

- A guide to the state of print stylesheets in 2018. (May 1, 2018) Retrieved on July 29, 2022, from
- Designing for print with CSS. (January 7, 2015) Retrieved on July 29, 2022, from
- How to create printer-friendly pages with CSS. (January 5, 2020) Retrieved on July 29, 2020, from
- SVG on the web - a practical guide. (n.d.) Retrieved on August 23, 2022, from
- What is a printer-friendly web page? (November 21, 2018) Retrieved on July 29, 2022, from

## Disclaimer

Links to nongovernment sources are made for educational or source citation purposes only, and do not represent an endorsement of the organizations by the General Services Administration. The General Services Administration does not assume any responsibility for the content, operation, or policies of other entities' websites.
