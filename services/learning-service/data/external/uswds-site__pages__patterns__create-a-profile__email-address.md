<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/patterns/create-a-user-profile/email-address/ -->
# Email address

The email address pattern allows users to confidently and accurately enter their email address and ensures that it is properly formatted.

## About this pattern

### What problem does this solve?

Email addresses can be confusing to enter and users often make mistakes. Some users find it very frustrating to try to identify problems in email formatting.

### When to use this pattern

Use this pattern whenever you are collecting email addresses.

### What's the solution?

A text input field with validation and robust error messaging to guide users in providing the correct information.

## Guidance

          What to do

            Tell users why you need their email address, why you might contact them, and when.
            Do validate formatting by checking for an at symbol (@) that is preceded and followed by one or more characters (not spaces).
            Do use both client-side and server-side validation to support properly formatted email addresses if possible.
            Do consider checking for common misspellings of popular email providers. Warn users if you detect a likely misspelling, but allow them to continue since it might be a genuine email address.
            Do accommodate up to 256 characters. Email addresses cannot be longer than 256 characters.
            Do allow users to paste their email address.
            Do consider enabling autocomplete to allow autofill to enter the email address if they’ve entered it previously.
            Do use fieldset and legend to group related fields together, and clear labels and attributes on these form elements.
            Do provide meaningful error messages that suggest the correct format for an email address.
            Do consider the safety implications of users who share email addresses with others. Consider asking for permission to leave potentially sensitive messages.

          What not to do

            Do not require users to re-enter their email address, unless you have a good reason for doing so.
            Do not set arbitrary minimum lengths for the local portion of the email address (occurring before the @ symbol) or domain (after the @ symbol) parts.
            Do not invalidate characters frequently seen in email addresses including hyphens (-), underscores (_), plus signs (+), or periods (.) in the local portion of an email address. See RFC 822 for the exhaustive list of permitted characters in the local portion of an email address.
            Do not restrict top-level domains for email address unless your use case is very specific, for example, only .gov or .mil addresses.
            Do not assume that email messages are private unless explicitly stated through permission-based settings.

      Pattern preview

      Pattern code

### Considerations

- **Confirm you need this information.** As with all personal information, consider whether you need to collect it at all. Clearly explain the reason for asking for the information and what will be done to secure the user’s privacy.
- **Sensitive information.** If you plan on using the email address to follow up with the user, consider whether you need to ask the user whether potentially sensitive information can be included in the message. Some users may not want sensitive information left in email messages for privacy or safety reasons.

### Usability guidance

- **Do not require users to re-enter their email address, unless you have a good reason for doing so.** If you're collecting email addresses for the purpose of communicating with the user, verifying that a user's email address is correctly spelled reduces the risk of sending sensitive information to the wrong individual.
- **Consider validating a user's email address by requiring them to click an emailed verification link.** When creating an account based on an email address, requiring users to click an emailed verification link and successfully authenticate  ensures information will be shared with the correct individual.
- This pattern uses radio buttons. See usability guidance for radio buttons.

### Accessibility

- **Follow input guidance.** These text fields should follow the accessibility guidelines for all text inputs.
- **Use fieldset and legend.** Group related radio buttons together with `` and describe the group with ``.
- **Use proper labels and attributes.** Each radio button should have a ``. Associate the two by matching the label's `for` attribute to the input's `id` attribute.
- **Customization.** As you customize, make sure you follow accessibility guidelines for form templates and the accessibility guidelines for form controls.

## Related components, patterns, and templates

- Radio buttons component
- Text input component
- Phone number pattern
- Social Security Number pattern

## References

- Mobile form usability: avoid splitting single input entities. (February 12, 2013) Retrieved on July 20, 2022, from .
- RFC 822. (August 13, 1982) Retrieved on July 20, 2022, from . See also RFC Editor Errata.
- Validate email addresses (Regular Expressions Cookbook). (n.d). Retrieved on July 20, 2022, from .

## Disclaimer

Links to nongovernment sources are made for educational or source citation purposes only, and do not represent an endorsement of the organizations by the General Services Administration. The General Services Administration does not assume any responsibility for the content, operation, or policies of other entities' websites.
