SELECT
*
FROM  {{ source('statscan_analytics_source', 'source_average_price') }}
 