WITH price_change_over_year AS
(
    SELECT
        reference_date,
        geography_location,
        products,
        average_price,
        LAG(average_price, 12) OVER (PARTITION BY geography_location, products ORDER BY reference_date) AS prev_year_price
    FROM
        {{ ref('silver_average_price') }}
)
SELECT
    reference_date,
    geography_location,
    products,
    average_price,
    prev_year_price,
    average_price - prev_year_price AS price_change,
    ROUND((average_price - prev_year_price) / (NULLIF(prev_year_price, 0)) * 100, 2) as precentage_change
FROM
    price_change_over_year