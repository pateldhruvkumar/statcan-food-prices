SELECT
    TRY_TO_DATE(REF_DATE || '-01', 'YYYY-MM-DD') AS reference_date,
    CAST(GEO AS VARCHAR(255)) AS geography_location,
    CAST(DGUID AS VARCHAR(255)) AS dguid,
    CAST("Products" AS VARCHAR(255)) AS products,
    CAST(COORDINATE AS VARCHAR(255)) AS coordinates,
    TRY_CAST(VALUE::VARCHAR AS NUMBER(6,2)) AS average_price
FROM
    {{ ref('bronze_average_price') }}
