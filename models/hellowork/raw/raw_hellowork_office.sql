{# 厚生労働省「都道府県労働局所在地一覧」の公共職業安定所の表の生データ。
   main.py が 47 都道府県のページを読み、1 施設 1 行にして .queria/hellowork_office.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    '.queria/hellowork_office.ndjson',
    format='newline_delimited',
    columns={
        'prefecture_code': 'VARCHAR',
        'prefecture_name': 'VARCHAR',
        'office_name': 'VARCHAR',
        'office_kind': 'VARCHAR',
        'name': 'VARCHAR',
        'postal_code': 'VARCHAR',
        'address': 'VARCHAR',
        'phone': 'VARCHAR',
        'fax': 'VARCHAR',
        'phone_text': 'VARCHAR',
        'guide_url': 'VARCHAR',
        'source_url': 'VARCHAR'
    }
)
