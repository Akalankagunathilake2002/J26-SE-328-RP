<!-- role: All Roles -->
<!-- topic: Git & Version Control -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/get-started/git-basics/setting-your-username-in-git -->
# Setting your username in Git

Git uses a username to associate commits with an identity. The Git username is not the same as your GitHub username.

## About Git usernames

You can change the name that is associated with your Git commits using the `git config` command. The new name you set will be visible in any future commits you push to GitHub from the command line. If you'd like to keep your real name private, you can use any text as your Git username.

Changing the name associated with your Git commits using `git config` will only affect future commits and will not change the name used for past commits.

## Setting your Git username for every repository on your computer

1.

   ```shell
   git config --global user.name "Mona Lisa"
   ```

1.

   ```shell
   $ git config --global user.name
   > Mona Lisa
   ```

## Setting your Git username for a single repository

1. Change the current working directory to the local repository where you want to configure the name that is associated with your Git commits.

1.

   ```shell
   git config user.name "Mona Lisa"
   ```

1.

   ```shell
   $ git config user.name
   > Mona Lisa
   ```

## Further reading

* AUTOTITLE
* "Git Configuration" from the _Pro Git_ book
