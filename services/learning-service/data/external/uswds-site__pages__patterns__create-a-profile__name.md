<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/patterns/create-a-user-profile/name/ -->
# Name

The name pattern makes it as easy as possible for users to enter their name in the format required. This pattern is often used to validate identity and helps collect name elements in the most effective and least intrusive manner possible.

## About this pattern

### What problem does this solve?

People have a wide variety of names in various formats. It can be confusing and alienating for them to enter their name if it doesn’t conform to the form fields provided, or if the form fields don’t support the characters, length, or language they require. At the same time, the name fields are often used as a primary form of identity validation, so the agency — and privacy issues — require the information be entered in a specific and consistent way.

### When to use this pattern

Follow this pattern when you need to ask for a user’s name as part of your service. Only ask for a name if you need it.

### What's the solution?

Provide multiple text entry fields that support a rich array of special characters and accents. Provide direction on how to complete the form and what to do if the name doesn’t fit into the provided format.

## Guidance

          What to do

            Do support long text fields for each name. Allow users to enter up to 128 characters per field, but follow form norms for field display size.
            Do support names as short as a single character.
            Do consider confirming very short or empty name fields.
            Do support a rich array of diacritics, accents, and alternative characters.
            Allow users to enter more than one name in each field. Spanish-speaking people will often have two family names. Brazilians may have three or four family names.
            Do allow both upper- and lowercase letters throughout each field.
            Allow users to enter hyphens, apostrophes, and blank spaces in each name field.
            Consider using the autocomplete attribute on name fields to allow the browser to autofill information that has been previously entered.
            Do use fieldset and legend to group related fields together, and clear labels and attributes on these form elements.
            Do display the complete name wherever the information is displayed (even if it is long), including on a confirmation page. You may need to truncate a name when used to convey logged-in status in the site header.
            Do use hint text to help users understand which name should be used in each field.

          What not to do

            Do not require users to enter something in each field. In some cultures, such as Indonesian and Icelandic, people may have only one name.
            If you need to request a middle name, don’t request just an initial. In some cultures, people often have multiple middle names and may not typically abbreviate them with initials.
            Do not assume that a single character is an initial. Some names are one character long.
            Do not normalize casing in names. In some names, such as McNamara and van der Waals, casing is part of the name.
            Do not ask for maiden name. Women are not the only ones who change their names. Ask for previous name.

      Pattern preview

      Pattern code

### Considerations

- **Confirm you need this information.** As with all personal information, consider whether you need to collect it at all. Clearly explain the reason for asking for the information and what will be done to secure the user’s privacy. For example, if you aren’t validating identity, you might not need to collect someone’s name, since a username will meet the need for account login.
- **Consider what name information you need.** If you don’t need to parse out the separate pieces of a person’s name, consider letting the user enter it into a single `full name` text field.
- **If the name information is for identity validation.**  Many people routinely use variations of their name depending on context. Be specific about the name you are requesting. Clearly state the context, for example, "Please enter your name exactly as it appears on your passport" so that users can successfully provide the required information.
- **Consider the field labels.** For many cultures, `first name` and `last name` are not intuitive. In Chinese, Korean, Hungarian, as well as other languages, the first name is the family name. This is an evolving space, with `given name` and `family name` becoming the recommended field labels. Consider using both in a phased approach as people’s comfort level with changing terminology increases (e.g., `First or given name`).
- **If you need the name for correspondence.** If you are going to use the name information to address correspondence to the user, consider including a separate field that allows the user to specify how they’d like to be addressed. This reduces the potential for addressing someone in a way that they find disrespectful. Some cultures find it disrespectful not to include an honorific (Dr., Professor, Mrs.), while others find it overly formal.

    If you won’t be addressing correspondence, avoid asking for the user’s title. Doing so may reveal their gender and marital status, which they might not want to do. If you do ask for their title, use an optional text input field, not a select.

- **If you are collecting information on a family.** Do not assume that partners or dependents of the person completing the form will have the same family name. In many cultures, children have a variation of their parent’s family name and children in blended families may not share a last name with their parents.
- **If you will be displaying the names in a list.** Consider that some cultures expect names to be sorted by given name, not family name.

### Accessibility

- **Follow input guidance.** These text fields should follow the accessibility guidelines for all text inputs.
- **Label each field.** Be sure each field is properly labeled.
- **Customization.** As you customize, make sure you follow accessibility guidelines for form templates and the accessibility guidelines for form controls.

## Related components, patterns, and templates

- Text input component
- Name form template

## References

- Diacritics and special characters by language. (n.d.) Retrieved July 15, 2022, from https://web.library.yale.edu/cataloging/music/diacrit
- GOV.UK Design System: Names. (n.d.) Retrieved July 27, 2022, from https://design-system.service.gov.uk/patterns/names/
- Personal names around the world. (August 17, 2011) Retrieved July 15, 2022, from https://www.w3.org/International/questions/qa-personal-names

## Disclaimer

Links to nongovernment sources are made for educational or source citation purposes only, and do not represent an endorsement of the organizations by the General Services Administration. The General Services Administration does not assume any responsibility for the content, operation, or policies of other entities' websites.
