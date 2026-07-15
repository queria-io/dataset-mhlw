"""厚生労働省オープンデータの取得 + dbt ビルド。

1. kaigo: 介護サービス情報公表システムから全サービス種類の事業所 CSV を取得し、
          英語列にそろえた NDJSON へ統合する。
2. ndb:   NDB オープンデータの特定健診 検査値 Excel を取得し、long 形式の NDJSON へ統合する。
3. dbt:   dbt ビルド。
"""

import logging
from pathlib import Path

from dbt.cli.main import dbtRunner

import ndb
from kaigo import download_and_flatten

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("pipelines")

FDL_DIR = Path(".fdl")
KAIGO_NDJSON_PATH = FDL_DIR / "kaigo_establishment.ndjson"
NDB_NDJSON_PATH = FDL_DIR / "ndb_health_checkup.ndjson"


def dbt_build() -> None:
    dbt = dbtRunner()
    for cmd in (["deps"], ["run"], ["docs", "generate"]):
        result = dbt.invoke(cmd)
        if not result.success:
            raise SystemExit(f"dbt {cmd[0]} failed")


def main() -> None:
    FDL_DIR.mkdir(exist_ok=True)

    logger.info("1/3: kaigo (介護サービス事業所)")
    rows = download_and_flatten(KAIGO_NDJSON_PATH)
    logger.info(f"  kaigo_establishment.ndjson: {rows} rows")

    logger.info("2/3: ndb (特定健診 検査値分布)")
    rows = ndb.download_and_flatten(NDB_NDJSON_PATH)
    logger.info(f"  ndb_health_checkup.ndjson: {rows} rows")

    logger.info("3/3: dbt build")
    dbt_build()


if __name__ == "__main__":
    main()
