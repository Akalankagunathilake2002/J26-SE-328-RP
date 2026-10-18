<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#glacier-gotchas-and-limitations -->
# AWS Guide: Glacier Gotchas and Limitations

-	🔸Getting files off Glacier is glacially slow (typically 3-5 hours or more).
-	🔸Due to a fixed overhead per file (you pay per PUT or GET operation), uploading and downloading many small files on/to Glacier might be very expensive. There is also a 32k storage overhead per file. Hence it’s a good idea is to archive files before upload.
-	💸Be aware of the per-object costs of archiving S3 data to Glacier. It costs $0.05 per 1,000 requests. If you have large numbers of S3 objects of relatively small size, it will take time to reach a break-even point (initial archiving cost versus lower storage pricing).

Quicksight
----------
