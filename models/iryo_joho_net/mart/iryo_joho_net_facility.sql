{# 医療情報ネットに載っている全国の病院・診療所・歯科診療所・助産所・薬局。1 行 = 1 施設。 #}

{{ config(materialized='table', alias='facility') }}

select
    id,
    facility_type,
    name,
    name_kana,
    short_name,
    short_name_kana,
    name_en,
    prefecture_code,
    city_code,
    {{ local_government_code('city_code') }} as local_gov_code,
    address,
    latitude,
    longitude,
    case
        when latitude is not null and longitude is not null
        then ST_Point(longitude, latitude)
    end as geometry,
    url,
    general_beds,
    long_term_care_beds,
    long_term_care_medical_insurance_beds,
    long_term_care_ltci_beds,
    psychiatric_beds,
    tuberculosis_beds,
    infectious_beds,
    total_beds,
    as_of
from {{ ref('stg_iryo_joho_net_facility') }}
order by city_code, id
