# StatCan Food Prices Pipeline: Interview Story in STAR Format

*For Data Analyst and Data Engineering interviews*

---

## The main STAR story (2–3 minutes)

### S: Situation
Grocery prices in Canada rose sharply, and I wanted to know **which items were rising, by how much and in which provinces**. Statistics Canada publishes this data for free: monthly average retail prices for about **110 products in 13 regions**, plus the Consumer Price Index. But it only comes as **large flat CSV files**, and the CPI file goes back to 1914. The raw data couldn't answer simple questions like "what were the top 10 price increases this year?"

### T: Task
My goal was to turn those raw government files into a **dashboard people could trust**. I wanted to build it the way a production data team would: automated, re-runnable, secure and layered. I set three requirements:
1. Answer four business questions: the change from last month, the change from last year, the top 10 increases, and the most expensive provinces.
2. Make every step safe to re-run without creating duplicates.
3. Keep credentials out of the code.

### A: Action
I built an end-to-end pipeline: **CSV → Python → AWS S3 → Snowflake → dbt (Bronze / Silver / Gold) → Power BI**.

**Ingestion (Python + S3)**
- I split the raw files by year (2017–2026) with pandas. A **row-count check** confirms the yearly files add up to the original total, so no rows were lost.
- I uploaded the files to S3 with boto3, using Hive-style partitions such as `landing/average-price/year=2024/`.

**Loading (Snowflake)**
- Snowflake reads S3 through a **storage integration** (IAM role), so there are no access keys in SQL.
- Tables are created from the CSV headers with `INFER_SCHEMA`, so I didn't write the table definitions by hand.
- `COPY INTO` remembers which files it has loaded, so re-running it is **safe and creates no duplicates**.

**Transformation (dbt, medallion layers)**
- **Bronze:** a raw copy of the source data.
- **Silver:** cleaned and typed data. `TRY_CAST` and `TRY_TO_DATE` turn bad values into NULL instead of failing the run.
- **Gold:** business metrics built with window functions: `LAG()` for month-over-month change, `LAG(…, 12)` for year-over-year change, `DENSE_RANK()` for the rankings, and rolling 3- and 12-month averages.
- A custom macro writes the models to the schemas `BRONZE`, `SILVER` and `GOLD` instead of dbt's default `PUBLIC_BRONZE` style names.

**Fixing data problems that didn't cause errors** (the most important part of the work)
- **Hidden spaces:** 11 product names had a trailing space (`"Tofu, 350 grams "`), which split one product into two. I fixed it with `TRIM()` in Silver.
- **Missing prices ranked first:** Snowflake puts NULLs first in a descending sort, so a province with *no price* ranked as the most expensive. I added an `IS NOT NULL` filter.
- **Misleading averages:** a "12-month average" with only 1 month of data is wrong. I count the rows in each window and only show the average when the window is full.
- **Divide-by-zero:** I used `NULLIF(prev_price, 0)` in every percentage calculation.

**Presentation**
- I built a Power BI dashboard on the Gold tables, with slicers for product, month and province.
- I also built an interactive web explorer that follows one price row through every step of the pipeline.

### R: Result
- About **141,000 price rows and 236,000 CPI rows** (Jan 2017 – Aug 2026) now flow from raw files to a dashboard, and every step can be safely re-run.
- The dashboard answers the four business questions in seconds. For August 2026, the top year-over-year increases were:
  - **Beef striploin: +16.6%** ($30.80 → $35.90/kg)
  - **Canned salmon: +15.5%**
  - **Romaine lettuce: +14.4%**
- I found and fixed **four problems that would each have given wrong answers without any error**.
- The project and the explorer are live at `read-me-statcan.dhruvpatel.app` and `artifact-statcan.dhruvpatel.app`.

**Lesson learned:** *"A pipeline that runs is not the same as a pipeline that's right."* Now I always check whitespace and NULLs before I trust a key, check how a ranking orders NULLs, and reconcile row counts between layers.

