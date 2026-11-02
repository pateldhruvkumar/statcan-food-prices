WITH rolling_window AS
(
    SELECT
        reference_date,
        geography_location,
        products,
        average_price,
        AVG(average_price) OVER (
            PARTITION BY geography_location, products
            ORDER BY reference_date
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS avg_3_month,
        COUNT(average_price) OVER (
            PARTITION BY geography_location, products
            ORDER BY reference_date
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS months_in_3_window,
        AVG(average_price) OVER (
            PARTITION BY geography_location, products
            ORDER BY reference_date
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ) AS avg_12_month,
        COUNT(average_price) OVER (
            PARTITION BY geography_location, products
            ORDER BY reference_date
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ) AS months_in_12_window
    FROM
        {{ ref('silver_average_price') }}
)

SELECT
    reference_date,
    geography_location,
    products,
    average_price,
    CASE WHEN months_in_3_window = 3 THEN ROUND(avg_3_month, 2) END AS moving_avg_3_month,
    CASE WHEN months_in_12_window = 12 THEN ROUND(avg_12_month, 2) END AS moving_avg_12_month
FROM
    rolling_window
ORDER BY
    geography_location,
    products,
    reference_date