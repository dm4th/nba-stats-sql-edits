Hi Dario,

Thank you for reaching out! We've taken a look at your prompt along with your example data and database and I have a strategy to help your team improve the performance of your system. With a few changes to your prompting strategy, **we were able to generate successful SQL responses in 46.9% of your ground truth cases**, and 37.5% of an additional, larger set of synthetic cases we created for further testing. I've included the code and a link to a quick analysis of the results in this email. You can find a more thorough explanation of our recommendations in the post-script below as well.

Please feel free to let me know if you have any further questions. Go Warriors!

- [Link to GitHub Repo](https://github.com/dm4th/nba-stats-sql-edits/tree/main)
- [Link to Dataset Analysis](https://docs.google.com/spreadsheets/d/1QqkQboqnzTHiAZrysTd1a_n83Kf4ZzuBfvw1jOHAUaI/edit?usp=sharing)

Best,
Daniel Mathieson

-------------

**_Prompting Recommendations:_**

My recommendation is to include a few key items to the system prompt of the application your analysts are using with the following pieces of context included:
1. **Explicit Rules to Only Write SQL and Nothing Else:** Claude will try to be as helpful as possible given your prompt, and that often means including explanations for the code it is writing in your case. By steering Claude from providing any text but valid SQL, it will make it much easier to parse the query Claude wants to run and improve success rates in your system.
2. **Include a Definition of the Tables & Schema for each Table:** I've written some code to query your sqlite database and create a string that you can inject into your system prompt at run-time. This will give Claude much needed context regarding which tables and columns are even queryable in your database and avoid hallucinations.
3. **Include a Few Successful Prompt <> Query Pairs:** Giving Claude a few examples of the type of outputs you're looking for can be very helpful in steering the results in the direction you'd like. 

Attached is a link to a small GitHub repository I put together with the code to more easily adopt these recommendations. If your team has any trouble with these files please let me know, some brief instructions are in the readme. The code in the repository should be configurable to continue refining and re-evaluating your prompts as you continue to build out your text-to-sql application. Here are some recommendations on what to try next:
1. **Provide Style Guidelines for Numbers and Return Sets:** The lowest-performing query-type in my analysis was "aggregation" at 32.0% accuracy primarily due to rounding errors on average calculations. Adding more specific language to provide numbers rounded to the 2nd decimal place would likely improve accuracy by about 10%.
2. **Retrieval-Augemented-Generation (RAG) over your Ground Truth Queries:** Instead of injecting a few hard-coded exampled into the system prompt as I did, you could find more relevant examples to show Claude by doing a more refined RAG pipeline over your ground truth queries against the user prompt. This would steer Claude towards matching style as well as having a better understanding of which tables to use in specific situations. You could leverage the synthetic data provided to test this strategy in particular.
3. **Query Error Handling:** Anytime Claude wrote a query that caused a database error, I labeled the question as a miss in my dataset. If you added a second prompting step to let Claude see it's mistake and try to correct it, you'd likely have greatly improved performance.