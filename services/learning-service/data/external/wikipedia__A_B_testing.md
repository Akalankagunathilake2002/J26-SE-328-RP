<!-- role: Digital Marketing Executive -->
<!-- topic: Digital Marketing -->
<!-- source: Wikipedia (Wikipedia contributors) -->
<!-- license: CC BY-SA 4.0 -->
<!-- url: https://en.wikipedia.org/wiki/A/B_testing -->
# A/B testing

A/B testing (also known as bucket testing, split-run testing or split testing) is a user-experience research method. A/B tests consist of a randomized experiment that usually involves two variants (A and B), although the concept can be also extended to multiple variants of the same variable. It includes application of statistical hypothesis testing or "two-sample hypothesis testing" as used in the field of statistics. A/B testing is employed to compare multiple versions of a single variable, for example by testing a subject's response to variant A against variant B, and to determine which of the variants is more effective.
Multivariate testing or multinomial testing is similar to A/B testing but may test more than two versions at the same time or use more controls. Simple A/B tests are not valid for observational, quasi-experimental or other non-experimental situations—commonplace with survey data, offline data, and other, more complex phenomena.

## Definition
"A/B testing" is a shorthand for a simple randomized controlled experiment, in which a number of samples (e.g. A and B) of a single vector-variable are compared. A/B tests are widely considered the simplest form of controlled experiment, especially when they only involve two variants. However, by adding more variants to the test, its complexity grows.
The following example illustrates an A/B test with a single variable:
A company has a customer database of 2,000 people and launches an email campaign with a discount code in order to generate sales through its website. The company creates two versions of the email with different calls to action (the part of the copy that encourages customers to act—in the case of a sales campaign, make a purchase) and identifying promotional codes.

To 1,000 people, the company sends an email with the call to action stating "Offer ends this Saturday! Use code A1",
To the remaining 1,000 people, it sends an email with the call to action stating "Offer ends soon! Use code B1".
All other elements of the emails' copy and layout are identical.
The company then monitors which campaign has the higher success rate by analyzing the use of the promotional codes. The email using the code A1 has a 5% response rate (50 of the 1,000 people emailed used the code to buy a product), and the email using the code B1 has a 3% response rate (30 of the recipients used the code to buy a product). The company therefore determines that in this instance, the first call to action is more effective and will use it in future sales. A more nuanced approach would involve applying statistical testing to determine whether the differences in response rates between A1 and B1 were statistically significant (highly likely that the differences are real, repeatable and not the result of random chance).
In the previous example, the purpose of the test is to determine the more effective strategy for encouraging customers to make a purchase. If, however, the aim of the test had been to determine which email would generate a higher click-through rate (the percentage of people who actually click the link after receiving the email), the results might have been different.
For example, even though more of the customers receiving the code B1 accessed the website, because the call to action did not state the end date of the promotion, many recipients may feel no urgency to make an immediate purchase. Consequently, if the purpose of the test had been simply to determine which email would bring more traffic to the website, the email containing code B1 might well have been more successful. An A/B test should have a defined, measurable outcome, such as sales converted, clickthrough rate or registration rate.

## Common test statistics
Two-sample hypothesis tests are appropriate for comparing the two samples in which the samples are divided by the two control cases in the experiment. Z-tests are appropriate for comparing means under stringent conditions regarding normality and a known standard deviation. Student's t-tests are appropriate for comparing means under relaxed conditions when less is assumed. Welch's t-test assumes the least and is therefore the most commonly used two-sample hypothesis test in which the mean of a metric is to be optimized. While the mean of the variable to be optimized is the most common choice of estimator, others are regularly used.
Fisher's exact test can be employed to compare two binomial distributions, such as a click-through rate.

## Segmentation and targeting
A/B tests most commonly apply the same variant (e.g., user interface element) with equal probability to all users. However, in some circumstances, responses to variants may be heterogeneous. While a variant A might have a higher response rate overall, variant B may have an even higher response rate within a specific segment of the customer base.
For instance, in the above example, the breakdown of the response rates by gender could have been:

In this case, while variant A attracted a higher overall response rate, variant B actually elicited a higher response rate among men.
As a result, the company might select a segmented strategy as a result of the A/B test, sending variant B to men and variant A to women in the future. In this example, a segmented strategy would yield a 30% increase in expected response rates from

        5
        %
        =

              40
              +
              10

              500
              +
              500

    {\textstyle 5\%={\frac {40+10}{500+500}}}

  to

        6.5
        %
        =

              40
              +
              25

              500
              +
              500

    {\textstyle 6.5\%={\frac {40+25}{500+500}}}

.
If segmented results are expected from the A/B test, the test should be properly designed at the outset to be evenly distributed across key customer attributes, such as gender. The test should contain a representative sample of men vs. women and assign men and women randomly to each “variant” (variant A vs. variant B). Failure to do so could lead to experiment bias and inaccurate conclusions.
This segmentation and targeting approach can be further generalized to include multiple customer attributes rather than a single customer attribute—for example, customers' age and gender—to identify more nuanced patterns that may exist in the test results.

