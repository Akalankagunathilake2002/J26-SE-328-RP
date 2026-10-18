<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#kms-gotchas-and-limitations -->
# AWS Guide: KMS Gotchas and Limitations

-	🔸The Encrypt API only works with < 4KB of data. Larger data requires generating and managing a data key in your application layer.
-	🔸KMS audit events are not available in the CloudTrail Lookup Events API. You need to look find them in the raw .json.gz files that CloudTrail saves in S3.
-	🔸In order to encrypt a multi-part upload to S3, the KMS Key Policy needs to allow “kms:Decrypt” and “kms:GenerateDataKey*” in addition to “kms:Encrypt”, otherwise the upload will fail with an “AccessDenied” error.
-	🔸KMS keys are region specific — they are stored and can only be used in the region in which they are created. They can't be transferred to other regions.
-	🔸KMS keys have a key policy that must grant access to something to manage the key.  If you don't grant anything access to the key on creation, then you have to reach out to support to have the key policy reset Reduce the Risk of the Key Becoming Unmanagable.
-	🔸If you use a key policy to grant access to IAM roles or users and then delete the user/role, recreating the user or role won't grant them permission to the key again.

CloudFront
----------
