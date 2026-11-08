{# 病院 × MDC × 手術の有無 の退院患者数。
   1 行 = 年度 × 病院 × MDC × 手術の有無。10 症例未満と 0 件の組み合わせは行が無い。 #}

{{ config(materialized='table') }}

select
    fiscal_year,
    notification_number,
    serial_number,
    mdc,
    mdc_name,
    has_surgery,
    patients
from {{ ref('stg_mdc_patients') }}
