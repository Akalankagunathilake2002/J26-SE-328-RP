<!-- role: Graphic Designer -->
<!-- topic: Visual Design Systems -->
<!-- source: U.S. Web Design System (GSA) -->
<!-- license: Public Domain (CC0) -->
<!-- url: https://designsystem.digital.gov/patterns/create-a-user-profile/phone-number/ -->
# Phone number

The phone number pattern allows users to easily enter their phone number and ensures the phone number is properly formatted.

## About this pattern

### What problem does this solve?

People format their phone number in varying ways — with or without extra spaces, hyphens, periods, and parentheses. Some may be more accustomed to providing only seven digits. This pattern was designed to reduce confusion and frustration and ensure accurate entry.

### When to use this pattern

Use this pattern if you need to collect the user’s phone number. Only ask for the phone number if you need it. This pattern is designed to support U.S. phone numbers and their specific format.

### What's the solution?

Help users enter their phone numbers in a consistent, correct, usable format. Use the form label and hint text to show users the expected format, and if you specifically need a U.S. or SMS-capable mobile phone number. When possible, use input masking and both client- and server-side validation to ensure the phone number they enter can be successfully used to contact them if needed.

## Guidance

          What to do

            Tell users why you need their phone number, why you might contact them, and when.
            Do clearly state if you need a U.S. telephone number.
            Do clearly state if you need an SMS-capable mobile phone number, such as when you need to text a security code for validation.
            Use clear hint text and input masking to ensure proper formatting.
            Do use a "text" vs "numeric" input type.
            Do use fieldset and legend to group related radio buttons together, and clear labels and attributes on these form elements.
            Consider using the autocomplete attribute on telephone number inputs, to allow the browser to autofill information if it has been previously entered.
            Offer very clear validation messages to help users successfully meet format requirements.
            Allow a user to supply multiple phone numbers, labeling options <code>Primary</code> and <code>Secondary</code>.
            Consider offering an extension field for a business line or other temporary residences/shelters.
            Do consider the safety implications of users who share phones and voicemail boxes. Ask for permission to leave potentially sensitive messages.

          What not to do

            Do not require users to enter hyphens or other characters.
            Do not split the phone number into separate fields. Separate fields have a high user interaction cost
            Do not assume that voicemail boxes are private unless explicitly stated through permission-based settings or in the message itself.

      Pattern preview

      Pattern code

### Considerations

- **Confirm you need this information.** As with all personal information, consider whether you need to collect it at all. Clearly explain the reason for asking for the information and what will be done to secure the user’s privacy.
- **Notifications.** If the phone number will be used to subscribe the user to any type of follow-up calls, including automated notifications, reminders, or informational call lists, clearly inform the user and provide a way for the user to opt out.
- **Sensitive information.** If you plan on using the phone number to follow up with the user, consider whether you need to ask the user for permission to leave a voice or text message, and ask them whether sensitive information can be included in the message. Some users may not want sensitive information left in messages for privacy or safety reasons.

### Usability guidance

- **Consider using an input mask.** In fields with a specific expected format, an input mask allows you to constrain and shape the information being entered into that format, without impairing the user’s ability to copy/paste or correct mistyping. If you use an input mask to support formatting the phone field, it should be `___-___-____` for U.S. phone numbers so that the phone number maps to users' experience and is properly formatted. Input masks can help a user more confidently fill out restricted fields, reduce user anxiety about making a mistake, and reduce validation errors and web form abandonment, particularly on mobile devices.
- **Validate client-side and server-side if possible.** Use client-side and ideally server-side validation to ensure proper formatting and usable phone numbers.
- This pattern uses radio buttons. See usability guidance for radio buttons.

### Accessibility

- **Follow input guidance.** These text fields should follow the accessibility guidelines for all text inputs.
- **Use “text” instead of “number” inputs.** Research indicates that numeric inputs still carry many usability problems. The way the user enters the data may differ from what the browser expects. Use `` to better support mobile users.
- **Use fieldset and legend.** Group related radio buttons together with <code></code> and describe the group with <code></code>.
- **Use proper labels and attributes.** Each radio button should have a ``. Associate the two by matching the label's `for` attribute to the input's `id` attribute.
- **Customization.** As you customize, make sure you follow accessibility guidelines for form templates and the accessibility guidelines for form controls.

## Related components, patterns, and templates

- Radio buttons component
- Text input component
- Email address pattern
- Social Security Number pattern

## References

- Bad practices on phone number form fields. (October 16, 2018) Retrieved on July 20, 2022, from
- Consider using localized input masks for ‘phone’ and other restricted inputs (64% aren’t taking advantage of input masking). (November 28, 2017) Retrieved on July 20, 2022, from
- Phone number field design best practices. (August 2, 2019) Retrieved on July 20, 2022, from
- Phone number UX: Always explain why the ‘phone field’ is required. (March 16, 2020) Retrieved on July 20, 2022, from
- Telephone numbers. (n.d.) Retrieved on July 20, 2022, from

## Disclaimer

Links to nongovernment sources are made for educational or source citation purposes only, and do not represent an endorsement of the organizations by the General Services Administration. The General Services Administration does not assume any responsibility for the content, operation, or policies of other entities' websites.
