{# 地域における自殺の基礎資料 市区町村別・月次の生データ。
   main.py が月次 ZIP の A7・A8 表を long 形式に展開して .queria/jisatsu_municipality_monthly.ndjson に保存する。
   型変換は stg 以降で行うため全列 VARCHAR で読む。 #}

{{ config(materialized='table') }}

select *
from read_json(
    '.queria/jisatsu_municipality_monthly.ndjson',
    format='newline_delimited',
    columns={
        'year': 'VARCHAR',
        'month': 'VARCHAR',
        'status': 'VARCHAR',
        'location_basis': 'VARCHAR',
        'prefecture_code': 'VARCHAR',
        'local_gov_code': 'VARCHAR',
        'municipality': 'VARCHAR',
        'area_level': 'VARCHAR',
        'sex': 'VARCHAR',
        'attribute': 'VARCHAR',
        'category': 'VARCHAR',
        'parent_category': 'VARCHAR',
        'count': 'VARCHAR'
    }
)
