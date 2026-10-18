<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#kms-basics -->
# AWS Guide: KMS Basics

-	📒 Homepage ∙ Developer guide ∙ FAQ ∙ Pricing
-	**KMS** (Key Management Service) is a secure service for creating, storing and auditing usage of cryptographic keys.
- **Service integration:** KMS integrates with other AWS services: EBS, Elastic Transcoder, EMR, Redshift, RDS, SES, S3, WorkMail and Workspaces.
- **Encryption APIs:** The Encrypt and Decrypt API allow you to encrypt and decrypt data on the KMS service side, never exposing the master key contents.
- **Data keys:** The GenerateDataKey API generates a new key off of a master key. The data key contents are exposed to you so you can use it to encrypt and decrypt any size of data in your application layer. KMS does not store, manage or track data keys, you are responsible for this in your application.
- 🔹**Auditing:** Turn on CloudTrail to audit all KMS API events.
- **Access:** Use key policies and IAM policies to grant different levels of KMS access. For example, you create an IAM policy that only allows a user to encrypt and decrypt with a specific key.

Back to top :arrow_up:
