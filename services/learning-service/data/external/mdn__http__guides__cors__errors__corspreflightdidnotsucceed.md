<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Guides -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS/Errors/CORSPreflightDidNotSucceed -->
# Reason: CORS preflight channel did not succeed

## Reason

```plain
Reason: CORS preflight channel did not succeed
```

## What went wrong?

The CORS request requires preflight, preflighting could not be
performed. There are a couple of reasons why preflighting might fail:

- A cross-site request has previously been performed that already did a preflight, and
  doing the preflight again is not permitted. Make sure your code only preflights once
  per connection.
- The preflight request suffered any kind of networking error that might ordinarily
  occur.

If the server is not under your control, see Client-side considerations for alternative approaches.
