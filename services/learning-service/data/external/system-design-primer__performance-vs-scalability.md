<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: System Design -->
<!-- source: The System Design Primer (Donne Martin) -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/donnemartin/system-design-primer#performance-vs-scalability -->
# System Design: Performance vs scalability

A service is **scalable** if it results in increased **performance** in a manner proportional to resources added. Generally, increasing performance means serving more units of work, but it can also be to handle larger units of work, such as when datasets grow.1

Another way to look at performance vs scalability:

* If you have a **performance** problem, your system is slow for a single user.
* If you have a **scalability** problem, your system is fast for a single user but slow under heavy load.

### Source(s) and further reading

* A word on scalability
* Scalability, availability, stability, patterns
