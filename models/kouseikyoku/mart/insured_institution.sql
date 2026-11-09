{# 全国の保険医療機関・保険薬局。1 行 = 1 医療機関コード。
   医科と歯科の両方の指定を受けた機関は、点数表ごとに別のコードで 2 行を持つ。 #}

{{ config(materialized='table') }}

select
    medical_institution_code,
    prefecture_code,
    fee_schedule,
    institution_number,
    name,
    zip.zip3 || zip.zip4 as postal_code,
    address,
    phone,
    institution_type,
    categories,
    status,
    designated_on,
    designation_reason,
    designation_period_start,
    annex_institution_number,
    cast(list_sum([b.beds for b in beds if b.kind = '一般']) as INTEGER) as general_beds,
    cast(list_sum([b.beds for b in beds if b.kind = '療養']) as INTEGER) as long_term_care_beds,
    cast(list_sum([b.beds for b in beds if b.kind = '精神']) as INTEGER) as psychiatric_beds,
    cast(list_sum([b.beds for b in beds if b.kind = '結核']) as INTEGER) as tuberculosis_beds,
    cast(list_sum([b.beds for b in beds if b.kind = '感染']) as INTEGER) as infectious_beds,
    beds,
    departments,
    full_time_doctors,
    full_time_dentists,
    full_time_pharmacists,
    part_time_doctors,
    part_time_dentists,
    part_time_pharmacists,
    as_of,
    bureau
from {{ ref('stg_insured_institution') }}
order by medical_institution_code
