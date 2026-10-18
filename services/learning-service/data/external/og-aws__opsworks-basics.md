<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#opsworks-basics -->
# AWS Guide: OpsWorks Basics

-	📒 Homepage ∙ Documentation ∙ FAQ ∙ Pricing: Stacks, Chef Automate, Puppet Enterprise
- OpsWorks is a configuration management service that uses Chef or Puppet configuration management. It is broken out into three different services:
  - OpsWorks Stacks: The service lets you configure and launch stacks specific to your application's needs, and allows you to automate application deployments. Chef runs can be performed manually via the Execute Cookbooks command, otherwise they are only run as part of lifecycle events.
    - OpsWorks Stacks differs from standard configuration management services in that it also allows you to perform some infrastructure and application automation (such as creating Amazon EC2 instances and deploying applications via Chef cookbooks).
  - OpsWorks for Chef Automate: This service launches a dedicated Chef Automate server in your account, which can be used to associate nodes, upload cookbook code, and configure systems. Automated patching, backups, OS updates, and minor Chef version upgrades are provided as part of the service. An AWS API is provided for associating/disassociating nodes. Chef runs can be scheduled on nodes using the chef-client cookbook.
  - OpsWorks for Puppet Enterprise: This service launches a dedicated Puppet Master in your account, which can be used to associate nodes, upload modules, and configure systems. Automated patching, backups, OS updates, and minor Puppet version upgrades are provided as part of the service. An AWS API is provided for associating/disassociating nodes. By default, the Puppet agent will run automatically every 30 minutes on associated nodes.
- OpsWorks for Chef Automate and OpsWorks for Puppet Enterprise are strictly designed for configuration management, and do not provision infrastructure outside the Chef Server/Puppet Master that is created in our account.
- All three OpsWorks services support managing both Amazon EC2 and on-premises infrastructure, however the implementation details differ slightly.
  - OpsWorks Stacks allows you to register instances and install the OpsWorks Agent to connect to your stack.
  - OpsWorks for Chef Automate and OpsWorks for Puppet Enterprise allow you to associate new or existing infrastructure using either the opsworks-cm:AssociateNode API action or the vendor-supported method for associating nodes to Chef Server or Puppet Enterprise.
- Although OpsWorks will let you work with common Chef recipes or Puppet modules when creating your stacks, creating custom recipes will require familiarity with Chef or Puppet syntax. Chef/Puppet code is not supported as part of AWS Support.
- As of December 2016, OpsWorks Stacks supports Chef versions 12, 11.10.4, 11.4.4 and 0.9.15.5.
- As of December 2016, OpsWorks for Chef Automate uses Chef Server version 12.11.1 This is the current stable version of Chef.
- Berkshelfcan be used  with Chef stacks of version 11.10 and later for managing cookbooks and their respective dependencies. However, on Chef 12.x stacks, Berkshelf must be installed by the stack administrator.
- Running your own Chef environment may be an alternative to consider - some considerations are listed in this Bitlancer article.

Back to top :arrow_up:
