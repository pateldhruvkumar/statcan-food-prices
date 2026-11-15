# The Story of the StatCan Food Prices Pipeline

*An interview story for Data Analyst and Data Engineering roles*

---

## The 30-second version (for "Tell me about a project")

> "Grocery prices in Canada kept going up, and I wanted to know *which* items were rising, by how much, and where. Statistics Canada publishes the data, but only as huge flat CSVs. So I built an end-to-end pipeline: Python splits and uploads the files to an S3 data lake, Snowflake loads them, dbt cleans and models them in Bronze, Silver and Gold layers, and Power BI shows the results. That's about 140,000 price rows covering 110 products in 13 regions from 2017 to 2026. For example, it showed that beef striploin rose about 17% in a year, from $30.80 to $35.90 a kilo. The interesting part wasn't the tools. It was the small data problems that would quietly have given wrong answers."

---

## The full story (2–3 minutes)

### 1. The hook: a question everyone has

Every Canadian has looked at a grocery receipt and thought, *"Wasn't this cheaper last year?"* I wanted to answer that with data instead of a feeling.

Statistics Canada publishes the answer for free: monthly average retail prices for about 110 food and household items, for every province, plus the Consumer Price Index. But the data comes as **one giant CSV per table**. The CPI file alone goes back to 1914. You can't open it, filter it and get "top 10 price increases this year." It's raw material, not an answer.

So the real question became: **how do I turn a government CSV dump into something a person can trust and use in under a minute?**

### 2. The plan: build it like a real company would

I could have done everything in one pandas notebook. I chose to build it the way a production data team would, because that's the skill I wanted to practise:

**CSV → Python → AWS S3 → Snowflake → dbt (Bronze / Silver / Gold) → Power BI**

- **Python** splits the raw files by year (2017–2026), so loads are incremental and easy to manage.
- **S3** is the landing zone, with Hive-style partitions (`landing/average-price/year=2024/…`).
- **Snowflake** reads S3 through a **storage integration** (IAM role, so no keys in code), builds tables with `INFER_SCHEMA` and loads them with `COPY INTO`. Because `COPY INTO` remembers which files it has loaded, I can re-run it safely and it won't load the same file twice.
- **dbt** does the transformations in medallion layers: Bronze is a raw copy, Silver is cleaned and typed, Gold holds the business metrics.
- **Power BI** sits on the Gold tables, with slicers for product, month and province.

### 3. The conflict: the data looked fine and was quietly wrong

This is the part of the story I tell most, because it's what the job is really like.

**Problem 1: the invisible space.**
StatCan publishes **11 product names with a trailing space**, for example `"Tofu, 350 grams "`. You can't see it. But to a database, `"Tofu, 350 grams "` and `"Tofu, 350 grams"` are two different products. That splits a time series, breaks lookups and makes slicers show duplicates. The fix is one `TRIM()` in Silver. Finding it took real investigation.

**Problem 2: missing prices ranked as the most expensive.**
For "the 3 most expensive provinces for each product" I used `DENSE_RANK() … ORDER BY average_price DESC`. Snowflake sorts **NULLs first** in descending order, so a province with *no price at all* came out as the "most expensive." The query ran without errors and the answer was wrong. I added an `average_price IS NOT NULL` filter, and now I always ask how my ranking treats NULLs.

**Problem 3: averages that lie.**
A 12-month moving average for the very first month of data is really a 1-month average with a misleading label. I count the rows in each window and only report the average when the window is full (3 or 12 months). An honest blank is better than a confident wrong number.

**Problem 4: protecting against bad values and silent data loss.**
- In Silver I used `TRY_CAST` and `TRY_TO_DATE`, so one bad value becomes `NULL` instead of failing the whole run.
- I used `NULLIF(prev_price, 0)` so a zero price can't cause divide-by-zero errors.
- When splitting by year, the script checks that the **sum of the yearly row counts equals the original row count**. It's a simple completeness check that no row was dropped.

