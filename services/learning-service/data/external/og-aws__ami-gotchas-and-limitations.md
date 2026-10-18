<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#ami-gotchas-and-limitations -->
# AWS Guide: AMI Gotchas and Limitations

-	🔸**Amazon Linux package versions:** By default, instances based on Amazon Linux AMIs are configured point to the latest versions of packages in Amazon’s package repository. This means that the package versions that get installed are not locked and it is possible for changes, including breaking ones, to appear when applying updates in the future. If you bake your AMIs with updates already applied, this is unlikely to cause problems in running services whose instances are based on those AMIs – breaks will appear at the earlier AMI-baking stage of your build process, and will need to be fixed or worked around before new AMIs can be generated. There is a “lock on launch” feature that allows you to configure Amazon Linux instances to target the repository of a particular major version of the Amazon Linux AMI, reducing the likelihood that breaks caused by Amazon-initiated package version changes will occur at package install time but at the cost of not having updated packages get automatically installed by future update runs. Pairing use of the “lock on launch” feature with a process to advance the Amazon Linux AMI at your discretion can give you tighter control over update behaviors and timings.
-   **Cloud-Init Defaults:** Oftentimes users create AMIs after performing customizations (albeit manually or via some tool such as Packer or Ansible).  If you're not careful to alter cloud-init settings that correspond to the system service (e.g. sshd, etc.) you've customized, you may find that your changes are no longer in effect after booting your new AMI for the first time, as cloud-init has overwritten them.

    Some distros have different files than others, but all are generally located in `/etc/cloud/`, regardless of distro.  You will want to review these files carefully for your chosen distro before rolling your own AMIs.  A complete reference to cloud-init is available on the cloud-init site.  This is an advanced configuration mechanism, so test any changes made to these files in a sandbox prior to any serious usage.

Auto Scaling
------------
