{# 厚生労働省「都道府県労働局所在地一覧」の公共職業安定所の管轄一覧表の生データ。
   main.py が 47 都道府県の管轄一覧表を読み、1 安定所 1 行にして .queria/hellowork_jurisdiction.ndjson に保存する。
   jurisdiction_items は管轄区域を括弧の外の読点で区切ったもの。 #}

{{ config(materialized='table') }}

select *
from read_json(
    '.queria/hellowork_jurisdiction.ndjson',
    format='newline_delimited',
    columns={
        'prefecture_code': 'VARCHAR',
        'prefecture_name': 'VARCHAR',
        'name': 'VARCHAR',
        'office_name': 'VARCHAR',
        'office_kind': 'VARCHAR',
        'jurisdiction': 'VARCHAR',
        'jurisdiction_items': 'VARCHAR[]',
        'source_url': 'VARCHAR'
    }
)
