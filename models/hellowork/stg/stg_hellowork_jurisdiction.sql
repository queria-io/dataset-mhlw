{{ config(materialized='ephemeral') }}

-- raw_hellowork_jurisdiction を mart から読むための stg。列は raw のまま
SELECT * FROM {{ ref('raw_hellowork_jurisdiction') }}
