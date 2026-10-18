<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/patterns/create-a-user-profile/race-and-ethnicity/ -->
# Race and ethnicity

The race and ethnicity pattern allows users to provide race and ethnicity information in the most accurate and respectful manner possible. Race and ethnicity are often integral to an individual’s sense of self, but they are complex topics; there is no generally accepted agreement that race is a real, biological attribute. Race and ethnicity can, however, be helpful information in assessing the civil rights impact of programs and services, and this data is sometimes a required reporting element.

## About this pattern

### Background

While there isn’t a generally accepted definition for race, the Census Bureau describes the race categories included in census questionnaires as reflecting “a social definition ... not an attempt to define race biologically, anthropologically, or genetically.”

The Office of Management and Budget (OMB) requires that five minimum categories of race and ethnicity are tracked when the data will be used for statistical, administrative, or compliance purposes: American Indian or Alaska Native, Asian, Black or African American, Native Hawaiian or Other Pacific Islander, and White.

OMB requires only two categories for data on ethnicity: Hispanic or Latino, and Not Hispanic or Latino.

OMB’s Standards for Maintaining, Collecting, and Presenting Federal Data on Race and Ethnicity (9/30/2016) actually encourage the collection of detailed race and ethnicity information provided it can be aggregated into their minimum categories. The challenge comes in ensuring that the people answering race and ethnicity questions see themselves in the provided choices. Increasingly, Americans do not. This has led the U.S. Census Bureau to conduct extensive research into alternative ways to collect information on race and ethnicity. This research suggests that a combined race and ethnicity question with detailed checkboxes and the ability to provide additional detail is the optimal way to improve the collection of race and ethnicity data.

### What problem does this solve?

Race and ethnicity can be challenging information for a user to provide, especially when choices are limited or do not align with how an individual self-identifies. Collecting race and ethnicity information can help illuminate issues of equity and disparities in incarceration rates, income, housing, employment, health care, education, and more. Respect for individual dignity should guide the methods for collecting data on race and ethnicity.

### When to use this pattern

Follow this pattern when asking for a user's race and ethnicity as part of your service or program. Only ask for this information if you need it.

### What's the solution?

Allow selection of more than one race and acknowledge people with multiple racial backgrounds. Provide direction on how to complete the form, for example, “Select one or more” or "Select all that apply" explanatory text. Whenever possible, allow respondents to self-identify their ethnicity through an open-ended text entry field.

## Guidance

          What to do

            Do explain why race and ethnicity information is being collected, and how this information will be used.
            Do ask for race and ethnicity as a two-part question as currently required by OMB.
            Do allow users to select more than one race and ethnicity.
            Do allow an open-ended text entry field when ethnicity information is requested and use hint text to communicate that more than one ethnicity can be provided.
            Do include the ability to opt out of providing this information.
            Do consider gender-neutral options when listing ethnicities. As an example, Latino encompasses both Hispanic and Latin-American ethnicities but has an implied masculine gender. Consider using <code>Hispanic</code> or <code>Latin American</code> instead. Gender-neutral options like <code>Latinx</code> have grown in use and adoption within the federal government, but this recommendation may change over time.

          What not to do

            Do not restrict choices to a single race or ethnicity.
            Do not use a single question to capture both race and ethnicity information. While the questions should be asked together, they should not be combined.
            Do not require the user to answer. Provide an option like “Prefer not to say.”
            Do not capture race or ethnicity information for operational or generalization purposes. For example, understanding that a majority of your webinar attendees self-identify as Hispanic does not mean that Hispanic people enjoy webinars.

      Pattern preview

      Pattern code

### Considerations

- **Confirm you need this information.** As with all personal information, consider whether you need to collect it at all. Clearly explain the reason for asking for the information and what will be done to secure the user’s privacy.
- **If you don't need a controlled vocabulary.** If you don't need to restrict the list of races and ethnicities to a specified data collection requirement, consider allowing for user self-identification with an open-ended text field. Users should also have the ability to opt out of providing this information.
- **If the information being collected is intended to be used for statistical, administrative, or compliance purposes.** If the intent of your data collection requires race and ethnicity to be mapped to a fixed minimum set of categories, refer to OMB’s Standards for Maintaining, Collecting, and Presenting Federal Data on Race and Ethnicity (9/30/2016), which encourages the collection of detailed race and ethnicity information provided it can be aggregated into the minimum categories.
- **If you are collecting information on a family.** Do not assume that partners or dependents of the person completing the form will identify as the same race or ethnicity.
- **If you will be displaying race and/or ethnicity in a list.** Always treat racial and ethnic groups as proper nouns and capitalize them. Consider the order list items appear to avoid the perception of bias or favoritism.

### Usability guidance

- **If you're only collecting information on race.** Do allow users to select all races that apply with clear hint text, for example, "Select all that apply".
- **If you’re collecting race and ethnicity information.** Strongly consider using checkboxes for race combined with an open-ended text input for ethnicity self-identification. Do allow users to select all races that apply, and multiple ethnicities, with clear hint text, for example, "Select all that apply" and "You may report more than one ethnicity".
- **Do allow users to opt out of providing race and ethnicity information** with a "Prefer not to answer" option.
- **OMB’s minimum categories for race:**
  - American Indian or Alaska Native
  - Asian
  - Black or African American
  - Native Hawaiian or Other Pacific Islander
  - White

### Accessibility

- **Follow input guidance.** These text fields should follow the accessibility guidelines for all text inputs.
- **Use a fieldset and legend for a checkbox group.** Surround a related set of checkboxes with a ``. The `` provides context for the grouping. Don’t use fieldset and legend for a single check.
- **These custom checkboxes are accessible.** The custom checkbox component is accessible to screen readers because the default checkbox is moved off-screen with `position: absolute; left: -999em`.
- **Use a semantic tag.** The checkbox should have a semantic tag for the `id` attribute, and its corresponding label should have the same value in its `for` attribute.
- **Customization.** As you customize, make sure you follow accessibility guidelines for form templates and the accessibility guidelines for form controls.

## Related components, patterns, and templates

- Checkbox component
- Text input component

## References

- 2010 Census race and Hispanic origin alternative questionnaire experiment. (February 28, 2013) Retrieved on July 15, 2022, from
- 2015 National content test race and ethnicity analysis report. (February 28, 2017) Retrieved on July 15, 2022, from
- About the topic of race. (n.d.) Retrieved on July 15, 2022, from
- Collecting and tabulating ethnicity and race response in the 2020 Census. (February 2020) Retrieved on July 16, 2022, from
- Content research. (n.d.) Retrieved on July 15, 2022, from
- Improvements to the 2020 Census race and Hispanic origin question designs, data processing, and coding procedures. (August 3, 2021) Retrieved on November 4, 2022, from
- Latinx identity in design, tech, and government. (October 14, 2022) Retrieved on November 1, 2022, from `https://digital.gov/2022/10/14/latinx-identity-in-design-tech-and-government/` This link is no longer active. [Archived copy of digital.gov]
- Research to improve data on race and ethnicity. (n.d.) Retrieved on July 15, 2022, from
- Revisions to the standards for the classification of federal data on race and ethnicity. (October 30, 1997) Retrieved on July 15, 2022, from
- Standards for maintaining, collecting, and presenting federal data on race and ethnicity. (September 30, 2016) Retrieved July 15, 2022, from
- Who is Hispanic? (September 15, 2022) Retrieved November 4, 2022, from

## Disclaimer

Links to nongovernment sources are made for educational or source citation purposes only, and do not represent an endorsement of the organizations by the General Services Administration. The General Services Administration does not assume any responsibility for the content, operation, or policies of other entities' websites.
