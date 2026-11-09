{# 病院・診療所・歯科診療所が医療情報ネットで公表している診療科。1 行 = 施設 × 診療科。 #}

{{ config(materialized='table', alias='speciality') }}

select
    id,
    speciality_code,
    speciality_name,
    cast(as_of as DATE) as as_of
from {{ ref('raw_iryo_joho_net_speciality') }}
order by id, speciality_code
