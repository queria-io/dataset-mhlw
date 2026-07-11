# dataset-mhlw

厚生労働省が公開するオープンデータを DuckLake カタログに取り込むデータセット。

現在の収録範囲は、介護サービス情報公表システムから抽出した全国の介護サービス
事業所情報（`kaigo` スキーマ）。

## スキーマ

### kaigo — 介護サービス

介護サービス情報公表システム オープンデータ。全国の介護サービス事業所を、提供する
サービス種類ごとに 1 レコードで収録する。

- `kaigo.establishment` — 介護サービス事業所

主な列:

| 列 | 内容 |
| --- | --- |
| `establishment_number` | 介護保険事業所番号（10 桁） |
| `service_type` | サービスの種類（訪問介護・通所介護・介護老人福祉施設 など） |
| `name` / `name_kana` | 事業所名 |
| `local_gov_code` | 全国地方公共団体コード（6 桁） |
| `prefecture_code` / `city_code` | 都道府県コード（2 桁）・市区町村コード（5 桁）。`lg_code` / `address_br` と結合可 |
| `prefecture` / `city` / `address` | 所在地 |
| `latitude` / `longitude` / `geometry` | 位置（欠測・国外誤登録は NULL） |
| `corporate_number` / `corporate_name` | 法人番号（`houjin_bangou` と結合可）・法人名 |
| `capacity` | 定員 |

事業所は同一でも、提供するサービス種類が異なると別レコードになる。緯度経度は
元データに欠測（0.0）や日本国外の明らかな誤登録値が混在するため、日本の範囲内
（緯度 20〜46 / 経度 122〜154）の値のみを採用し、それ以外は NULL にしている。

## データ出典

介護サービス情報公表システム（厚生労働省）のデータを加工して作成。

- 介護サービス情報公表システム オープンデータ: https://www.mhlw.go.jp/stf/kaigo-kouhyou_opendata.html

ライセンス: 厚生労働省ホームページ利用規約に基づく公共データ利用規約（第1.0版, PDL1.0）
および クリエイティブ・コモンズ表示 4.0（CC BY 4.0）。出典表示のうえ商用利用・再配布可。

## ビルド

fdl 経由でビルドする（dbt を直接実行しない）。

```bash
uv sync
bash scripts/build.sh local
```

パイプラインは `main.py` が担う:

1. `kaigo.py` が全サービス種類の事業所 CSV を取得し、英語列にそろえた NDJSON へ統合する。
2. dbt が raw → stg → mart をビルドする（型変換・座標クレンジング・ジオメトリ生成）。

更新頻度は年 2 回（6 月末・12 月末時点）。CI の Sync は年次で実行する。
