SELECT
    TRY_TO_DATE(REF_DATE || '-01', 'YYYY-MM-DD') AS reference_date,
    CAST(GEO AS VARCHAR(255)) AS geography_location,
    CAST(DGUID AS VARCHAR(255)) AS dguid,
    CAST("Products and product groups" AS VARCHAR(255)) AS products,
    CAST(COORDINATE AS VARCHAR(255)) AS coordinates,
    TRY_CAST(VALUE::VARCHAR AS NUMBER(6,2)) AS cpi_index
FROM
    {{ ref('bronze_cpi') }}