**Next steps:** add dbt tests (`not_null`, `unique`), switch to incremental models, schedule monthly refreshes with Airflow or GitHub Actions, and compare food prices with the overall CPI.

---

## The 30-second STAR version

> **S:** Grocery prices in Canada were rising, but Statistics Canada's data only comes as huge raw CSV files.
> **T:** I wanted to turn it into a dashboard people could trust, built like a production pipeline.
> **A:** I built Python → S3 → Snowflake → dbt Bronze/Silver/Gold → Power BI, and fixed hidden problems along the way, such as trailing spaces that split products and NULLs that ranked as the most expensive.
> **R:** About 141,000 price rows now feed a dashboard that answers four questions in seconds. For example, it shows beef striploin rose 16.6% in a year.

---

## Short STAR stories for behavioral questions

These are smaller stories from the same project for common "Tell me about a time…" questions.

### "Tell me about a time you found a data quality issue."
- **S:** My product slicers in Power BI showed what looked like duplicate products, and some time series had gaps.
- **T:** Find the cause before trusting any of the metrics.
- **A:** I compared distinct product names and their lengths, and found that 11 names published by StatCan ended in a space. I added `TRIM()` in the Silver layer, so every model downstream gets clean keys.
- **R:** The duplicates disappeared, the time series became continuous, and the fix lives in one place instead of in every report.

### "Tell me about a time your results were wrong but nothing failed."
- **S:** My "3 most expensive provinces for each product" model ran without errors.
- **T:** Check that the output made sense before putting it on the dashboard.
- **A:** I spot-checked the top results and saw provinces with no price ranked #1. The cause was that Snowflake sorts NULLs first in a descending order. I added `average_price IS NOT NULL` to the query.
- **R:** The rankings became correct, and I now check NULL ordering whenever I write a ranking query.

### "Tell me about a time you designed for reliability."
- **S:** The pipeline loads files from S3 into Snowflake, and I would need to re-run it often while developing.
- **T:** Make sure re-runs never create duplicate rows and that one bad value can't stop the whole run.
- **A:** I used `COPY INTO`, which skips files it has already loaded, `TRY_CAST` to turn bad values into NULL, and a row-count check after splitting the files.
- **R:** I could re-run any step at any time without cleaning up afterwards, and the row-count check confirmed no data was lost.

### "Tell me about a time you handled security or credentials."
- **S:** The pipeline connects to both AWS and Snowflake.
- **T:** Keep every credential out of the code repository.
- **A:** Snowflake reads S3 through a storage integration (IAM role), boto3 uses the standard AWS credential chain, and dbt profiles and `.env` files are git-ignored.
- **R:** The repository is public with no secrets in it.

### "What would you do differently?"
- **S:** I found the data problems by hand during development.
- **T:** Catch them automatically next time.
- **A:** I would add dbt tests (`not_null`, `unique`, `accepted_values`) from day one, and fix naming typos (`provience`) early, before they reach the BI layer.
- **R:** Problems would show up as failing tests in CI instead of wrong numbers on a dashboard.

---

## Which parts to emphasise for each role

| | **Data Analyst** | **Data Engineering** |
|---|---|---|
| **In the Situation** | The business question: "which groceries are rising?" | The raw data problem: huge flat files that aren't ready for analysis |
| **In the Action** | Window functions, the NULL ranking fix, dashboard design | S3 partitions, storage integration, safe `COPY INTO` reloads, medallion layers |
| **In the Result** | The findings (beef +16.6%) | A re-runnable, secure pipeline that's ready to automate |
| **Best behavioral story** | "Results were wrong but nothing failed" | "Designed for reliability" |

---

## Delivery tips
- **Keep about 60% of your time on the Action**, and spend most of that on the data problems you fixed. That's where you show judgment.
- **Always end the Result with a number** (141,000 rows, +16.6%, 4 problems fixed).
- **Say "I", not "we".** This was your project.
- **After the Result, give the lesson in one sentence**, then stop and let them ask questions.
