<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/patterns/create-a-user-profile/social-security-number/ -->
# Social Security Number

The Social Security Number pattern allows users to easily enter their Social Security Number and ensures the Social Security Number is properly formatted.

## About this pattern

### What problem does this solve?

A Social Security Number is often a critical piece for validating identity when applying for government services or benefits, but can be confusing for users to enter correctly.

### When to use this pattern

Only use this pattern when you need to confirm a user's identity by asking for their Social Security Number. This information may be important when determining eligibility for many federal programs, such as federal student loans, public assistance, and Medicare.

### When to consider something else

If you do not specifically need a person’s Social Security Number, do not ask for or collect this information. The Social Security Number is intricately linked to a person’s identity, and should only be used when absolutely required for identification purposes.

While most U.S. citizens and eligible U.S. residents have a Social Security Number, some people may not know their Social Security Number, or may lack the necessary documentation to obtain one easily.

### What's the solution?

Provide a single text field to enter the Social Security Number.

## Guidance

          What to do

            Do allow users to enter a Social Security Number with as much fault tolerance as possible. Hyphens and blank spaces in the Social Security Number field should be accommodated if at all possible, since users may be accustomed to entering separators to the numeric groups that make up a Social Security Number.
            Do use a "text" vs "numeric" input type.
            Do consider using input masking to guide correct entry of the Social Security Number.
            Do use both client-side and server-side validation if possible to enforce format consistency and flag invalid Social Security Numbers.

          What not to do

            Do not separate the Social Security Number entry into three separate fields.
            Do not use placeholder text.

      Pattern preview

      Pattern code

### Considerations

- **Confirm you need this information.** As with all personal information, consider whether you need to collect it at all. Clearly explain the reason for asking for the information and what will be done to secure the user’s privacy.
- **People without Social Security Numbers.** Some people do not have Social Security Numbers, and may not be easily able to provide the documentation required to apply for a Social Security Number. Consider whether there are other methods you can use to validate identity in the absence of a Social Security Number.

### Usability guidance

- **Avoid multiple fields.** If possible, let users type the entire Social Security Number into a single field, not across three separate fields.
- **Consider using an input mask.** In fields with a specific expected format, an input mask allows you to constrain and shape the information being entered into that format, without impairing the user’s ability to copy/paste or correct mistyping. If you use an input mask for the Social Security Number field, it should be `___ __ ____` so that the Social Security Number maps to users' experience with Social Security Numbers and is properly formatted. Input masks can help a user more confidently fill out restricted fields, reduce user anxiety about making a mistake, and reduce validation errors and web form abandonment, particularly on mobile devices. Make sure your hint text supports the format expected from the user if using an input mask.
- **Avoid obfuscation.** It may be tempting to obfuscate Social Security Numbers as they are being input similar to the way many password fields operate. This can add to a user’s anxiety and frustration as they will not be able to see whether what they have entered is correct. If you must use obfuscation, provide an easy way for users to disable obfuscation allowing them to confirm their input.

### Accessibility

- **Follow input guidance.** These text fields should follow the accessibility guidelines for all text inputs.
- **Use “text” instead of “number” inputs.** Research indicates that numeric inputs still carry many usability problems. The way the user enters the data may differ from what the browser expects. Use `` to better support mobile users.
- **Customization.** As you customize, make sure you follow accessibility guidelines for form templates and the accessibility guidelines for form controls.

## Related components, patterns, and templates

- Input masking component
- Text input component
- Email address pattern
- Phone number pattern

## References

- 8 recommendations for creating effective input fields. (n.d.) Retrieved on July 20, 2022, from
- Consider using localized input masks for ‘phone’ and other restricted inputs. (November 28, 2017) Retrieved on July 20, 2022, from
- Masked field. (n.d.) Retrieved on July 20, 2022, from
- Mobile form usability: avoid splitting single input entities. (February 12, 2013) Retrieved on July 20, 2022, from
- National Insurance Numbers. (n.d.) Retrieved on July 20, 2022, from
- Placeholders in a form field. (May 11, 2014) Retrieved on July 20, 2022, from
- Social Security is changing the way SSNs are issued. (n.d.) Retrieved on July 20, 2022, from

## Disclaimer

Links to nongovernment sources are made for educational or source citation purposes only, and do not represent an endorsement of the organizations by the General Services Administration. The General Services Administration does not assume any responsibility for the content, operation, or policies of other entities' websites.
