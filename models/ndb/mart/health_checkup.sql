{# 特定健診 検査値の都道府県別・性年齢階級別分布。
   1 行 = 検査項目 × 都道府県 × 検査値階層 × 性 × 年齢階級 の受診者数。 #}

{{ config(materialized='table') }}

select
    fiscal_year,
    test_item,
    unit,
    prefecture_code,
    prefecture,
    sex,
    age_class,
    value_class,
    count
from {{ ref('stg_health_checkup') }}
