<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: Web Security -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Secure_Contexts/features_restricted_to_secure_contexts -->
# Features restricted to secure contexts

This reference lists the web platform features available only in secure contexts — see Secure Contexts for a definition and more details.

## Current features available only in secure contexts

This section lists APIs that specifications make available only in secure contexts.

- Async Clipboard API
- Audio Output Devices API
- Background Fetch API
- Background Synchronization API
- Badging API
- Barcode Detection API
- Battery Status API
- `Cache-Control: immutable`
- Contact Picker API
- Content Index API
- Cookie Store API
- Credential Management API
- Device Memory API
- Device Orientation / Device Motion
- Document Picture-in-Picture API
- EyeDropper API
- Encrypted Media Extensions
- File System API
- Generic Sensor API
- Gamepad API
- Geolocation API
- Idle Detection API
- Keyboard API
- Local Font Access API
- Notifications API
- Web-based Payment Handler API
- Payment Request API
- Presentation API
- Push API
- Reporting API
- Screen Capture API
- Screen Wake Lock API
- Service Workers
- Shared Storage API
- Storage API
- Translator and Language Detector APIs
- VirtualKeyboard API
- Web Authentication API
- Web Bluetooth
- Web Locks API
- Web MIDI
- Web NFC API
- Web Crypto API
- WebCodecs API
- WebGPU API
- WebHID API
- WebOTP API
- WebTransport API
- WebUSB API
- WebXR Device API
- Web Share API
- Window Management API

In addition, the following methods require a secure context (even if the associated API does not):

- `MediaDevices.getUserMedia()`
- `Navigator.registerProtocolHandler()`
