<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: Web Security -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/User_activation -->
# User activation

To ensure applications are unable to abuse APIs that can create a bad user experience when the behavior is not desired, some APIs can only be used when the user is in an "active interaction" state, meaning the user is currently interacting with the web page, or has interacted with the page at least once.
Browsers limit access to sensitive APIs like popups, fullscreen, or vibration APIs to active user interactions to prevent malicious scripts from abusing these features.
This page lists web platform features available only after user activation.

A user activation either implies that the user is currently interacting with the page, or has completed an interaction since page load.
Typically, this is a click on a button or some other interaction with the UI.

More precisely, an _activation triggering input event_ is an event which:

- has the `isTrusted` attribute set to `true`, and
- is one of the following types:
  - `keydown` (except for the Esc key, browser-reserved shortcuts, and certain keys that do not produce user activation, which vary by keyboard, such as Caps Lock, Num Lock, and Print Screen. The behavior may vary by browser.)

  - `mousedown`
  - `pointerdown` (if `pointerType` is "mouse")
  - `pointerup` (if `pointerType` is not "mouse")
  - `touchend`

If an activation has been triggered, the user agent differentiates between two types of user activation window states: sticky and transient.

## Comparison between transient and sticky activation

The difference between transient and sticky activation is that transient activation only lasts for a short while, and may in some cases be consumed (deactivated) when a protected feature is used, while sticky activation persists until the end of the session.

Gating features on transient activation ensures that they are only available if directly triggered by a user.
Sticky activation, by contrast, is primarily used to restrict features that should not automatically trigger on page load, such as popups.

## Transient activation

Transient activation is a window state that indicates a user has recently pressed a button or performed some other user interaction.
Transient activation expires after a timeout (if not renewed by further interaction) and may also be consumed by some APIs (like Window.open()).

APIs that require transient activation (list is not exhaustive):

- Clients.openWindow()
- Clipboard.read()
- Clipboard.readText()
- Clipboard.write()
- Clipboard.writeText()
- ContactsManager.select()
- Document.requestStorageAccess()
- DocumentPictureInPicture.requestWindow()
- Element.requestFullScreen()
- Element.requestPointerLock()
- EyeDropper.open()
- HID.requestDevice()
- HTMLInputElement.showPicker()
- HTMLSelectElement.showPicker()
- HTMLVideoElement.requestPictureInPicture()
- IdleDetector.requestPermission()
- Keyboard.lock()
- LanguageModel.create()
- MediaDevices.getDisplayMedia()
- `MediaDevices.getViewportMedia()`
- MediaDevices.selectAudioOutput()
- `MediaStreamTrack.sendCaptureAction()`
- Navigator.share()
- PaymentRequest.show()
- PresentationRequest.start()
- RemotePlayback.prompt()
- Serial.requestPort()
- USB.requestDevice()
- Window.getScreenDetails()
- Window.open()
- Window.queryLocalFonts()
- Window.showDirectoryPicker()
- Window.showOpenFilePicker()
- Window.showSaveFilePicker()
- WindowClient.focus()
- XRSystem.requestSession()

## Sticky activation

Sticky activation is a window state that indicates a user has at some time in the session pressed a button, used a menu, or performed some other user interaction.
It is not reset after it has been set initially (unlike transient activation).

APIs that require sticky activation (not exhaustive):

- beforeunload event
- Navigator.vibrate()
- VirtualKeyboard.show()
- Autoplay of Media and Web Audio APIs (in particular for `AudioContexts`).
- clipboardchange events (these can also be enabled by the user granting the `clipboard-read` permission).

## UserActivation API

To programmatically determine if a window has either sticky or transient user activation, the UserActivation API provides two properties which are available using navigator.userActivation:

- UserActivation.hasBeenActive indicates whether the window has sticky user activation.
- UserActivation.isActive indicates whether the window has transient user activation.
