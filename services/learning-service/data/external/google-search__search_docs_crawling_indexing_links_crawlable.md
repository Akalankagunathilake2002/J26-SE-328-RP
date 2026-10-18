<!-- role: Digital Marketing Executive -->
<!-- topic: SEO (Google Search Central) -->
<!-- source: Google Search Central -->
<!-- license: CC BY 4.0 -->
<!-- url: https://developers.google.com/search/docs/crawling-indexing/links-crawlable -->
# Link best practices for Google

Google uses links as a signal when determining the relevancy of pages and to find new pages
to crawl. Learn how to make your links crawlable so that Google can find other pages on your
site via the links on your page, and how to improve your anchor text so that it's easier for
people and Google to make sense of your content.

## Make your links crawlable

Generally, Google can only crawl your link if it's an `` HTML element (also
known as *anchor element*)
with an `href` attribute. Most links in other formats won't be parsed and extracted
by Google's crawlers. Google can't reliably extract URLs from `` elements
that don't have an `href` attribute or other tags that perform as links because of
script events. Here are examples of links that Google can and can't parse:

**Recommended (Google can parse)**

```sql

```

```sql

```

```sql

```

```sql

```

```sql

```

**Not recommended (but Google may still
attempt to parse this):**

```sql

```

```sql

```

```sql

```

Make sure that the URL in your `` element resolves into an actual web
address (meaning, it resembles a URI) that Google crawlers can send requests to, for example:

**Recommended (Google can resolve):**

```sql

```

```sql

```

```sql

```

**Not recommended (but Google may still
attempt to resolve this):**

```sql

```

```sql

```

## Anchor text placement

*Anchor text* (also known as *link text*) is the visible text of a link. This
text tells people and Google something about the page you're linking to. Place anchor text
between `` elements that Google can crawl.

**Good:**

> **ghost peppers**

**Bad (empty link text):**

>

As a fallback, Google can use the `title` attribute as anchor text if the
`` element is for some reason empty.

>

For images as links, Google uses the `alt` attribute of the `img` element
as anchor text, so be sure to add descriptive alt text to your images:

**Good:**

>

**Bad (empty alt text and empty link text):**

>

If you are using JavaScript to insert anchor text, use the URL Inspection Tool
to make sure it's present in the rendered HTML.

## Write good anchor text

Good anchor text is descriptive, reasonably concise, and relevant to the page that it's on
and to the page it links to. It provides context for the link, and sets the expectation for your readers.
The better your anchor text, the easier it is for people to
navigate your site and for Google to understand what the page you're linking to is about.

**Bad (too generic):**

> **Click here** to learn more.

> **Read more**.

> Learn more about our cheese on our **website**.

> We have an **article** that provides more background on how the cheese is made.

**Better (more descriptive):**

> For a full list of cheese available for purchase, see the **list of cheese types**.

**Bad (weirdly long):**

> Starting next Tuesday, the **Knitted
> Cow invites local residents of Wisconsin to their grand re-opening by also offering
> complimentary cow-shaped ice sculptures** to the first 20 customers.

**Better (more concise):**

> Starting next Tuesday, the **Knitted
> Cow invites local residents of Wisconsin** to their
> grand re-opening by also offering complimentary cow-shaped ice sculptures to the first 20 customers.

Write as naturally as possible, and resist the urge to cram every keyword that's related to
the page that you're linking to (remember, keyword stuffing
is a violation of our spam policies). Ask yourself, does the reader need these keywords to
understand the next page? If it feels like you're forcing keywords into the anchor text, then
it's probably too much.

Remember to give context to your links: the words before and after links matter, so pay
attention to the sentence as a whole. Don't chain up links next to each other; it's harder
for your readers to distinguish between links, and you lose surrounding text for each link.

**Bad (too many links next to each other):**

> I've written about cheese **so**
> **many**
> **times**
> **this**
> **year**.

**Better (links are spaced out with context):**

> I've written about cheese so many times this year: who can forget the **controversy over blue cheese and gorgonzola**, the
> **world's oldest brie**
> piece that won the Cheesiest Research Medal, the epic retelling of **The Lost Cheese**, and my personal favorite,
> **A Boy and His Cheese: a story of two unlikely friends**.

## Internal links: cross-reference your own content

You may usually think about linking in terms of pointing to external websites, but paying more attention to the anchor text used for internal links can help both people and Google make sense of your site more easily and find other pages on your site. Every page you care about should have a link from at least one other page on your site. Think about what other resources on your site could help your readers understand a given page on your site, and link to those pages in context.

## External links: link to other sites

Linking to other sites isn't something to be scared of; in fact, using external links can help
establish trustworthiness (for example, citing your sources). Link out to external sites when
it makes sense, and provide context to your readers about what they can expect.

**Good (citing your sources)**:

> According to a recent study from Swiss researchers, Emmental cheese wheels that were exposed
> to music had a milder flavor when compared to the control cheese wheels (which experienced no
> such musical treatment), with the full findings available in **Cheese
> in Surround Sound—a culinary art experiment**.

Use `nofollow`
only when you don't trust the source, and not for every external link on your site. For example,
you're a cheese enthusiast and someone published a story badmouthing your favorite cheese, so
you want to write an article in response; however, you don't want to give the site some of your
reputation from your link. This would be a good time to use `nofollow`.

If you were paid in some way for the link, qualify these links with
`sponsored`
or `nofollow`. If users can insert links on your site (for example, you have a
forum section or Q&A site), add `ugc`
or `nofollow` to these links too.
