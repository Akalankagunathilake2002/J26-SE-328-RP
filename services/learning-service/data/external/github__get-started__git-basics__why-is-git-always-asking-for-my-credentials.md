<!-- role: All Roles -->
<!-- topic: Git & Version Control -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/get-started/git-basics/why-is-git-always-asking-for-my-credentials -->
# Why is Git always asking for my credentials?

If Git prompts you for your credentials every time you try to interact with GitHub, you''re probably using the HTTPS clone URL for your repository.

Using an HTTPS remote URL has some advantages compared with using SSH. It's easier to set up than SSH, and usually works through strict firewalls and proxies. However, it also prompts you to enter your GitHub credentials every time you pull or push a repository.

You can avoid being prompted for your password by configuring Git to cache your credentials for you. Once you've configured credential caching, Git automatically uses your cached GitHub when you pull or push a repository using HTTPS.

If you are an Enterprise Managed User, and your enterprise owners do not have the SSO Redirect setting enabled for the enterprise, then credential caching may not work properly when using Git Credential Manager (GCM). You will need to disable GCM account filtering locally in this situation to prevent getting prompted for authentication each time you perform a Git operation. For more details, see AUTOTITLE.

## Further reading

* AUTOTITLE
* AUTOTITLE
* AUTOTITLE
* AUTOTITLE
