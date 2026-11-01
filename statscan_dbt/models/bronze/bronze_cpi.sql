SELECT
*
FROM  {{ source('statscan_analytics_source', 'source_cpi') }}