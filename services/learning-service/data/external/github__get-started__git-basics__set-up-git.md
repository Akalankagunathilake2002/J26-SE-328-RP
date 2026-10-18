<!-- role: All Roles -->
<!-- topic: Git & Version Control -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/get-started/git-basics/set-up-git -->
# Set up Git

At the heart of GitHub is an open-source version control system (VCS) called Git. Git is responsible for everything GitHub-related that happens locally on your computer.

## Using Git

To use Git on the command line, you need to download, install, and configure Git on your computer. You can also install GitHub CLI to use GitHub from the command line. For more information, see AUTOTITLE.

If you want to work with Git locally, but do not want to use the command line, you can download and install the GitHub Desktop client. For more information, see AUTOTITLE.

If you do not need to work with files locally, GitHub lets you complete many Git-related actions directly in the browser, including:

* AUTOTITLE
* AUTOTITLE
* Managing files

## Setting up Git

1. Download and install the latest version of Git.

   > [!NOTE]
   > Most Chrome OS devices from 2020 onwards now have a built-in Linux environment, which includes Git. To enable it, go to the Launcher, search for Linux, and click **Turn on**.
   >
   > If you are using an older Chrome OS device, another method is required:
   >
   > 1. Install a terminal emulator such as Termux from the Google Play Store on your Chrome OS device.
   > 1. From the terminal emulator that you installed, install Git. For example, in Termux, enter `pkg install git` and then type `y` when prompted.

1. Set your username in Git.
1. Set your commit email address in Git.

## Authenticating with GitHub from Git

When you connect to a GitHub repository from Git, you need to authenticate with GitHub using either HTTPS or SSH.

> [!NOTE]
> You can authenticate to GitHub using GitHub CLI, for either HTTPS or SSH. For more information, see `gh auth login`.

### Connecting over HTTPS (recommended)

If you clone with HTTPS, you can cache your GitHub credentials in Git using a credential helper. For more information, see AUTOTITLE and AUTOTITLE.

### Connecting over SSH

If you clone with SSH, you must generate SSH keys on each computer you use to push or pull from GitHub. For more information, see AUTOTITLE and AUTOTITLE.

## Next steps

You now have Git and GitHub all set up. You can now choose to create a repository where you can store your projects. Saving your code in a repository allows you to back up your work and share it around the world.

*

*

*

*
