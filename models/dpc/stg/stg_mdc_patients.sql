{# 型変換と MDC の名称の付与。MDC の名称は診断群分類の主要診断群（MDC）18 区分。 #}

select
    try_cast(m.fiscal_year as INTEGER) as fiscal_year,
    m.notification_number,
    nullif(m.serial_number, '-') as serial_number,
    m.mdc,
    n.mdc_name,
    m.surgery = '有り' as has_surgery,
    try_cast(m.patients as BIGINT) as patients
from {{ ref('raw_mdc_patients') }} as m
left join (
    values
        ('01', '神経系疾患'),
        ('02', '眼科系疾患'),
        ('03', '耳鼻咽喉科系疾患'),
        ('04', '呼吸器系疾患'),
        ('05', '循環器系疾患'),
        ('06', '消化器系疾患、肝臓・胆道・膵臓疾患'),
        ('07', '筋骨格系疾患'),
        ('08', '皮膚・皮下組織の疾患'),
        ('09', '乳房の疾患'),
        ('10', '内分泌・栄養・代謝に関する疾患'),
        ('11', '腎・尿路系疾患及び男性生殖器系疾患'),
        ('12', '女性生殖器系疾患及び産褥期疾患・異常妊娠分娩'),
        ('13', '血液・造血器・免疫臓器の疾患'),
        ('14', '新生児疾患、先天性奇形'),
        ('15', '小児疾患'),
        ('16', '外傷・熱傷・中毒'),
        ('17', '精神疾患'),
        ('18', 'その他')
) as n (mdc, mdc_name) using (mdc)
