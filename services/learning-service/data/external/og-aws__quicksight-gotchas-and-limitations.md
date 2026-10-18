<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#quicksight-gotchas-and-limitations -->
# AWS Guide: Quicksight Gotchas and Limitations

-	❗Out of the box Quicksight is not able to access tables that are linked to a Schema in the AWS Glue Schema Registry. This is because the auto-generated IAM role `aws-quicksight-service-role-v0` does not have the necessary permissions. You can't pick another role to be used but you can add more permissions to the role. The error message you will receive is an `SQL_EXCEPTION` with details `SYNTAX_ERROR: line 2:8: Column 'columnname' cannot be resolved` where `columnname` is the first column in your table.
-	🔸Only QuickSight accounts that were created in the US East (N. Virginia) region can access the QuickSight Forum/Community. And you can only have a QuickSight account in one region per AWS account.

RDS
---
