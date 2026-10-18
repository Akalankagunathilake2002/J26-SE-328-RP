<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#which-services-to-use -->
# AWS Guide: Which Services to Use

-	AWS offers a *lot* of different services — about a hundred at last count.
-	Most customers use a few services heavily, a few services lightly, and the rest not at all. What services you’ll use depends on your use cases. Choices differ substantially from company to company.
-	**Immature and unpopular services:** Just because AWS has a service that sounds promising, it doesn’t mean you should use it. Some services are very narrow in use case, not mature, are overly opinionated, or have limitations, so building your own solution may be better. We try to give a sense for this by breaking products into categories.
-	**Must-know infrastructure:** Most typical small to medium-size users will focus on the following services first. If you manage use of AWS systems, you likely need to know at least a little about all of these. (Even if you don’t use them, you should learn enough to make that choice intelligently.)
	-	IAM: User accounts and identities (you need to think about accounts early on!)
	-	EC2: Virtual servers and associated components, including:
		-	AMIs: Machine Images
		-	Load Balancers: CLBs and ALBs
		-	Autoscaling: Capacity scaling (adding and removing servers based on load)
		-	EBS: Network-attached disks
		-	Elastic IPs: Assigned IP addresses
	-	S3: Storage of files
	-	Route 53: DNS and domain registration
	-	VPC: Virtual networking, network security, and co-location; you automatically use
	-	CloudFront: CDN for hosting content
	-	CloudWatch: Alerts, paging, monitoring
-	**Managed services:** Existing software solutions you could run on your own, but with managed deployment:
	-	RDS: Managed relational databases (managed MySQL, Postgres, and Amazon’s own Aurora database)
	-	EMR: Managed Hadoop
	-	Elasticsearch: Managed Elasticsearch
	-	ElastiCache: Managed Redis and Memcached
-	**Optional but important infrastructure:** These are key and useful infrastructure components that are less widely known and used. You may have legitimate reasons to prefer alternatives, so evaluate with care to be sure they fit your needs:
	-	⛓Lambda: Running small, fully managed tasks “serverless”
	-	CloudTrail: AWS API logging and audit (often neglected but important)
	-	⛓🕍CloudFormation: Templatized configuration of collections of AWS resources
	-	🕍Elastic Beanstalk: Fully managed (PaaS) deployment of packaged Java, .NET, PHP, Node.js, Python, Ruby, Go, and Docker applications
	-	🐥EFS: Network filesystem compatible with NFSv4.1
	-	⛓🕍ECS: Docker container/cluster management (note Docker can also be used directly, without ECS)
	-   🕍 EKS: Kubernetes (K8) Docker Container/Cluster management
	-	⛓ECR: Hosted private Docker registry
	-	🐥Config: AWS configuration inventory, history, change notifications
	-	🐥X-Ray: Trace analysis and debugging for distributed applications such as microservices.
-	**Special-purpose infrastructure:** These services are focused on specific use cases and should be evaluated if they apply to your situation. Many also are proprietary architectures, so tend to tie you to AWS.
	-	⛓DynamoDB: Low-latency NoSQL key-value store
	-	⛓Glacier: Slow and cheap alternative to S3
	-	⛓Kinesis: Streaming (distributed log) service
	-	⛓SQS: Message queueing service
	-	⛓Redshift: Data warehouse
	-	🐥QuickSight: Business intelligence service
	-	SES: Send and receive e-mail for marketing or transactions
	-	⛓API Gateway: Proxy, manage, and secure API calls
	-	⛓IoT: Manage bidirectional communication over HTTP, WebSockets, and MQTT between AWS and clients (often but not necessarily “things” like appliances or sensors)
	-	⛓WAF: Web firewall for CloudFront to deflect attacks
	-	⛓KMS: Store and manage encryption keys securely
	-	Inspector: Security audit
	-	Trusted Advisor: Automated tips on reducing cost or making improvements
	-	🐥Certificate Manager: Manage SSL/TLS certificates for AWS services
	-	🐥⛓Fargate: Docker containers management, backend for ECS and EKS
-	**Compound services:** These are similarly specific, but are full-blown services that tackle complex problems and may tie you in. Usefulness depends on your requirements. If you have large or significant need, you may have these already managed by in-house systems and engineering teams.
	-	Machine Learning: Machine learning model training and classification
	-	Lex: Automatic speech recognition (ASR) and natural language understanding (NLU)
	-	Polly: Text-to-speech engine in the cloud
	-	Rekognition: Service for image recognition
	-	⛓🕍Data Pipeline: Managed ETL service
	-	⛓🕍SWF: Managed state tracker for distributed polyglot job workflow
	-	⛓🕍Lumberyard: 3D game engine
-	**Mobile/app development:**
	-	SNS: Manage app push notifications and other end-user notifications
	-	⛓🕍Cognito: User authentication via Facebook, Twitter, etc.
	-	Device Farm: Cloud-based device testing
	-	Mobile Analytics: Analytics solution for app usage
	-	🕍Mobile Hub: Comprehensive, managed mobile app framework
-	**Enterprise services:** These are relevant if you have significant corporate cloud-based or hybrid needs. Many smaller companies and startups use other solutions, like Google Apps or Box. Larger companies may also have their own non-AWS IT solutions.
	-	AppStream: Windows apps in the cloud, with access from many devices
	-	Workspaces: Windows desktop in the cloud, with access from many devices
	-	WorkDocs (formerly Zocalo): Enterprise document sharing
	-	WorkMail: Enterprise managed e-mail and calendaring service
	-	Directory Service: Microsoft Active Directory in the cloud
	-	Direct Connect: Dedicated network connection between office or data center and AWS
	-	Storage Gateway: Bridge between on-premises IT and cloud storage
	-	Service Catalog: IT service approval and compliance
-	**Probably-don't-need-to-know services:** Bottom line, our informal polling indicates these services are just not broadly used — and often for good reasons:
	-	Snowball: If you want to ship petabytes of data into or out of Amazon using a physical appliance, read on.
	-	Snowmobile: Appliances are great, but if you've got exabyte scale data to get into Amazon, nothing beats a tractor trailer full of drives.
	-	CodeCommit: Git service. You’re probably already using GitHub or your own solution (Stackshare has informal stats).
	-	🕍CodePipeline: Continuous integration. You likely have another solution already.
	-	🕍CodeDeploy: Deployment of code to EC2 servers. Again, you likely have another solution.
	-	🕍OpsWorks: Management of your deployments using Chef or (as of November 2017) Puppet Enterprise.
-	AWS in Plain English offers more friendly explanation of what all the other different services are.

Back to top :arrow_up:
