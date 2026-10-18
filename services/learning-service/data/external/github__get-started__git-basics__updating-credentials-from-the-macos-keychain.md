<!-- role: All Roles -->
<!-- topic: Git & Version Control -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/get-started/git-basics/updating-credentials-from-the-macos-keychain -->
# Updating credentials from the macOS Keychain

You''ll need to update your saved credentials in the `git-credential-osxkeychain` helper if you change your username, password, or GitHub on GitHub.

> [!NOTE]
> Updating credentials from the macOS Keychain only applies to users who manually configured a GitHub using the `osxkeychain` helper that is built-in to macOS.
>
> We recommend you either configure SSH or upgrade to the Git Credential Manager (GCM) instead. GCM can manage authentication on your behalf (no more manual GitHubs) including 2FA (two-factor auth).

> [!NOTE]
>

## Updating your credentials via Keychain Access

1. Click on the Spotlight icon (magnifying glass) on the right side of the menu bar.
1. Type `Keychain Access`, then press the Enter key to launch the app.
1. In Keychain Access, search for `github.com`.
1. Find the "Internet password" entry for `github.com`.
1. Edit or delete the entry accordingly.

## Deleting your credentials via the command line

Through the command line, you can use the credential helper directly to erase the keychain entry.

```shell
$ git credential-osxkeychain erase
host=github.com
protocol=https
> [Press Return]
```

If it's successful, nothing will print out. To test that it works, try and clone a private repository. If you are prompted for a password, the keychain entry was deleted.

## Further reading

* AUTOTITLE