## Tradeoffs
### Positives
The results of A/B tests are simple to interpret to create a clear picture of real user preferences, as they directly test one option over another. A/B tests can also provide answers to highly specific design questions. One example of this is Google's A/B testing with hyperlink colors. In order to optimize revenue, Google tested dozens of hyperlink hues to determine which colors attract the most clicks.

### Negatives
A/B tests are sensitive to variance; they require a large sample size in order to reduce standard error and produce a statistically significant result. In applications in which active users are abundant, such as with popular online social-media platforms, obtaining a large  sample size is trivial. In other cases, large sample sizes are obtained by increasing the experiment enrollment period. However, using a technique coined by Microsoft as Controlled Experiment Using Pre-Experiment Data (CUPED), variance from before the experiment start can be taken into account so that fewer samples are required to produce a statistically significant result.
Because of its nature as an experiment, running an A/B test introduces the risk of wasted time and resources if the test produces unwanted or unhelpful results.
In December 2018, representatives with experience in large-scale A/B testing from 13 organizations (Airbnb, Amazon, Booking.com, Facebook, Google, LinkedIn, Lyft, Microsoft, Netflix, Twitter, Uber and Stanford University) summarized the top challenges in a paper. The challenges were grouped into four areas: analysis, engineering and culture, deviations from traditional A/B tests and data quality.

## History
It is difficult to definitively establish when A/B testing was first used. The first randomized double-blind trial to assess the effectiveness of a homeopathic drug occurred in 1835. Experimentation with advertising campaigns, which has been compared to modern A/B testing, began in the early 20th century. The advertising pioneer Claude Hopkins used promotional coupons to test the effectiveness of his campaigns. However, this process, which Hopkins described in his 1923 book Scientific Advertising, did not incorporate concepts such as statistical significance and the null hypothesis, which are used in statistical hypothesis testing. Modern statistical methods for assessing the significance of sample data were developed separately in the same period. This work was conducted in 1908 by William Sealy Gosset when he altered the Z-test to create Student's t-test.
With the growth of the internet, new ways to sample populations have become available. Google engineers ran their first A/B test in 2000 to determine the optimum number of results to display in its search-engine results. The first test was unsuccessful because of glitches that resulted from slow loading times. Later A/B testing research was more advanced, but the foundation and underlying principles generally remain the same, and in 2011, Google ran more than 7,000 different A/B tests.
In 2012, a Microsoft employee working on the search engine Bing created an experiment to test different methods of displaying advertising headlines. Within hours, the alternative format produced a revenue increase of 12% with no impact on user-experience metrics. Today, major software companies such as Microsoft and Google each conduct over 10,000 A/B tests annually.
A/B testing has been claimed by some to be a change in philosophy and business-strategy in certain niches, although the approach is identical to a between-subjects design, which is commonly used in a variety of research traditions. A/B testing as a philosophy of web development brings the field into line with a broader movement toward evidence-based practice.
Many companies now use the "designed experiment" approach to making marketing decisions, with the expectation that relevant sample results can improve positive conversion results. It is an increasingly common practice as the tools and expertise grow in this area. As a result, more marketing teams now use A/B testing to guide decisions, matching the rigor of the test to measured hypotheses and measuring impact on outcomes such as conversions, revenue, and downstream conversion.

## Applications
### Social media
A/B tests have been used by large social-media sites such as LinkedIn, Facebook and Instagram to understand user engagement and satisfaction of online features, such as a new feature or product. A/B tests have also been used to conduct complex experiments on subjects such as network effects when users are offline, how online services affect user actions and how users influence one another.

### E-commerce
On an e-commerce website, the purchase funnel is typically a helpful candidate for A/B testing, as even marginal decreases in drop-off rates can represent a significant gain in sales. Significant improvements can be sometimes seen through testing elements such as copy text, layouts, images and colors. In these tests, users only see one of two versions, as the goal is to discover which of the two versions is preferable.

### Product pricing
A/B testing can be used to determine the right price for a product, which is one of the most difficult challenges faced when a new product or service is launched. A/B testing (especially valid for digital goods) is an effective mechanism to identify the price point that maximizes the total revenue.

### Political A/B testing
A/B tests have also been used by political campaigns. In 2007, Barack Obama's presidential campaign used A/B testing to garner online attraction and understand what voters wanted to see from Obama. For example, Obama's team tested four distinct buttons on their website that led users to register for newsletters. Additionally, the team used six different accompanying images to attract users.

### HTTP routing and API feature testing
A/B testing is commonly employed when deploying a newer version of an API. For real-time user experience testing, an HTTP layer 7 reverse proxy is configured in such a way that n% of the HTTP traffic is routed to the newer version of the backend instance, while the remaining 100-n% of HTTP traffic hits the (stable) older version of the backend HTTP application service. This is usually achieved to limit the exposure of customers to a newer backend instance such that, if there is a bug with the newer version, only n% of the total user agents or clients are affected while others are routed to a stable backend, which is a common ingress control mechanism.
