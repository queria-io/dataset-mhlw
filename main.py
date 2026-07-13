"""厚生労働省オープンデータの取得 + dbt ビルド。

1. kaigo: 介護サービス情報公表システムから全サービス種類の事業所 CSV を取得し、
          英語列にそろえた NDJSON へ統合する。
2. josei: 女性の活躍推進企業データベースの全体版 CSV を取得し、企業属性と主要指標に
          絞った NDJSON へ整形する。
3. dbt:   dbt ビルド。
"""

import logging
from pathlib import Path

from dbt.cli.main import dbtRunner

import josei
import kaigo

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("pipelines")

FDL_DIR = Path(".fdl")
KAIGO_NDJSON_PATH = FDL_DIR / "kaigo_establishment.ndjson"
JOSEI_NDJSON_PATH = FDL_DIR / "josei_katsuyaku_company.ndjson"


def dbt_build() -> None:
    dbt = dbtRunner()
    for cmd in (["deps"], ["run"], ["docs", "generate"]):
        result = dbt.invoke(cmd)
        if not result.success:
            raise SystemExit(f"dbt {cmd[0]} failed")


def main() -> None:
    FDL_DIR.mkdir(exist_ok=True)

    logger.info("1/3: kaigo (介護サービス事業所)")
    rows = kaigo.download_and_flatten(KAIGO_NDJSON_PATH)
    logger.info(f"  kaigo_establishment.ndjson: {rows} rows")

    logger.info("2/3: josei (女性活躍推進企業)")
    rows = josei.download_and_flatten(JOSEI_NDJSON_PATH)
    logger.info(f"  josei_katsuyaku_company.ndjson: {rows} rows")

    logger.info("3/3: dbt build")
    dbt_build()


if __name__ == "__main__":
    main()
