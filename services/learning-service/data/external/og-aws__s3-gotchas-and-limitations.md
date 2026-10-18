<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#s3-gotchas-and-limitations -->
# AWS Guide: S3 Gotchas and Limitations

-   ❗S3 buckets sit outside the VPC and can be accessed from anywhere in the world if bucket policies are not set to deny it. Read the permissions section above carefully, there are countless cases of buckets exposed to the public.
-	🔸For many years, there was a notorious **100-bucket limit** per account, which could not be raised and caused many companies significant pain. As of 2015, you can request increases. You can ask to increase the limit, but it will still be capped (generally below ~1000 per account).
-	🔸Be careful not to make implicit assumptions about transactionality or sequencing of updates to objects. Never assume that if you modify a sequence of objects, the clients will see the same modifications in the same sequence, or if you upload a whole bunch of files, that they will all appear at once to all clients.
-	🔸S3 has an **SLA** with 99.9% uptime. If you use S3 heavily, you’ll inevitably see occasional error accessing or storing data as disks or other infrastructure fail. Availability is usually restored in seconds or minutes. Although availability is not extremely high, as mentioned above, durability is excellent.
-	🔸After uploading, any change that you make to the object causes a full rewrite of the object, so avoid appending-like behavior with regular files.
-	🔸Eventual data consistency, as discussed above, can be surprising sometimes. If S3 suffers from internal replication issues, an object may be visible from a subset of the machines, depending on which S3 endpoint they hit. Those usually resolve within seconds; however, we’ve seen isolated cases when the issue lingered for 20-30 hours.
-	🔸**MD5s and multi-part uploads:** In S3, the ETag header in S3 is a hash on the object. And in many cases, it is the MD5 hash. However, this is not the case in general when you use multi-part uploads. One workaround is to compute MD5s yourself and put them in a custom header (such as is done by s4cmd).
-	🔸**Incomplete multi-part upload costs:** Incomplete multi-part uploads accrue storage charges even if the upload fails and no S3 object is created. Amazon (and others) recommend using a lifecycle policy to clean up incomplete uploads and save on storage costs. Note that if you have many of these, it may be worth investigating whatever's failing regularly.
-	🔸**US Standard region:** Previously, the us-east-1 region (also known as the US Standard region) was replicated across coasts, which led to greater variability of latency. Effective Jun 19, 2015 this is no longer the case. All Amazon S3 regions now support read-after-write consistency. Amazon S3 also renamed the US Standard region to the US East (N. Virginia) region to be consistent with AWS regional naming conventions.
- 🔸**S3 authentication versions and regions:** In newer regions, S3 only supports the latest authentication. If an S3 file operation using CLI or SDK doesn't work in one region, but works correctly in another region, make sure you are using the latest authentication signature.

Back to top :arrow_up:
