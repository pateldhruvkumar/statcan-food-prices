WITH price_change AS
(
    SELECT
        reference_date,
        geography_location,
        products,
        average_price,
        LAG(average_price) OVER (PARTITION BY geography_location, products ORDER BY reference_date) AS prev_month_price
    FROM
        {{ ref('silver_average_price') }}
)

SELECT
    reference_date,
    geography_location,
    products,
    average_price,
    prev_month_price,
    average_price - prev_month_price AS price_change,
    ROUND(((average_price - prev_month_price) / (NULLIF(prev_month_price, 0))) * 100, 2) AS pct_change
FROM
    price_change
