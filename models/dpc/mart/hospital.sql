{# DPC 退院患者調査に参加した病院の年度別の施設概要。
   1 行 = 年度 × 病院。年度の途中で合併した病院は合併前と合併後の 2 行を持つ。 #}

{{ config(materialized='table') }}

select
    fiscal_year,
    notification_number,
    serial_number,
    hospital_name,
    facility_group,
    hospital_category,
    prefecture_code,
    city_code,
    local_gov_code,
    dpc_beds,
    dpc_basic_fee,
    dpc_bed_ratio,
    rehabilitation_beds,
    community_care_beds,
    psychiatric_beds,
    long_term_care_beds,
    tuberculosis_beds,
    total_beds,
    months_submitted
from {{ ref('stg_hospital') }}