### 4. The resolution: a dashboard you can trust

The final Gold layer answers four clear questions:

| Question | Technique |
|---|---|
| How much did the price change from last month? | `LAG()` over province + product |
| How much did it change from the same month last year? | `LAG(…, 12)` |
| Which 10 products rose the most in Canada? | `DENSE_RANK()` on YoY % for the latest month |
| Which provinces are the most expensive for each product? | `DENSE_RANK()` partitioned by product |

For August 2026 the top year-over-year increases were:
- **Beef striploin:** +16.6% ($30.80 → $35.90/kg)
- **Canned salmon:** +15.5%
- **Romaine lettuce:** +14.4%
- **Salmon:** +14.2%

To make the project easy to explain, I also built an **interactive pipeline explorer** that follows one price row through every step, from raw CSV to Gold metric. It's live at `artifact-statcan.dhruvpatel.app`, with a write-up at `read-me-statcan.dhruvpatel.app`.

### 5. The lesson: the moral of the story

> **"A pipeline that runs is not the same as a pipeline that's right."**

Every bug I found ran successfully. No errors, no red text, just wrong answers. That changed how I work. I now check whitespace and nulls before I trust a key, I check how a ranking orders NULLs, and I reconcile row counts between layers.

### 6. What's next (shows maturity, not weakness)

- Add **dbt tests** (`not_null`, `unique`, `accepted_values`) so these checks run automatically.
- Make the models **incremental**, so each month only new data is processed.
- **Orchestrate** monthly refreshes (Airflow or GitHub Actions) instead of running steps by hand.
- Use the CPI data I already modelled to compare **food prices with overall inflation**.

---

## Tailor the emphasis to the role

| | **Data Analyst interview** | **Data Engineering interview** |
|---|---|---|
| **Lead with** | The business question and the findings (beef +16.6%) | The architecture and *why* each layer exists |
| **Deep-dive on** | Window functions (`LAG`, `DENSE_RANK`, rolling averages), the NULL ranking bug, dashboard design | S3 partitioning, storage integration, idempotent `COPY INTO`, medallion layers, the dbt schema macro |
| **Best bug to tell** | NULLs ranked as "most expensive" | Trailing spaces splitting product keys |
| **Close with** | "I turned a raw government file into answers anyone can use in seconds." | "I built it to be re-runnable, secure and ready to automate." |

---

## Likely follow-up questions (have these ready)

1. **"Why Bronze, Silver and Gold instead of one transform?"**
   Each layer has one job. Bronze keeps the raw data so I can always reprocess it. Silver is the single cleaned source of truth. Gold is shaped for one business question. If a metric looks wrong, I can trace it back layer by layer.

2. **"Why split by year?"**
   Smaller files load in parallel and the S3 layout is easy to browse. When new data arrives, only the current year's file changes. It also made the completeness check easy.

3. **"How do you avoid loading duplicates?"**
   `COPY INTO` keeps load metadata for each file, so re-running it skips files it has already loaded.

4. **"How do you handle credentials?"**
   Snowflake reads S3 through a storage integration (IAM role), so there are no keys in SQL. AWS credentials come from the standard credential chain, and dbt profiles are git-ignored.

5. **"Why `DENSE_RANK` and not `ROW_NUMBER`?"**
   If two products tie, both should appear, and the next rank shouldn't skip a number.

6. **"What would you do differently?"**
   Add dbt tests from day one, so the trailing-space and NULL issues would have been caught by a failing test rather than found by hand. Also fix early naming typos (`provience`), because they spread into the BI layer and become expensive to change.

---

## Storytelling tips for delivery

- **Start with the receipt, not the tech stack.** People remember a question they've asked themselves.
- **Use one number and repeat it** ("beef up 17%"). One concrete number sticks better than five.
- **Spend most of your time on the conflict.** Bugs that ran without errors show judgment, and judgment is what interviewers are hiring for.
- **End with the moral**, then stop talking and let them ask questions.
