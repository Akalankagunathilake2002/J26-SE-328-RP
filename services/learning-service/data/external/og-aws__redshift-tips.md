<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#redshift-tips -->
# AWS Guide: Redshift Tips

-	Although Redshift is mostly Postgres-compatible, its SQL dialect and performance profile are different.
-	Redshift supports only 12 primitive data types. (List of unsupported Postgres types\)
-	It has a leader node and computation nodes (the leader node distributes queries to the computation ones). Note that some functions can be executed only on the lead node.
-	🔹Make sure to create a new cluster parameter group and option group for your database since the default parameter group does not allow dynamic configuration changes.
-	Major third-party BI tools support Redshift integration (see Quora).
-	Top 10 Performance Tuning Techniques for Amazon Redshift provides an excellent list of performance tuning techniques.
-	Amazon Redshift Utils contains useful utilities, scripts and views to simplify Redshift ops.
-	VACUUM regularly following a significant number of deletes or updates to reclaim space and improve query performance.
-	Avoid performing blanket VACUUM or ANALYZE operations at a cluster level. The checks on each table to determine whether VACUUM or ANALYZE action needs to be taken is wasteful. Only perform ANALYZE and VACUUM commands on the objects that require it. Utilize the Analyze & Vacuum Schema Utility to perform this work. The SQL to determine whether a table needs to be VACUUMed or ANALYZEd can be found in the Schema Utility README if you wish to create your own maintenance process.
-	Redshift provides various column compression options to optimize the stored data size. AWS strongly encourages users to use automatic compression at the COPY stage, when Redshift uses a sample of the data being ingested to analyze the column compression options. However, automatic compression can only be applied to an empty table with no data. Therefore, make sure the initial load batch is big enough to provide Redshift with a representative sample of the data (the default sample size is 100,000 rows).
-	Redshift uses columnar storage, hence it does not have indexing capabilities. You can, however, use distribution key and sortkey to improve performance. Redshift has two types of sort keys: compounding sort key and interleaved sort key.
-	A compound sort key is made up of all columns listed in the sort key definition. It is most useful when you have queries with operations using the prefix of the sortkey.
-	An interleaved sort key on the other hand gives equal weight to each column or a subset of columns in the sort key. So if you don't know ahead of time which column(s) you want to choose for sorting and filtering, this is a much better choice than the compound key. Here is an example using interleaved sort key.
-	🔸⏱ **Distribution strategies:** Since data in Redshift is physically distributed among nodes, choosing the right data **distribution key** and distribution style is crucial for adequate query performance. There are three possible distribution style settings — **EVEN** (the default), **KEY**, or **ALL**. Use KEY to collocate join key columns for tables which are joined in queries. Use ALL to place the data in small-sized tables on all cluster nodes.

Back to top :arrow_up:
