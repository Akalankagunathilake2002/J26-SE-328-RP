<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/patterns/create-a-user-profile/address/ -->
# Address

The physical and mailing address patterns help users enter their address successfully.

## About these patterns

### What problems do these patterns solve?

While most addresses in the U.S. follow a specific pattern, there are unique variations in some rural areas, U.S. territories, and military posts. In addition, some people are unhoused or in temporary housing, and may need to specify a mailing address that is different from their physical address —  particularly in disaster relief and recovery situations.

## Physical address

### When to use this pattern

Use this pattern when you need the physical location of a person and you need to parse out the specific parts of the address. This may be important when determining benefits eligibility, for disaster recovery purposes, or other reasons. Since physical addresses may be new, temporary, or not currently served by the USPS consider asking for a mailing address, too. Physical addresses may be where a building or property is located, or potentially where a displaced individual is currently located. Mailing addresses are where postal mail must be sent.

### When to consider something else

This pattern supports domestic U.S. addresses, including the U.S. territories and military outposts. If you need to collect addresses that may not fit this format, such as international addresses for citizens living overseas, you will need to use something else.

### What’s the solution

Provide all the fields needed for a user to provide a physical address, even less conventional attributes like a Google Plus Code.

### Guidance

          What to do

            Do support long text fields.
            Do support a rich array of diacritics, accents, and alternative characters.
            Do allow both upper and lowercase letters throughout each field.
            Allow users to enter hyphens, apostrophes, special characters, and blank spaces in each name field.
            Consider using the autocomplete attribute on address input fields to allow the browser to autofill information that has been previously entered.
            Provide rich information cues in dropdowns. For example, for state dropdowns, use <code>MD - Maryland</code> and <code>TX - Texas</code>, rather than the state code alone.
            Do provide the Puerto Rican Urbanization field, unless your program does not serve Puerto Rico.
            If your program does not serve the armed forces or U.S. territories, you may want to provide links to related resources for these users if such resources exist.

          What not to do

            Don't auto-advance focus from one field to the next. This makes it difficult for keyboard-only users to navigate and correct mistakes.
            Do not limit addresses to conventionally formatted addresses. Some rural areas and the U.S. territories have unusually formatted addresses.
            Do not assume that people can receive mail at their physical location. People in some communities can only receive mail at post office boxes.

      Pattern preview

      Pattern code

#### Considerations

- **Confirm you need this information.** As with all personal information, consider whether you need to collect it at all. Clearly explain the reason for asking for the information and what will be done to secure the user’s privacy.
- **People without fixed addresses.** Some people do not have fixed addresses. Consider providing other options for reaching them.
- **Physical vs. mailing address.** If you do need an address, determine if you need a physical address or a mailing address, or both. Physical addresses are most important for determining benefits eligibility or for disaster response. Mailing addresses are important for correspondence.
- **Both physical and mailing address.** If you need both the physical and mailing address, consider providing a checkbox for `same as physical address` to auto-populate the mailing address.
- **Google Plus Codes.** Consider whether Google Plus Codes are appropriate for your audience. Google Plus Codes identify a physical location, including those that are not identifiable by a typical postal address. They can be used to identify physical locations that are very remote, where addresses are not available, where someone doesn’t have a fixed address (such as a person who is unhoused), or during an emergency.
- **Puerto Rico.** Consider whether residents of Puerto Rico are part of your audience. Addresses for Puerto Rico require the Urbanization field.

#### Usability guidance

- **Consider using an input mask.** In fields with a specific expected format, an input mask allows you to constrain and shape the information being entered into that format, without impairing the user’s ability to copy/paste or correct mistyping. If you use an input mask for the ZIP code field, it should be `_____-____` so that the ZIP code maps to users' experience with ZIP codes and is properly formatted, regardless of whether a user enters a five- or nine-digit ZIP code. Input masks can help a user more confidently fill out restricted fields, reduce  user anxiety about making a mistake, and reduce validation errors and web form abandonment, particularly on mobile devices.
- **Avoid dropdowns that require long scrolling.** If possible, let users type their state or territories’ abbreviation when they reach the state dropdown menu, instead of having to scroll and select.
- **Provide rich information cues in dropdowns.** For example, for state dropdowns, use `MD - Maryland` and `TX - Texas`, rather than the state code alone.

#### Accessibility

