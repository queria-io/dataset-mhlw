{# 型変換と、所在地からの郵便番号の切り出し、種別の判定。
   所在地は「〒064－0807札幌市中央区…」の形で、郵便番号の区切りは全角の「－」。
   種別の欄は 病院・診療所・薬局 のほかに 特定機能・地域支援・総合病院・療養病床 が並ぶ。
   特定機能（特定機能病院）・地域支援（地域医療支援病院）・総合病院は病院の区分なので、
   「病院」と書かれていない局の行も病院とする。 #}

select
    medical_institution_code,
    prefecture_code,
    fee_schedule,
    replace(institution_number, '-', '') as institution_number,
    name,
    regexp_extract(address, '^〒(\d{3})[－-](\d{4})', ['zip3', 'zip4']) as zip,
    trim(regexp_replace(address, '^〒\d{3}[－-]\d{4}', '')) as address,
    nullif(phone, '') as phone,
    case
        when list_has_any(categories, ['病院', '特定機能', '地域支援', '総合病院']) then '病院'
        when list_contains(categories, '診療所') then '診療所'
        when list_contains(categories, '薬局') then '薬局'
    end as institution_type,
    categories,
    status,
    cast(designated_on as DATE) as designated_on,
    designation_reason,
    cast(designation_period_start as DATE) as designation_period_start,
    replace(annex_institution_number, '-', '') as annex_institution_number,
    full_time_doctors,
    full_time_dentists,
    full_time_pharmacists,
    part_time_doctors,
    part_time_dentists,
    part_time_pharmacists,
    beds,
    departments,
    cast(as_of as DATE) as as_of,
    bureau
from {{ ref('raw_insured_institution') }}
