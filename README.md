# dataset-mhlw

厚生労働省が公開するオープンデータを DuckLake カタログに取り込むデータセット。

現在の収録範囲は、介護サービス情報公表システムから抽出した全国の介護サービス
事業所情報（`kaigo` スキーマ）、障害福祉サービス等情報公表システムから抽出した
全国の障害福祉サービス等事業所情報（`shougai` スキーマ）、および NDB オープンデータの
特定健診 検査値の都道府県別・性年齢階級別分布（`ndb` スキーマ）。

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

### ndb — 特定健診（NDB）

NDB（ナショナルデータベース）オープンデータの特定健診（特定健康診査）検査値。
検査項目ごとの検査値分布を、検査項目 × 都道府県 × 検査値階層 × 性 × 年齢階級 の
long 形式で収録する。値は各区分に該当する受診者数（人数）。

- `ndb.health_checkup` — 特定健診 検査値分布

主な列:

| 列 | 内容 |
| --- | --- |
| `fiscal_year` | 集計対象年度（西暦） |
| `test_item` | 検査項目（BMI・HbA1C・収縮期血圧・眼底検査（SCOTT分類） など 25 項目） |
| `unit` | 検査値階層の単位・注記（kg/㎡・mmHg・％※NGSP値 など）。分類項目は NULL |
| `prefecture_code` | 都道府県コード（2 桁）。`lg_code` / `census` / `address_br` と結合可 |
| `prefecture` | 都道府県名。判別不可は「都道府県判別不可」（コードは NULL） |
| `sex` | 性（男／女） |
| `age_class` | 年齢階級（40〜74 歳を 5 歳刻み） |
| `value_class` | 検査値階層（数値範囲・眼底検査の分類・尿検査の判定・心電図の所見 など項目により異なる） |
| `count` | 当該区分に該当する受診者数。集計結果 10 未満の秘匿セルは NULL |

検査項目は BMI・腹囲・血圧（収縮期／拡張期）・血糖（HbA1C／空腹時／随時）・
脂質（HDL／LDL／中性脂肪）・肝機能（GOT／GPT／γ-GT）・腎機能（血清クレアチニン／
eGFR）・尿検査（尿糖／尿蛋白）・ヘモグロビン・心電図・眼底検査（各分類）の 25 項目。
数値区分のほか、眼底検査の分類・尿検査の判定・心電図の所見など、項目により検査値階層の
表現が異なるため、`value_class` は文字列で保持している。年齢階級は特定健診の対象年齢
（40〜74 歳）で、性ごとの小計「中計」は収録しない。集計結果が 10 未満のセルは元データで
秘匿されており、`count` は NULL になる。

## データ出典

いずれも厚生労働省が公開するデータを加工して作成。

- 介護サービス情報公表システム オープンデータ: https://www.mhlw.go.jp/stf/kaigo-kouhyou_opendata.html
- 障害福祉サービス等情報公表システム オープンデータ（WAM NET 配信）: https://www.wam.go.jp/content/wamnet/pcpub/top/sfkopendata/
- NDB オープンデータ: https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000177182.html

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
3. `ndb.py` が特定健診 検査値の Excel を取得し、long 形式の NDJSON へ統合する。
4. dbt が raw → stg → mart をビルドする（型変換・座標クレンジング・ジオメトリ生成）。

更新頻度は、介護サービスが年 2 回（6 月末・12 月末時点）、障害福祉サービス等が年 2 回
（3 月末・9 月末時点）、NDB オープンデータが年次。CI の Sync は年次で実行する。
