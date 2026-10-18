<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#when-to-use-aws -->
# AWS Guide: When to Use AWS

-	AWS is the dominant public cloud computing provider.
	-	In general, “cloud computing” can refer to one of three types of cloud: “public,” “private,” and “hybrid.” AWS is a public cloud provider, since anyone can use it. Private clouds are within a single (usually large) organization. Many companies use a hybrid of private and public clouds.
	-	The core features of AWS are infrastructure-as-a-service (IaaS) — that is, virtual machines and supporting infrastructure. Other cloud service models include platform-as-a-service (PaaS), which typically are more fully managed services that deploy customers’ applications, or software-as-a-service (SaaS), which are cloud-based applications. AWS does offer a few products that fit into these other models, too.
	-	In business terms, with infrastructure-as-a-service you have a variable cost model — it is OpEx, not CapEx (though some pre-purchased contracts are still CapEx).
  - AWS’s TTM revenue was **$37.549 billion** as of Q1 2020 according to their earnings results (slide 14 in the linked deck), or roughly **14%** of Amazon.com’s total revenue (slide 11 in the same deck) for the same TTM period.
-	**Main reasons to use AWS:**
	-	If your company is building systems or products that may need to scale
	-	and you have technical know-how
	-	and you want the most flexible tools
	-	and you’re not significantly tied into different infrastructure already
	-	and you don’t have internal, regulatory, or compliance reasons you can’t use a public cloud-based solution
	-	and you’re not on a Microsoft-first tech stack
	-	and you don’t have a specific reason to use Google Cloud
	-	and you can afford, manage, or negotiate its somewhat higher costs
	-	... then AWS is likely a good option for your company.
-	Each of those reasons above might point to situations where other services are preferable. In practice, many, if not most, tech startups as well as a number of modern large companies can or already do benefit from using AWS. Many large enterprises are partly migrating internal infrastructure to Azure, Google Cloud, and AWS.
-	**Costs:** Billing and cost management are such big topics that we have an entire section on this.
-	🔹**EC2 vs. other services:** Most users of AWS are most familiar with EC2, AWS’ flagship virtual server product, and possibly a few others like S3 and CLBs. But AWS products now extend far beyond basic IaaS, and often companies do not properly understand or appreciate all the many AWS services and how they can be applied, due to the sharply growing number of services, their novelty and complexity, branding confusion, and fear of ⛓lock-in to proprietary AWS technology. Although a bit daunting, it’s important for technical decision-makers in companies to understand the breadth of the AWS services and make informed decisions. (We hope this guide will help.)
-	🚪**AWS vs. other cloud providers:** While AWS is the dominant IaaS provider (31% market share in this 2016 estimate), there is significant competition and alternatives that are better suited to some companies. This Gartner report has a good overview of the major cloud players :
	-	**Google Cloud Platform**. GCP arrived later to market than AWS, but has vast resources and is now used widely by many companies, including a few large ones. It is gaining market share. Not all AWS services have similar or analogous services in GCP. And vice versa: In particular, GCP offers some more advanced machine learning-based services like the Vision, Speech, and Natural Language APIs. It’s not common to switch once you’re up and running, but it does happen: Spotify migrated from AWS to Google Cloud. There is more discussion on Quora about relative benefits. Of particular note is that VPCs in GCP are global by default with subnetworks per region, while AWS’ VPCs have to live within a particular region. This gives GCP an edge if you’re designing applications with geo-replication from the beginning. It’s also possible to share one GCP VPC between multiple projects (roughly analogous to AWS accounts), while in AWS you’d have to peer them. It’s also possible to peer GCP VPCs in a similar manner to how it’s done in AWS.
	-	**Microsoft Azure** is the de facto choice for companies and teams that are focused on a Microsoft stack, and it has now placed significant emphasis on Linux as well
	-	In **China**, AWS’ footprint is relatively small. The market is dominated by Alibaba’s Alibaba Cloud, formerly called Aliyun.
	-	Companies at (very) large scale may want to reduce costs by managing their own infrastructure. For example, Dropbox migrated to their own infrastructure.
	-	Other cloud providers such as Digital Ocean offer similar services, sometimes with greater ease of use, more personalized support, or lower cost. However, none of these match the breadth of products, mind-share, and market domination AWS now enjoys.
	-	Traditional managed hosting providers such as Rackspace offer cloud solutions as well.
