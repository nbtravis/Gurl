# Gurl: grouping similar urls

This is an algorithm for grouping URLs with similar patterns that I developed while working on the Wortharead app. 

So, for example, if you scrape an entire blog website, you'll end up with a list of URLs, with some URLs corresponding to the actual blog posts and others corresponding to ads, other pages of the website, etc. Suppose you wanted to automatically select the blog posts URLs from the full set of URLs. This algorithm could be of service. Specifically, the largest (or in some cases, second largest) group will nearly always consist of the actual blog posts.

I'm not sure if other projects could benefit from this algorithm, but given the number of people scraping the web, who knows. So I plan to write up a short post describing the algorithm soon...
