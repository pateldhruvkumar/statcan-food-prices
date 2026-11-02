WITH latest_date AS
(
    SELECT 
        MAX(reference_date) AS max_date 
    FROM
        {{ ref('price_change_over_years') }}
),

filter_products AS 
(
    SELECT
        reference_date,
        geography_location,
        products,
        prev_year_price,
        average_price,
        price_change,
        precentage_change,
        DENSE_RANK() OVER (ORDER BY precentage_change DESC) AS dns_rank
    FROM
        {{ ref('price_change_over_years') }}
    WHERE
        reference_date = (SELECT max_date FROM latest_date)
        AND geography_location = 'Canada'
        AND precentage_change IS NOT NULL
)

SELECT
    reference_date,
    geography_location,
    products,
    prev_year_price,
    average_price,
    price_change,
    precentage_change,
    dns_rank
FROM
    filter_products
WHERE
    dns_rank <= 10
ORDER BY
    dns_rank