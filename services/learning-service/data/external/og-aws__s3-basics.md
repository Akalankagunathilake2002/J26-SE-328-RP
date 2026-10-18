<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#s3-basics -->
# AWS Guide: S3 Basics

-	📒 Homepage ∙ Developer guide ∙ FAQ ∙ Pricing
-	**S3** (Simple Storage Service) is AWS’ standard cloud storage service, offering file (opaque “blob”) storage of arbitrary numbers of files of almost any size, from 0 to **5TB**. (Prior to 2011 the maximum size was 5 GB; larger sizes are now well supported via multipart support.)
-	Items, or **objects**, are placed into named **buckets** stored with names which are usually called **keys**. The main content is the **value**.
-	Objects are created, deleted, or updated. Large objects can be streamed, but you cannot modify parts of a value; you need to update the whole object. Partial data access can work via S3 Select.
-	Every object also has **metadata**, which includes arbitrary key-value pairs, and is used in a way similar to HTTP headers. Some metadata is system-defined, some are significant when serving HTTP content from buckets or CloudFront, and you can also define arbitrary metadata for your own use.
-	**S3 URIs:** Although often bucket and key names are provided in APIs individually, it’s also common practice to write an S3 location in the form 's3://bucket-name/path/to/key' (where the key here is 'path/to/key'). (You’ll also see 's3n://' and 's3a://' prefixes in Hadoop systems.)
-	**S3 vs Glacier, EBS, and EFS:** AWS offers many storage services, and several besides S3 offer file-type abstractions. Glacier is for cheaper and infrequently accessed archival storage. EBS, unlike S3, allows random access to file contents via a traditional filesystem, but can only be attached to one EC2 instance at a time. EFS is a network filesystem many instances can connect to, but at higher cost. See the comparison table.

Back to top :arrow_up:
