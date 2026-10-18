<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#high-availability-tips -->
# AWS Guide: High Availability Tips

-	AWS offers two levels of redundancy, regions and availability zones (AZs).
-	When used correctly, regions and zones do allow for high availability. You may want to use non-AWS providers for larger business risk mitigation (i.e. not tying your company to one vendor), but reliability of AWS across regions is very high.
-	**Multiple regions:** Using multiple regions is complex, since it’s essentially like managing completely separate infrastructures. It is necessary for business-critical services with the highest levels of redundancy. However, for many applications (like your average consumer startup), deploying extensive redundancy across regions may be overkill.
-	The High Scalability Blog has a good guide to help you understand when you need to scale an application to multiple regions.
-	🔹**Multiple AZs:** Using AZs wisely is the primary tool for high availability!
	-	A typical single-region high availability architecture would be to deploy in two or more availability zones, with load balancing in front, as in this AWS diagram.
	-	The bulk of outages in AWS services affect one zone only. There have been rare outages affecting multiple zones simultaneously (for example, the great EBS failure of 2011) but in general most customers’ outages are due to using only a single AZ for some infrastructure.
	-	Consequently, design your architecture to minimize the impact of AZ outages, especially single-zone outages.
	-	Deploy key infrastructure across at least two or three AZs. Replicating a single resource across more than three zones often won’t make sense if you have other backup mechanisms in place, like S3 snapshots.
	-	A second or third AZ should significantly improve availability, but additional reliability of 4 or more AZs may not justify the costs or complexity (unless you have other reasons like capacity or Spot market prices).
	-	💸Watch out for **cross-AZ traffic costs**. This can be an unpleasant surprise in architectures with large volume of traffic crossing AZ boundaries.
	-	Deploy instances evenly across all available AZs, so that only a minimal fraction of your capacity is lost in case of an AZ outage.
	-	If your architecture has single points of failure, put all of them into a single AZ. This may seem counter-intuitive, but it minimizes the likelihood of any one SPOF to go down on an outage of a single AZ.
-	**EBS vs instance storage:** For a number of years, EBSs had a poorer track record for availability than instance storage. For systems where individual instances can be killed and restarted easily, instance storage with sufficient redundancy could give higher availability overall. EBS has improved, and modern instance types (since 2015) are now EBS-only, so this approach, while helpful at one time, may be increasingly archaic.
-	Be sure to use and understand CLBs/ALBs appropriately. Many outages are due to not using load balancers, or misunderstanding or misconfiguring them.

Back to top :arrow_up:
