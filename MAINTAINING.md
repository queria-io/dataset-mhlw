# 運用メモ

## ビルドと公開

このデータセットは日本国内から実行する必要がある。`josei.py` の取得元（女性の活躍推進
企業データベース）が日本国外からのアクセスを 403 で弾くためで、前段の AWS ロード
バランサが落とすのでヘッダーや Cookie では通らない。GitHub ホストランナーは US に
あり、この 1 ファイルだけ取得できない。そのため Sync は CI で自動実行せず、日本国内
から次のスクリプトで公開する。

```bash
QUERIA_TOKEN=... bash scripts/sync-local.sh
```

このスクリプトは、CI の Sync と同じく queria を最新に上げてからビルド・公開する。
ビルドだけを回す場合は queria 経由で実行する（dbt を直接実行しない）。

```bash
uv sync
bash scripts/build.sh
```

配信元の地域制限が解除されたら、`.github/workflows/sync.yml` の `push` / `schedule`
トリガーを戻して CI に返す。月次の Checkpoint は取得元に触れないので CI のままでよい。

パイプラインは `main.py` が担う:

1. `kaigo.py` が介護サービスの全サービス種類の事業所 CSV を取得し、英語列にそろえた NDJSON へ統合する。
2. `shougai.py` が障害福祉サービス等の全サービス種類の事業所 CSV（最新提供時点）を取得し、英語列にそろえた NDJSON へ統合する。
3. `ndb.py` が特定健診 検査値の Excel を取得し、long 形式の NDJSON へ統合する。
4. `josei.py` が女性の活躍推進企業データベースの全体版 CSV を取得し、企業属性と主要指標
   に絞った NDJSON へ整形する。
5. `jisatsu.py` が地域における自殺の基礎資料の年計 Excel（A7 表・A8 表）を取得し、
   long 形式の NDJSON へ統合する。
6. dbt が raw → stg → mart をビルドする（型変換・座標クレンジング・ジオメトリ生成）。

更新頻度は、介護サービスが年 2 回（6 月末・12 月末時点）、障害福祉サービス等が年 2 回
（3 月末・9 月末時点）、NDB オープンデータと地域における自殺の基礎資料が年次。自殺の基礎資料は新しい年の
確定値が出たら、`jisatsu.py` の `ANNUAL_ZIP_URLS` にその年の ZIP を足す。Sync は年 1 回、日本国内から手動で回す。
