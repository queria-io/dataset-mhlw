"""厚生労働省オープンデータの取得 + dbt ビルド。

1. kaigo: 介護サービス情報公表システムから全サービス種類の事業所 CSV を取得し、
          英語列にそろえた NDJSON へ統合する。
2. dbt:   dbt ビルド。
"""

import logging
from pathlib import Path

from dbt.cli.main import dbtRunner

from kaigo import download_and_flatten

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("pipelines")

FDL_DIR = Path(".fdl")
NDJSON_PATH = FDL_DIR / "kaigo_establishment.ndjson"


def dbt_build() -> None:
    dbt = dbtRunner()
    for cmd in (["deps"], ["run"], ["docs", "generate"]):
        result = dbt.invoke(cmd)
        if not result.success:
            raise SystemExit(f"dbt {cmd[0]} failed")


def main() -> None:
    FDL_DIR.mkdir(exist_ok=True)

    logger.info("1/2: kaigo (介護サービス事業所)")
    rows = download_and_flatten(NDJSON_PATH)
    logger.info(f"  kaigo_establishment.ndjson: {rows} rows")

    logger.info("2/2: dbt build")
    dbt_build()


if __name__ == "__main__":
    main()
