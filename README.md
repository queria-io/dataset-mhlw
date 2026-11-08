# 厚生労働省

厚生労働省が公開するオープンデータのうち、全国の介護・障害福祉サービス事業所、特定健診の検査値の分布（NDB）、企業が公表した女性活躍の指標、市区町村別の自殺者数、DPC 調査に参加した病院の MDC 別の退院患者数を、SQL で検索・集計できるテーブルにしたデータセットです。事業所は市区町村コードで lg_code・address_br と、企業は法人番号で houjin_bangou・gbizinfo と結合できます。

## 出典と利用条件

| 原典 | スキーマ |
| --- | --- |
| [介護サービス情報公表システム オープンデータ](https://www.mhlw.go.jp/stf/kaigo-kouhyou_opendata.html) | `kaigo` |
| [障害福祉サービス等情報公表システム オープンデータ（WAM NET 配信）](https://www.wam.go.jp/content/wamnet/pcpub/top/sfkopendata/) | `shougai` |
| [NDB オープンデータ](https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000177182.html) | `ndb` |
| [女性の活躍推進企業データベース オープンデータ](https://positive-ryouritsu.mhlw.go.jp/positivedb/opendata/) | `josei_katsuyaku` |
| [地域における自殺の基礎資料](https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000140901.html) | `jisatsu` |
| [DPC 導入の影響評価に係る調査「退院患者調査」の結果報告](https://www.mhlw.go.jp/stf/shingi2/newpage_00137.html) | `dpc` |

- いずれも厚生労働省が公開するデータを加工して作成したものです
- 厚生労働省ホームページ利用規約に基づく公共データ利用規約（第1.0版、PDL1.0）およびクリエイティブ・コモンズ表示 4.0（CC BY 4.0）に従います
- 障害福祉サービス等情報公表システムのオープンデータは、官民データ活用推進基本法に基づき営利・非営利を問わず二次利用できます
- 女性の活躍推進企業データベースは、政府標準利用規約第2.0版に準拠したオープンデータ利用規約（CC BY 4.0 互換）で提供されています
- いずれも出典を表示すれば商用利用・再配布ができます

## テーブル

| テーブル | 内容 |
| --- | --- |
| `kaigo.establishment` | 全国の介護サービス事業所。1 行が事業所 × サービス種類 |
| `shougai.establishment` | 全国の障害福祉サービス等事業所。1 行が事業所 × サービス種類 |
| `ndb.health_checkup` | 特定健診の検査値の分布。検査項目 × 都道府県 × 検査値階層 × 性 × 年齢階級ごとの受診者数 |
| `josei_katsuyaku.company` | 企業が公表した女性活躍・両立支援の指標。1 行が 1 企業 |
| `jisatsu.suicide_municipality` | 市区町村別・年別の自殺者数。年 × 集計地 × 市区町村 × 性 × 属性区分 × 区分 |
| `dpc.hospital` | DPC 退院患者調査に参加した病院の施設概要。1 行が年度 × 病院 |
| `dpc.mdc_patients` | 病院別の退院患者数。年度 × 病院 × MDC（主要診断群）× 手術の有無 |

## 使い方

日野市の訪問介護の事業所を数える（同じ事業所が複数のサービスで行を持つので、事業所番号の重複を除きます）:

```sql
SELECT count(DISTINCT establishment_number) AS establishments
FROM mhlw.kaigo.establishment
WHERE city_code = '13212' AND service_type = '訪問介護';
```

都道府県ごとに、女性管理職割合を公表している企業の数と平均を出す:

```sql
SELECT prefecture, count(*) AS companies, round(avg(women_in_management_pct), 1) AS avg_pct
FROM mhlw.josei_katsuyaku.company
WHERE women_in_management_pct IS NOT NULL
GROUP BY ALL
ORDER BY companies DESC;
```

東京都の 2024 年の自殺者数（住居地）を出す（区の行を除いて足します）:

```sql
SELECT sum(count) AS suicides
FROM mhlw.jisatsu.suicide_municipality
WHERE year = 2024 AND location_basis = '住居地' AND sex = '総数'
  AND attribute = '総数' AND prefecture_code = '13' AND area_level <> '区';
```

2023 年度に循環器系疾患（MDC 05）で手術を受けて退院した患者の数を、都道府県ごとに出す:

```sql
SELECT h.prefecture_code, sum(m.patients) AS patients
FROM mhlw.dpc.mdc_patients AS m
JOIN mhlw.dpc.hospital AS h
  ON m.fiscal_year = h.fiscal_year
 AND m.notification_number = h.notification_number
 AND m.serial_number IS NOT DISTINCT FROM h.serial_number
WHERE m.fiscal_year = 2023 AND m.mdc = '05' AND m.has_surgery
GROUP BY ALL
ORDER BY patients DESC;
```

## 介護サービス（kaigo）

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

- 事業所が同じでも、提供するサービス種類が異なると別の行になります
- 緯度経度は、元データに欠測（0.0）や日本国外の明らかな誤登録が混ざるため、日本の範囲内（緯度 20〜46、経度 122〜154）の値だけを採用し、それ以外は NULL にしています。地図に出すときは NULL を除いてください

## 障害福祉サービス（shougai）

障害者総合支援法・児童福祉法に基づく障害福祉サービス等事業所（訪問系・日中活動系・施設系・訓練系・就労系・相談支援・障害児支援）を収録しています。

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

- 事業所が同じでも、提供するサービス種類が異なると別の行になります。緯度経度の扱いは kaigo と同じです
- `corporate_number` は原典の値をそのまま持っています。基本は 13 桁ですが、桁数の異なる値も一部に含まれます

## 特定健診（ndb）

NDB（ナショナルデータベース）オープンデータの特定健診の検査値です。値は各区分に該当する受診者数で、個人単位のデータではありません。

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

- 検査項目は BMI・腹囲・血圧（収縮期／拡張期）・血糖（HbA1C／空腹時／随時）・脂質（HDL／LDL／中性脂肪）・肝機能（GOT／GPT／γ-GT）・腎機能（血清クレアチニン／eGFR）・尿検査（尿糖／尿蛋白）・ヘモグロビン・心電図・眼底検査（各分類）の 25 項目です
- 検査値階層の表現は項目により異なるため、`value_class` は文字列で持っています
- 年齢階級は特定健診の対象年齢（40〜74 歳）です。性ごとの小計「中計」は収録していません
- 集計結果が 10 未満のセルは元データで秘匿されていて、`count` は NULL です

## 女性活躍推進企業（josei_katsuyaku）

女性活躍推進法・次世代育成支援対策推進法に基づく情報公表制度で、企業が任意に公表した指標です。

| 列 | 内容 |
| --- | --- |
| `corporate_number` | 法人番号（13 桁）。`houjin_bangou` / `gbizinfo` と結合可 |
| `company_name` | 企業名 |
| `industry` / `industry_detail` | 業種・業種（詳細分類） |
| `prefecture` / `company_size` | 都道府県・企業規模 |
| `market_segment` / `securities_code` | 上場企業の市場区分・証券コード（非上場は NULL） |
| `eruboshi_stage` / `kurumin` | えるぼし認定の段階・くるみん認定の状況 |
| `women_in_kakaricho_pct` / `women_in_management_pct` / `women_on_board_pct` | 係長級・管理職・役員に占める女性割合(%) |
| `gender_wage_gap_all_pct` / `gender_wage_gap_regular_pct` / `gender_wage_gap_nonregular_pct` | 男女の賃金の差異（全労働者・正規・非正規, %） |
| `childcare_leave_male_pct` / `childcare_leave_female_pct` | 育児休業取得率（男性・女性, %） |
| `avg_monthly_overtime_hours` / `paid_leave_rate_pct` | 一月当たりの平均残業時間・年次有給休暇取得率(%) |
| `last_updated` | 企業がデータを最終更新した日 |

- 任意公表のため、公表していない企業の指標は NULL です。NULL は 0 ではありません
- 育児休業取得率は雇用管理区分ごとに公表されるため、先頭の区分（`childcare_leave_category`）の値だけを収録しています
- 元データは 236 列の横持ちです。このテーブルは企業単位で 1 つの値になる主要指標に絞っています

## 自殺統計（jisatsu）

警察庁の自殺統計を厚生労働省が市区町村別に再集計した資料の確定値のうち、年計の自殺日集計（A7 表・A8 表）を収録しています。2022 年から 2025 年です。

| 列 | 内容 |
| --- | --- |
| `year` | 年（西暦・暦年）。自殺日で集計 |
| `location_basis` | 集計地。住居地（自殺者の住居があった市区町村）／発見地（自殺死体が発見された市区町村） |
| `prefecture_code` | 都道府県コード（2 桁） |
| `local_gov_code` / `city_code` | 全国地方公共団体コード（6 桁）・市区町村コード（5 桁）。`lg_code` / `address_br` と結合可 |
| `municipality` | 都道府県名を付けた市区町村名。政令指定都市の区は「札幌市中央区」、東京都の特別区は「東京都千代田区」の形 |
| `area_level` | 行の種別（市区町村／区／区不詳／市区町村不詳／都道府県不詳） |
| `sex` | 性（総数／男／女） |
| `attribute` / `category` | 属性区分（年齢階級、同居人の有無、職業、場所、手段、時間帯、曜日、原因・動機、自殺未遂歴）と、その中の区分 |
| `parent_category` | 内数の区分が属する上位の区分（職業のみ） |
| `count` | 自殺者数。秘匿された欄は NULL |

- 政令指定都市と東京都特別区は、市の行（`area_level` = 市区町村）と各区の行（区）の両方を持ちます。市の行は各区の和で、区が分からない人数（区不詳）を含みません。市の総数を出すときは、同じ市の区不詳の行を足してください
- 全国や都道府県の合計は、`area_level` = 区 の行を除いて足してください。こうして足した総数は、元資料の全国表の総数と各年で一致します
- 自殺者が 0 人の市区町村は行がありません
- 個人が識別されないよう秘匿処理があります。自殺者総数が 1 か 2 の自治体では職業・場所・手段・原因・動機・自殺未遂歴が公表されず、それ以外でも他の欄から 1 か 2 が逆算できる欄は公表されません。秘匿された欄の `count` は NULL で、0 ではありません
- 原因・動機は 1 人につき 4 つまで計上するため、区分の和は総数と一致しません
- 自殺死亡率は収録していません。率が必要なときは人口のテーブルと `city_code` で結合してください
- 2022 年 1 月に自殺統計原票が見直され、職業と原因・動機の区分が変わったため、それより前の年は収録していません

## DPC 退院患者調査（dpc）

中医協 DPC 評価分科会の「DPC 導入の影響評価に係る調査『退院患者調査』」の結果報告から、施設概要表と参考資料「MDC 別医療機関別件数」を収録しています。平成 28 年度（2016 年度）から令和 5 年度（2023 年度）です。DPC 対象病院のほか、DPC 準備病院と、データを提出している出来高算定病院を含みます。

`dpc.hospital`:

| 列 | 内容 |
| --- | --- |
| `fiscal_year` | 年度（西暦）。4 月から翌年 3 月までに退院した患者を集計 |
| `notification_number` | 当該年度の告示番号（5 桁） |
| `serial_number` | 前年度の告示番号。当該年度から参加した病院と、合併後の病院は NULL |
| `hospital_name` | 施設名 |
| `facility_group` | 施設類型（大学病院本院群／DPC特定病院群／DPC標準病院群／DPC準備病院／出来高算定病院。2017 年度までは DPC対象病院Ⅰ群・Ⅱ群・Ⅲ群） |
| `hospital_category` | DPC に参加した年度と参加の種別（例 平成15年度DPC参加病院） |
| `prefecture_code` / `city_code` / `local_gov_code` | 所在地の都道府県コード・市区町村コード（5 桁）・全国地方公共団体コード（6 桁）。`lg_code` / `address_br` と結合可 |
| `dpc_beds` / `dpc_basic_fee` / `dpc_bed_ratio` | DPC 算定病床数・その入院基本料・病床総数に占める割合 |
| `rehabilitation_beds` / `community_care_beds` / `psychiatric_beds` / `long_term_care_beds` / `tuberculosis_beds` / `total_beds` | 回復期リハビリテーション病棟入院料等・地域包括ケア病棟入院料・精神・療養・結核の病床数と病床総数 |
| `months_submitted` | 当該年度にデータを提出した月の数 |

`dpc.mdc_patients`:

| 列 | 内容 |
| --- | --- |
| `fiscal_year` / `notification_number` / `serial_number` | 年度と病院。`dpc.hospital` と結合するキー |
| `mdc` / `mdc_name` | 主要診断群（MDC）の 2 桁のコード（01〜18）と名称 |
| `has_surgery` | 手術があった症例なら true。輸血関連の手技だけの症例は手術なし |
| `patients` | 退院または転棟した患者の数 |

- 施設類型は告示番号の先頭の桁で決まります（1 大学病院本院群、2 DPC 特定病院群、3 DPC 標準病院群、9 DPC 準備病院、0 出来高算定病院）。各年度の施設類型ごとの病院数は、元資料の集計条件に載る集計対象施設数と一致します
- DPC 準備病院と出来高算定病院の告示番号は、調査参加年度ごとの施設コード順で年度ごとに振り直されます。年度をまたいで同じ病院を追うときは `serial_number`（前年度の告示番号）でつないでください
- 年度の途中で合併した病院は、合併前と合併後の 2 行を持ち、告示番号が同じになることがあります。1 年度の中では `notification_number` と `serial_number` の組で一意です。`serial_number` は NULL を含むので、結合では `IS NOT DISTINCT FROM` で比べてください
- 症例数が 10 未満の組み合わせと 0 件の組み合わせは公表されていないため、`dpc.mdc_patients` に行がありません
- 在院日数 1 日以下、24 時間以内の死亡、移植手術ありなど、元資料の集計条件に定める症例は分析対象から除かれています

## 更新

年 1 回、元データの更新に合わせて取り込みます。女性の活躍推進企業データベースが日本国外からのアクセスを受け付けないため、日本国内の環境でビルドしています。

```bash
git submodule update --init
uv sync
bash scripts/build.sh
```
