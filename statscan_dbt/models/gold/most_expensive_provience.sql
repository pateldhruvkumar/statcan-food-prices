WITH latest_date AS
(
    SELECT 
        MAX(reference_date) AS max_date
    FROM 
        {{ ref('silver_average_price') }}
),
most_expensive_provience AS
(
    SELECT
        reference_date,
        geography_location,
        products,
        average_price,
        DENSE_RANK() OVER (PARTITION BY products ORDER BY average_price DESC) AS dns_rank
    FROM
        {{ ref('silver_average_price') }}
    WHERE
        reference_date = (SELECT max_date FROM latest_date) AND geography_location <> 'Canada'    
)

SELECT
    reference_date,
    geography_location,
    products,
    average_price,
    dns_rank
FROM
    most_expensive_provience
WHERE
    dns_rank < 4
ORDER BY
    products,
    dns_rank
