<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#redshift-gotchas-and-limitations -->
# AWS Guide: Redshift Gotchas and Limitations

-	❗⏱While Redshift can handle heavy queries well, it does not scale horizontally, i.e. does not handle multiple queries in parallel. Therefore, if you expect a high parallel load, consider replicating or (if possible) sharding your data across multiple clusters.
-	🔸 The leader node, which manages communications with client programs and all communication with compute nodes, is the single point of failure.
-	⏱Although most Redshift queries parallelize well at the compute node level, certain stages are executed on the leader node, which can become the bottleneck.
-	🔹Redshift data commit transactions are very expensive and serialized at the cluster level. Therefore, consider grouping multiple mutation commands (COPY/INSERT/UPDATE) commands into a single transaction whenever possible.
-	🔹Redshift does not support multi-AZ deployments. Building multi-AZ clusters is not trivial. Here is an example using Kinesis.
-	🔸Beware of storing multiple small tables in Redshift. The way Redshift tables are laid out on disk makes it impractical. The minimum space required to store a table (in MB) is nodes * slices/node * columns. For example, on a 16 node cluster an empty table with 20 columns will occupy 640MB on disk.
-	⏱ Query performance degrades significantly during data ingestion. WLM (Workload Management) tweaks help to some extent. However, if you need consistent read performance, consider having replica clusters (at the extra cost) and swap them during update.
-	❗ Never resize a live cluster. The resize operation can take hours depending on the dataset size. In rare cases, the operation may also get stuck and you'll end up having a non-functional cluster. The safer approach is to create a new cluster from a snapshot, resize the new cluster and shut down the old one.
-	🔸Redshift has **reserved keywords** that are not present in Postgres (see full list here). Watch out for DELTA (Delta Encodings).
-	🔸Redshift does not support many Postgres functions, most notably several date/time-related and aggregation functions. See the full list here.
-	🔸 Uniqueness, primary key, and foreign key constraints on Redshift tables are informational only and are not enforced. They are, however, used by the query optimizer to generate query plans. `NOT NULL` column constraints are enforced. See here for more information on defining constraints.
-	🔸Compression on sort key can result in significant performance impact. So if your Redshift queries involving sort key(s) are slow, you might want to consider removing compression on a sort key.
-	🔹 Choosing a sort key is very important since you can not change a table’s sort key after it is created. If you need to change the sort or distribution key of a table, you need to create a new table with the new key and move your data into it with a query like “insert into new_table select * from old_table”.
-	❗🚪 When moving data with a query that looks like “insert into x select from y”, you need to have twice as much disk space available as table “y” takes up on the cluster’s disks. Redshift first copies the data to disk and then to the new table. Here is a good article on how to this for big tables.

EMR
---
