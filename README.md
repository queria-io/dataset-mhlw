# dataset-mhlw

厚生労働省が公開するオープンデータを DuckLake カタログに取り込むデータセット。

現在の収録範囲は、介護サービス情報公表システムから抽出した全国の介護サービス
事業所情報（`kaigo` スキーマ）と、障害福祉サービス等情報公表システムから抽出した
全国の障害福祉サービス等事業所情報（`shougai` スキーマ）。

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

### shougai — 障害福祉サービス

障害福祉サービス等情報公表システム オープンデータ。障害者総合支援法・児童福祉法に
基づく障害福祉サービス等事業所（訪問系・日中活動系・施設系・訓練系・就労系・相談支援・
障害児支援）を、提供するサービス種類ごとに 1 レコードで収録する。

- `shougai.establishment` — 障害福祉サービス等事業所

主な列:

| 列 | 内容 |
| --- | --- |
| `establishment_number` | 障害福祉サービス等事業所番号 |
| `service_type` | サービス種別（居宅介護・生活介護・就労継続支援B型・放課後等デイサービス など） |
| `name` / `name_kana` | 事業所名 |
| `local_gov_code` | 全国地方公共団体コード（5 桁） |
| `prefecture_code` / `city_code` | 都道府県コード（2 桁）・市区町村コード（5 桁）。`lg_code` / `address_br` と結合可 |
| `designating_authority` | 指定機関名（指定した自治体） |
| `address_city` / `address_detail` | 所在地 |
| `latitude` / `longitude` / `geometry` | 位置（欠測・国外誤登録は NULL） |
| `corporate_number` / `corporate_name` | 法人番号（`houjin_bangou` と結合可）・法人名 |
| `capacity` | 定員（定員概念のないサービスは NULL） |
| `hours_weekday` / `hours_saturday` / `hours_sunday` / `hours_holiday` | 利用可能な時間帯 |

事業所は同一でも、提供するサービス種類が異なると別レコードになる。緯度経度の
クレンジングは `kaigo` と同様（日本の範囲内のみ採用）。`corporate_number` は原典が
提供する値をそのまま保持しており、基本は 13 桁だが、一部に桁数の異なる値も含まれる。

## データ出典

いずれも厚生労働省が公開するデータを加工して作成。

- 介護サービス情報公表システム オープンデータ: https://www.mhlw.go.jp/stf/kaigo-kouhyou_opendata.html
- 障害福祉サービス等情報公表システム オープンデータ（WAM NET 配信）: https://www.wam.go.jp/content/wamnet/pcpub/top/sfkopendata/

ライセンス: 厚生労働省ホームページ利用規約に基づく公共データ利用規約（第1.0版, PDL1.0）
および クリエイティブ・コモンズ表示 4.0（CC BY 4.0）。障害福祉サービス等情報公表システムの
オープンデータは、官民データ活用推進基本法に基づき営利・非営利を問わず二次利用可能。
いずれも出典表示のうえ商用利用・再配布可。

## ビルド

fdl 経由でビルドする（dbt を直接実行しない）。

```bash
uv sync
bash scripts/build.sh local
```

パイプラインは `main.py` が担う:

1. `kaigo.py` が介護サービスの全サービス種類の事業所 CSV を取得し、英語列にそろえた NDJSON へ統合する。
2. `shougai.py` が障害福祉サービス等の全サービス種類の事業所 CSV（最新提供時点）を取得し、英語列にそろえた NDJSON へ統合する。
3. dbt が raw → stg → mart をビルドする（型変換・座標クレンジング・ジオメトリ生成）。

更新頻度は、介護サービスが年 2 回（6 月末・12 月末時点）、障害福祉サービス等が年 2 回
（3 月末・9 月末時点）。CI の Sync は年次で実行する。
