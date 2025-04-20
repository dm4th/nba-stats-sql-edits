Hi Dario,

Thank you for reaching out! We've taken a look at your prompt along with your example data and database and I have a strategy to help your team improve the performance of your system. With a few changes to your prompting strategy, **we were able to generate successful SQL responses in 46.9% of your ground truth cases**, and 37.5% of an additional, larger set of synthetic cases we created for further testing. I've included the code and a link to a quick analysis of the results in this email.

Below you'll find a detailed explanation of our recommendations and implementation strategy. I've also included relevant resources:

- [Link to GitHub Repo](https://github.com/dm4th/nba-stats-sql-edits/tree/main)
- [Link to Dataset Analysis](https://docs.google.com/spreadsheets/d/1QqkQboqnzTHiAZrysTd1a_n83Kf4ZzuBfvw1jOHAUaI/edit?usp=sharing)

Please feel free to let me know if you have any questions or need clarification on any of the points discussed.

Best regards,
Daniel Mathieson

-------------

**_Implementation Recommendations:_**

Our analysis suggests including the following key elements in your system prompt:

1. **Explicit Rules to Only Write SQL and Nothing Else:** Claude will try to be as helpful as possible given your prompt, and that often means including explanations for the code it is writing in your case. By steering Claude from providing any text but valid SQL, it will make it much easier to parse the query Claude wants to run and improve success rates in your system.

2. **Include a Definition of the Tables & Schema for each Table:** I've written some code to query your sqlite database and create a string that you can inject into your system prompt at run-time. This will give Claude much needed context regarding which tables and columns are even queryable in your database and avoid hallucinations.

3. **Include a Few Successful Prompt <> Query Pairs:** Giving Claude a few examples of the type of outputs you're looking for can be very helpful in steering the results in the direction you'd like.

I've prepared a GitHub repository with the code to help you implement these recommendations. The repository includes a README with implementation instructions. The code is designed to be configurable, allowing your team to continue refining and re-evaluating your prompts as you develop your text-to-sql application.

**_Next Steps for Further Improvement:_**

1. **Provide Style Guidelines for Numbers and Return Sets:** The lowest-performing query-type in our analysis was "aggregation" at 32.0% accuracy, primarily due to rounding errors on average calculations. Adding more specific language to provide numbers rounded to the 2nd decimal place would likely improve accuracy by approximately 10%.

2. **Retrieval-Augmented-Generation (RAG) over your Ground Truth Queries:** Instead of injecting a few hard-coded examples into the system prompt, you could implement a more refined RAG pipeline over your ground truth queries against the user prompt. This would help Claude match style and better understand which tables to use in specific situations. The synthetic data provided would be particularly useful for testing this strategy.

3. **Query Error Handling:** When Claude wrote queries that caused database errors, these were marked as misses in our dataset. Implementing a second prompting step to allow Claude to see and correct its mistakes would likely significantly improve performance.