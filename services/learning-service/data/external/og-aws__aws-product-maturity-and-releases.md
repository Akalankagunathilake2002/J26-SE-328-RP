<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#aws-product-maturity-and-releases -->
# AWS Guide: AWS Product Maturity and Releases

It’s important to know the maturity of each AWS product. Here is a mostly complete list of first release date, with links to the release notes. Most recently released services are first. Not all services are available in all regions; see this table.

| Service                                                                                                    | Original release | Availability                                                                  | CLI Support | HIPAA Compliant | PCI-DSS Compliant |
|------------------------------------------------------------------------------------------------------------|------------------|-------------------------------------------------------------------------------|:-----------:|:---------------:|:-----------------:|
| 🐥X-Ray										  | 2016-12          | General																	  |✓            |✓                |✓                   |
| 🐥Lex                                           | 2016-11          | Preview                                                                       |             |                 |                   |
| 🐥Polly                                       | 2016-11          | General                                                                       |✓            |✓                |✓                   |
| 🐥Rekognition 							 | 2016-11          | General                                                                       |✓            |✓				 |✓  				|
| 🐥Athena 										 | 2016-11          | General                                                                       |✓             |✓               |✓					|
| 🐥Batch 							 | 2016-11          | General                                                                       |✓             |✓			|✓					|
| 🐥Database Migration Service | 2016-03          | General                                                                      |              | ✓         		|	✓    			|
| 🐥Certificate Manager | 2016-01          | General                                                            | ✓		   |✓			|✓					|
| 🐥IoT                                  | 2015-08          | General                                                                       | ✓           |✓			|✓13					|
| 🐥WAF                                               | 2015-10          | General                                                                       | ✓           | ✓         		|	✓    			|
| 🐥Data Pipeline                           | 2015-10          | General                                                                       | ✓           |				|					|
| 🐥Elasticsearch                | 2015-10          | General                                                                       | ✓           |✓			|✓					|
| 🐥Aurora                                            | 2015-07          | General                                                                       | ✓           | ✓3 |	✓3			|
| 🐥Service Catalog                       | 2015-07          | General                                                                       | ✓           |✓			|✓					|
| 🐥Device Farm                         	  | 2015-07          | General                                                                       | ✓           |				|					|
| 🐥CodePipeline                             | 2015-07          | General                                                                       | ✓           |✓			|					|
| 🐥CodeCommit                                 | 2015-07          | General                                                                       | ✓           |✓			|✓					|
| 🐥API Gateway                            | 2015-07          | General                                                                       | ✓           | ✓1  |	 ✓ 			|
| 🐥Config                                         | 2015-06          | General                                                                       | ✓           |✓                |  ✓              |
| 🐥EFS                                            | 2015-05          | General                                                                       | ✓           |✓                |✓                  |
| 🐥Machine Learning                                 | 2015-04          | General                                                                       | ✓           |                 |                  |
| Lambda                                          | 2014-11          | General                                                                       | ✓           |✓                |   ✓             |
| ECS                                                           | 2014-11          | General                                                                       | ✓           | ✓         		|	✓   			|
| EKS                                                           | 2018-06          | General                                                                       | ✓12           |✓         		|✓	  			|
| KMS                                                | 2014-11          | General                                                                       | ✓           |✓                |   ✓             |
| CodeDeploy                                  | 2014-11          | General                                                                       | ✓           |✓                |                  |
| Kinesis                                     | 2013-12          | General                                                                       | ✓           |✓                |   ✓11    |
| CloudTrail                                  | 2013-11          | General                                                                       | ✓           |✓                |   ✓             |
| AppStream                                 | 2013-11          | Preview                                                                       |             |✓                |                  |
| CloudHSM                                      | 2013-03          | General                                                                       | ✓           |✓                |   ✓            |
| Silk                                           | 2013-03          | Obsolete?                                                                     |             |                 |                  |
| OpsWorks                                      | 2013-02          | General                                                                       | ✓           |✓                |   ✓             |
| Redshift                                   | 2013-02          | General                                                                       | ✓           | ✓         		|	✓   			|
| Elastic Transcoder               | 2013-01          | General                                                                       | ✓           |                 |                  |
| Glacier                                     | 2012-08          | General                                                                       | ✓           | ✓         		|	✓	    		|
| CloudSearch                             | 2012-04          | General                                                                       | ✓           |                 |                  |
| SWF                                             | 2012-02          | General                                                                       | ✓           |✓                | ✓                |
| Storage Gateway                        | 2012-01          | General                                                                       | ✓           |✓                |✓                  |
| DynamoDB                                   | 2012-01          | General                                                                       | ✓           | ✓         		|	  ✓  			|
| DirectConnect                           | 2011-08          | General                                                                       | ✓           | ✓         		|	✓   			|
| ElastiCache                             | 2011-08          | General                                                                       | ✓           |✓14 |✓14                  |
| CloudFormation                          | 2011-04          | General                                                                       | ✓           |✓                |  ✓              |
| SES                                             | 2011-01          | General                                                                       | ✓           |✓                |                  |
| Elastic Beanstalk                    | 2010-12          | General                                                                       | ✓           |✓                |  ✓              |
| Route 53                                   | 2010-10          | General                                                                       | ✓           |✓                | ✓               |
| IAM                     | 2010-09          | General                                                                       | ✓           |                 |  ✓              |
| SNS                                             | 2010-04          | General                                                                       | ✓           | ✓         		| ✓					|
| EMR                                      | 2010-04          | General                                                                       | ✓           | ✓         		|	✓   			|
| RDS                                             | 2009-12          | General                                                                       | ✓           |✓2        |✓9				|
| VPC                                             | 2009-08          | General                                                                       | ✓           | ✓         		|	✓   			|
| Snowball                                  | 2015-10          | General                                                                       | ✓           | ✓         		|✓15					|
| Snowmobile                                                           | 2016-11          | General                                                                       |            |✓                |✓                  |
| CloudWatch                                      | 2009-05          | General                                                                       | ✓           |✓                |  ✓               |
| CloudFront                                      | 2008-11          | General                                                                       | ✓           | ✓4        |  ✓				|
| Fulfillment Web Service                         | 2008-03          | Obsolete?                                                                     |             |                 |                  |
| SimpleDB                                   | 2007-12          | ❗Nearly obsolete | ✓           |                 |  ✓              |
| DevPay                                              | 2007-12          | General                                                                       |             |                 |                  |
| Flexible Payments Service                       | 2007-08          | Retired                                                                       |             |                 |                  |
| EC2                                             | 2006-08          | General                                                                       | ✓           | ✓5,6,7          |	✓6,7,10			|
| SQS                                             | 2006-07          | General                                                                       | ✓           | ✓         		| ✓               |
| S3                                               | 2006-03          | General                                                                       | ✓           | ✓8   |	✓   			|
| Alexa Top Sites                                                 | 2006-01          | General ❗HTTP-only                                                            |             |                 |                  |
| Alexa Web Information Service                                              | 2005-10          | General ❗HTTP-only                                                            |             |                 |                  |

Back to top :arrow_up:
##### Footnotes
**1**: Excludes use of Amazon API Gateway caching
**2**: RDS MySQL, Oracle, and PostgreSQL engines only
**3**: MySQL-compatible Aurora edition only
**4**: Excludes Lambda@Edge
**5**: Includes EC2 Systems Manager
**6**: Includes Elastic Block Storage (EBS)
**7**: Includes Elastic Load Balancing
**8**: Includes S3 Transfer Acceleration
**9**: Includes RDS MySQL, Oracle, PostgreSQL, SQL Server, and MariaDB
**10**: Includes Auto-Scaling
**11**: Data Analytics, Streams, Video Streams and Firehose
**12**: Kubernetes uses a custom CLI for Pod/Service management called kubectl. AWS CLI only handles Kubernetes Master concerns
**13**: IoT Core (includes Device Management) and Greengrass
**14**: ElastiCache for Redis only
**15**: Snowball and Snowball Edge
