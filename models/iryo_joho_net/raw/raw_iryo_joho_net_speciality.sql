{# 医療情報ネット オープンデータの診療科・診療時間票の生データ。
   main.py が病院・診療所・歯科診療所の票から 施設 × 診療科 を取り出して
   .queria/iryo_joho_net_speciality.ndjson に保存する。診療時間は取り込んでいない。 #}

{{ config(materialized='table') }}

select *
from read_json(
    '.queria/iryo_joho_net_speciality.ndjson',
    format='newline_delimited',
    columns={
        'as_of': 'VARCHAR',
        'id': 'VARCHAR',
        'speciality_code': 'VARCHAR',
        'speciality_name': 'VARCHAR'
    }
)
