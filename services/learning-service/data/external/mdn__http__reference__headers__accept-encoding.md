<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Headers -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Accept-Encoding -->
# Accept-Encoding header

The HTTP **`Accept-Encoding`** request and response header indicates the content encoding (usually a compression algorithm) that the sender can understand.
In requests, the server uses content negotiation to select one of the encoding proposals from the client and informs the client of that choice with the Content-Encoding response header.
In responses, it provides information about which content encodings the server can understand in messages to the requested resource, so that the encoding can be used in subsequent requests to the resource.
For example, `Accept-Encoding` is included in a 415 Unsupported Media Type response if a request to a resource (e.g., PUT) used an unsupported encoding.

Even if both the client and the server support the same compression algorithms, the server may choose not to compress the body of a response if the `identity` value is also acceptable.
This happens in two common cases:

1. The data is already compressed, meaning a second round of compression will not reduce the transmitted data size, and may actually increase the size of the content in some cases.
   This is true for pre-compressed image formats (JPEG, for instance).
2. The server is overloaded and cannot allocate computing resources to perform the compression. For example, Microsoft recommends not to compress if a server uses more than 80% of its computational power.

As long as the `identity;q=0` or `*;q=0` directives do not explicitly forbid the `identity` value that means no encoding, the server must never return a 406 Not Acceptable error.

> [!NOTE]
> IANA maintains a list of official content encodings.
> The `bzip` and `bzip2` encodings are non-standard, but may be used in some cases, particularly for legacy support.

      Header type
      Request header, Response header

      Forbidden request header
      Yes

## Syntax

```http
Accept-Encoding: gzip
Accept-Encoding: compress
Accept-Encoding: deflate
Accept-Encoding: br
Accept-Encoding: zstd
Accept-Encoding: dcb
Accept-Encoding: dcz
Accept-Encoding: identity
Accept-Encoding: *

// Multiple algorithms, weighted with the quality value syntax:
Accept-Encoding: deflate, gzip;q=1.0, *;q=0.5
```

## Directives

- `gzip`
  - : A compression format that uses the Lempel-Ziv coding (LZ77) with a 32-bit CRC.
- `compress`
  - : A compression format that uses the Lempel-Ziv-Welch (LZW) algorithm.
- `deflate`
  - : A compression format that uses the zlib structure with the _deflate_ compression algorithm.
- `br`
  - : A compression format that uses the Brotli algorithm.
- `zstd`
  - : A compression format that uses the Zstandard algorithm.
- `dcb`
  - : A format that uses the Dictionary-Compressed Brotli algorithm. See Compression Dictionary Transport.
- `dcz`
  - : A format that uses the Dictionary-Compressed Zstandard algorithm. See Compression Dictionary Transport.
- `identity`
  - : Indicates the identity function (that is, without modification or compression). This value is always considered as acceptable, even if omitted.
- `*` (wildcard)
  - : Matches any content encoding not already listed in the header. This is the default value if the header is not present. This directive does not suggest that any algorithm is supported but indicates that no preference is expressed.
- `;q=` (qvalues weighting)
  - : Any value is placed in an order of preference expressed using a relative quality value called _weight_.

## Examples

### Default Accept-Encoding values

Browser navigation typically has the following `Accept-Encoding` request header value:

```http
GET /en-US/ HTTP/2
Host: developer.mozilla.org
Accept-Encoding: gzip, deflate, br, zstd
```

### Weighted Accept-Encoding values

The following header shows `Accept-Encoding` preferences using a quality value between `0` (lowest priority) and `1` (highest-priority).
Brotli compression is weighted at `1.0`, making `br` the client's first choice, followed by `gzip` at `0.8` priority, and then any other content encoding at `0.1`:

```http
Accept-Encoding: br;q=1.0, gzip;q=0.8, *;q=0.1
```
