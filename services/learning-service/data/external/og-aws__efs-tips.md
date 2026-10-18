<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#efs-tips -->
# AWS Guide: EFS Tips

-	With EFS being based on NFSv4.1, any directory on the EFS can be mounted directly, it doesn't have to be the root directory. One application could mount *fs-12345678:/prog1*, another *fs-12345678:/prog2*.
-	User and group level permissions can be used to control access to certain directories on the EFS file system.
-	⏱ **Sharing EFS filesystems:** One EFS filesystem can be used for multiple applications or services, but it should be considered carefully:

	Pros:
	- Because performance is based on total size of stored files, having everything on one drive will increase performance for everyone. One application consuming credits faster than it can accumulate might be offset by another application that just stores files on EFS and rarely accesses them.

	Cons:
	- Since credits are shared, if one application over-consumes them, it will affect the others.
	- A compromise is made with regards to security: all clients will have to have network access to the drive. Someone with root access on one client instance can mount any directory on the EFS and they have read-write access to all files on the drive, even if they don't have access to the applications hosted on other clients. There isn't a no-root-squash equivalent for EFS.

Back to top :arrow_up:
