<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: Web Security -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/Security/Attacks/Clickjacking -->
# Clickjacking

In a **clickjacking** attack, an attacker tricks the user into interacting with a target site in a way that they didn't intend.

To do this, the attacker creates a decoy site which embeds the user's target site inside an iframe element. The attacker's site hides the ``, and aligns some decoy elements so they appear in the same place as elements in the target site that trigger sensitive actions. When the user tries to interact with these decoy elements, they are inadvertently interacting with the target site instead, and may be tricked into performing actions with the target site which they did not intend.

## A clickjacking example

Suppose the website for the user's bank is `https://my-bank.example.com`. The user typically stays logged into this site. For simplicity we'll say that the site has a page with a button which transfers all the user's funds to the attacker — although this is obviously unrealistic, it's plausible that the site would have some interactive elements that perform some sensitive operation.

The attacker creates a web page which contains:

- a button element whose contents encourage the user to click it
- an iframe element embedding the bank's page.

```html
Click here for a free kitten!

```

In the CSS for the page, the attacker:

- hides the ``, for example by setting its opacity to zero
- positions the button so it is in the same place as the "Transfer all your money?" button.

```css
iframe {
  opacity: 0;
}

#fake-button {
  position: absolute;
  top: 185px;
  left: 90px;
}
```

The result looks like this (we have set the `` opacity to `0.1`, so you can see the overlay):

If the user tries to click "Click here for a free kitten!", they will actually be clicking on the invisible "Transfer all your money?" button in the bank's website. If the user is already signed in, then the request that this makes to the bank's server will include the user's real credentials, and the request will succeed.

## Clickjacking defenses

### Restricting embedding

Clickjacking depends on the target website being embedded in the attacker's decoy site inside an ``. The main defense is to disallow or at least restrict this capability.

There are two relevant tools here:

- The `frame-ancestors` directive in a content security policy. With this directive, you can control exactly which other documents are allowed to embed yours.
- The X-Frame-Options response header. This header is less fine-grained: it just enables you to disable embedding entirely, or allow it only for same-origin documents.

The `frame-ancestors` directive is a replacement for `X-Frame-Options`. By setting `X-Frame-Options` as well as `frame-ancestors`, you can prevent embedding in browsers that don't support `frame-ancestors`. As browser support for `frame-ancestors` is very good, this is not a major concern.

If `frame-ancestors` and `X-Frame-Options` are both set, then browsers that support `frame-ancestors` will ignore `X-Frame-Options`.

### Restricting cross-site cookies

As an additional partial mitigation, sites should set the `SameSite` cookie attribute for session cookies to `Lax` or `Strict`. Requests from embedded contexts such as `` elements that are not same-site with the top-level document will not include these cookies, and the server will therefore not treat the request as coming from a logged-in user.

## Defense summary checklist

- Set the `frame-ancestors` CSP directive and the X-Frame-Options HTTP response header, in order to prevent other sites from embedding your site as an ``, or to strictly control which sites can embed it.

- Set the `SameSite` cookie attribute for session cookies to `Lax` or `Strict`.
