{# NDB オープンデータ 特定健診 検査値の生データ。
   main.py が全検査項目の Excel を long 形式に展開して .fdl/ndb_health_checkup.ndjson に保存する。
   型変換は stg 以降で行うため全列 VARCHAR で読む。 #}

{{ config(materialized='table') }}

select *
from read_json(
    '.fdl/ndb_health_checkup.ndjson',
    format='newline_delimited',
    columns={
        'fiscal_year': 'VARCHAR',
        'test_item': 'VARCHAR',
        'unit': 'VARCHAR',
        'prefecture': 'VARCHAR',
        'prefecture_code': 'VARCHAR',
        'value_class': 'VARCHAR',
        'sex': 'VARCHAR',
        'age_class': 'VARCHAR',
        'count': 'VARCHAR'
    }
)
