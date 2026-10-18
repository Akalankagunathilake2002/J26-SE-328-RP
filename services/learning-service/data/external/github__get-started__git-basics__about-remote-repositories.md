<!-- role: All Roles -->
<!-- topic: Git & Version Control -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/get-started/git-basics/about-remote-repositories -->
# About remote repositories

GitHub''s collaborative approach to development depends on publishing commits from your local repository to GitHub for other people to view, fetch, and update.

## About remote repositories

A remote URL is Git's fancy way of saying "the place where your code is stored." That URL could be your repository on GitHub, or another user's fork, or even on a completely different server.

You can only push to two types of URL addresses:

* An HTTPS URL like `https://github.com/user/repo.git`
* An SSH URL, like `git@github.com:user/repo.git`

Git associates a remote URL with a name, and your default remote is usually called `origin`.

## Creating remote repositories

You can use the `git remote add` command to match a remote URL with a name.
For example, you'd type the following in the command line:

```shell
git remote add origin
```

This associates the name `origin` with the `REMOTE_URL`.

You can use the command `git remote set-url` to change a remote's URL.

## Choosing a URL for your remote repository

There are several ways to clone repositories available on GitHub.

When you view a repository while signed in to your account, the URLs you can use to clone the project onto your computer are available below the repository details.

For information on setting or changing your remote URL, see AUTOTITLE.

## Cloning with HTTPS URLs

The `https://` clone URLs are available on all repositories, regardless of visibility. `https://` clone URLs work even if you are behind a firewall or proxy.

When you `git clone`, `git fetch`, `git pull`, or `git push` to a private remote repository using HTTPS URLs on the command line, Git will ask for your GitHub username and password.

> [!TIP]
> * You can use a credential helper so Git will remember your GitHub credentials every time it talks to GitHub. For more information, see AUTOTITLE.
> * To clone a repository without authenticating to GitHub on the command line, you can use GitHub Desktop to clone instead. For more information, see AUTOTITLE.

 If you'd rather use SSH but cannot connect over port 22, you might be able to use SSH over the HTTPS port. For more information, see AUTOTITLE.

## Cloning with SSH URLs

SSH URLs provide access to a Git repository via SSH, a secure protocol. To use these URLs, you must generate an SSH keypair on your computer and add the **public** key to your account on GitHub. For more information, see AUTOTITLE.

When you `git clone`, `git fetch`, `git pull`, or `git push` to a remote repository using SSH URLs, you'll be prompted for a password and must provide your SSH key passphrase. For more information, see AUTOTITLE.

If you are accessing an organization that uses SAML single sign-on (SSO), you must authorize your SSH key to access the organization before you authenticate. For more information, see AUTOTITLE and AUTOTITLE" in the GitHub documentation..

> [!TIP]
> You can use an SSH URL to clone a repository to your computer, or as a secure way of deploying your code to production servers. You can also use SSH agent forwarding with your deploy script to avoid managing keys on the server. For more information, see AUTOTITLE.

## Cloning with GitHub CLI

You can also install GitHub CLI to use GitHub workflows in your terminal. For more information, see AUTOTITLE.