- **Follow input guidance.** These text fields should follow the accessibility guidelines for all text inputs.
- **Don't auto-advance focus.** Do not use JavaScript to auto advance the focus from one field to the next. This makes it difficult for keyboard-only users to navigate and correct mistakes.
- **Customization.** As you customize, make sure you follow accessibility guidelines for form templates and the accessibility guidelines for form controls.

## Mailing address

### When to use this pattern

Use this pattern when you need to provide written correspondence or materials to a person and need to parse out the elements of the address. For many people this may be the same address as their physical address.

### When to consider something else

This pattern supports domestic U.S. addresses, including the U.S. territories and military outposts. If you need to collect addresses that may not fit this format, such as international addresses for citizens living overseas, you will need to use something else.

### What’s the solution

Provide all the fields a user needs to successfully enter a mailing address.

### Guidance

          What to do

            Do support long text fields.
            Do support a rich array of diacritics, accents, and alternative characters.
            Do allow both upper and lowercase letters throughout each field.
            Allow users to enter hyphens, apostrophes, special characters, and blank spaces in each name field.
            Consider using the autocomplete attribute on address input fields to allow the browser to autofill information that has been previously entered.
            Provide rich information cues in dropdowns. For example, for state dropdowns, use <code>MD - Maryland</code> and <code>TX - Texas</code>, rather than the state code alone.
            Do provide the Puerto Rican Urbanization field, unless your program does not serve Puerto Rico.
            If the armed forces and the U.S. territories are not included, you may want to provide a link to their resources for clarity.

          What not to do

            Don't auto-advance focus from one field to the next. This makes it difficult for keyboard-only users to navigate and correct mistakes.
            Do not limit addresses to conventionally formatted addresses. Some rural areas and the U.S. territories have unusually formatted addresses.
            Do not assume that people can receive mail at their physical location. People in some communities can only receive mail at post office boxes.

      Pattern preview

      Pattern code

#### Considerations

- **Confirm you need this information.** As with all personal information, consider whether you need to collect it at all. Clearly explain the reason for asking for the information and what will be done to secure the user’s privacy.
- **People without fixed addresses.** Some people do not have fixed addresses. Consider providing other options for them to be reached.
- **Physical vs. mailing address.** If you do need an address, determine if you need a physical address or a mailing address, or both. Physical addresses are most important for determining benefits eligibility or for disaster response. Mailing addresses are important for correspondence.
- **Both physical and mailing address.** If you need both the physical and mailing address, consider providing a checkbox for `same as physical address` to auto-populate the mailing address.

#### Usability guidance

- **Consider using an input mask.** In fields with a specific expected format, an input mask allows you to constrain and shape the information being entered into that format, without impairing the user’s ability to copy/paste or correct mistyping. If you use an input mask for the ZIP code field, it should be `_____-____` so that the ZIP code maps to users' experience with ZIP codes and is properly formatted, regardless of whether a user enters a five- or nine-digit ZIP code. Input masks can help a user more confidently fill out restricted fields, reduce  user anxiety about making a mistake, and reduce validation errors and web form abandonment, particularly on mobile devices.
- **Avoid dropdowns that require long scrolling.** If possible, let users type their state or territories’ abbreviation when they reach the state dropdown menu, instead of having to scroll and select.
- **Provide rich information cues in dropdowns.** For example, for state dropdowns, use `MD - Maryland` and `TX - Texas`, rather than the state code alone.

#### Accessibility

- **Follow input guidance.** These text fields should follow the accessibility guidelines for all text inputs.
- **Don't auto-advance focus.** Do not use JavaScript to auto advance the focus from one field to the next. This makes it difficult for keyboard-only users to navigate and correct mistakes.
- **Customization.** As you customize, make sure you follow accessibility guidelines for form templates and the accessibility guidelines for form controls.

## Related components, patterns, and templates

- Checkbox component
- Input mask component
- Select component
- Text input component
- Name pattern
- Address form template

## References

- Google Plus Codes. (n.d.) Retrieved July 15, 2022, from
- The Navajo Nation addresses its residents with Plus Codes. (October 12, 2020) Retrieved on August 3, 2022, from
- USPS Addressing Standards Publication 28. (n.d.) Retrieved July 15, 2022, from
- USPS Addressing Standards for Puerto Rico and the U.S. Virgin Islands. (n.d.) Retrieved July 15, 2022, from
- Universal Post*Code Database. (n.d.) Retrieved July 28, 2022, from

## Disclaimer

Links to nongovernment sources are made for educational or source citation purposes only, and do not represent an endorsement of the organizations by the General Services Administration. The General Services Administration does not assume any responsibility for the content, operation, or policies of other entities' websites.
