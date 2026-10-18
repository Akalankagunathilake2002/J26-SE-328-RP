<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#elastic-beanstalk-gotchas-and-limitations -->
# AWS Guide: Elastic Beanstalk Gotchas and Limitations

- 🔸 Don't edit [apache|nginx] conf files manually on ec2 instances as they will be re-written on each deployment (use ebextensions instead)
- 🔸 After creating an EB environment, it's no longer possible to change the `Name` tag
- 🔸 EB will sometimes quarantine instances that cause multiple deployment issues. Despite being quarantined, EB will still deploy to them on subsequent deployments. To prevent this behavior, said instances will need to be terminated (or the underlying issue fixed)
- File uploads are capped at 10MB for most default eb configurations - update nginx config to change
- If you edit `.elasticbeanstalk/saved_configs/`, be aware that this is not kept in sync with the EB environment config. You'll need to manually fetch and save for changes to take effect

Elastic IPs
-----------