-	🚪**AWS vs. PaaS:** If your goal is just to put up a single service that does something relatively simple, and you’re trying to minimize time managing operations engineering, consider a platform-as-a-service such as Heroku. The AWS approach to PaaS, Elastic Beanstalk, is arguably more complex, especially for simple use cases.
-	🚪**AWS vs. web hosting:** If your main goal is to host a website or blog, and you don’t expect to be building an app or more complex service, you may wish consider one of the myriad web hosting services.
-	🚪**AWS vs. managed hosting:** Traditionally, many companies pay managed hosting providers to maintain physical servers for them, then build and deploy their software on top of the rented hardware. This makes sense for businesses who want direct control over hardware, due to legacy, performance, or special compliance constraints, but is usually considered old fashioned or unnecessary by many developer-centric startups and younger tech companies.
-	**Complexity:** AWS will let you build and scale systems to the size of the largest companies, but the complexity of the services when used at scale requires significant depth of knowledge and experience. Even very simple use cases often require more knowledge to do “right” in AWS than in a simpler environment like Heroku or Digital Ocean. (This guide may help!)
-	**Geographic locations:** AWS has data centers in over a dozen geographic locations, known as **regions**, in Europe, East Asia, North and South America, and now Australia and India. It also has many more **edge locations** globally for reduced latency of services like CloudFront.
	-	See the current list of regions and edge locations, including upcoming ones.
	-	If your infrastructure needs to be in close physical proximity to another service for latency or throughput reasons (for example, latency to an ad exchange), viability of AWS may depend on the location.
-	⛓**Lock-in:** As you use AWS, it’s important to be aware when you are depending on AWS services that do not have equivalents elsewhere.
	-	Lock-in may be completely fine for your company, or a significant risk. It’s important from a business perspective to make this choice explicitly, and consider the cost, operational, business continuity, and competitive risks of being tied to AWS. AWS is such a dominant and reliable vendor, many companies are comfortable with using AWS to its full extent. Others can tell stories about the dangers of “cloud jail” when costs spiral.
	-	Generally, the more AWS services you use, the more lock-in you have to AWS — that is, the more engineering resources (time and money) it will take to change to other providers in the future.
	-	Basic services like virtual servers and standard databases are usually easy to migrate to other providers or on premises. Others like load balancers and IAM are specific to AWS but have close equivalents from other providers. The key thing to consider is whether engineers are architecting systems around specific AWS services that are not open source or relatively interchangeable. For example, Lambda, API Gateway, Kinesis, Redshift, and DynamoDB do not have substantially equivalent open source or commercial service equivalents, while EC2, RDS (MySQL or Postgres), EMR, and ElastiCache more or less do. (See more below, where these are noted with ⛓.)
-	**Combining AWS and other cloud providers:** Many customers combine AWS with other non-AWS services. For example, legacy systems or secure data might be in a managed hosting provider, while other systems are AWS. Or a company might only use S3 with another provider doing everything else. However small startups or projects starting fresh will typically stick to AWS or Google Cloud only.
-	**Hybrid cloud:** In larger enterprises, it is common to have hybrid deployments encompassing private cloud or on-premises servers and AWS — or other enterprise cloud providers like IBM/Bluemix, Microsoft/Azure, NetApp, or EMC.
-	**Major customers:** Who uses AWS and Google Cloud?
	-	AWS’s list of customers includes large numbers of mainstream online properties and major brands, such as Netflix, Pinterest, Spotify (moving to Google Cloud), Airbnb, Expedia, Yelp, Zynga, Comcast, Nokia, and Bristol-Myers Squibb.
	-	Azure’s list of customers includes companies such as NBC Universal, 3M and Honeywell Inc.
	-	Google Cloud’s list of customers is large as well, and includes a few mainstream sites, such as Snapchat, Best Buy, Domino’s, and Sony Music.

Back to top :arrow_up:
