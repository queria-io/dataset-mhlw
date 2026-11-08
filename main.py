"""厚生労働省オープンデータの取得 + dbt ビルド。

1. kaigo:   介護サービス情報公表システムから全サービス種類の事業所 CSV を取得し、
            英語列にそろえた NDJSON へ統合する。
2. shougai: 障害福祉サービス等情報公表システムから全サービス種類の事業所 CSV を取得し、
            英語列にそろえた NDJSON へ統合する。
3. ndb:     NDB オープンデータの特定健診 検査値 Excel を取得し、long 形式の NDJSON へ統合する。
4. josei:   女性の活躍推進企業データベースの全体版 CSV を取得し、企業属性と主要指標に
            絞った NDJSON へ整形する。
5. jisatsu: 地域における自殺の基礎資料の年計 Excel を取得し、市区町村別の自殺者数を
            long 形式の NDJSON へ統合する。
6. dpc:     DPC 退院患者調査の施設概要表と MDC 別医療機関別件数の Excel を年度ごとに取得し、
            2 本の NDJSON へ統合する。
7. dbt:     dbt ビルド。
"""

import logging
from pathlib import Path

from dbt.cli.main import dbtRunner

import dpc
import jisatsu
import josei
import kaigo
import ndb
import shougai

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("pipelines")

WORK_DIR = Path(".queria")
KAIGO_NDJSON_PATH = WORK_DIR / "kaigo_establishment.ndjson"
SHOUGAI_NDJSON_PATH = WORK_DIR / "shougai_establishment.ndjson"
NDB_NDJSON_PATH = WORK_DIR / "ndb_health_checkup.ndjson"
JOSEI_NDJSON_PATH = WORK_DIR / "josei_katsuyaku_company.ndjson"
JISATSU_NDJSON_PATH = WORK_DIR / "jisatsu_municipality.ndjson"
DPC_HOSPITAL_NDJSON_PATH = WORK_DIR / "dpc_hospital.ndjson"
DPC_MDC_NDJSON_PATH = WORK_DIR / "dpc_mdc_patients.ndjson"


def dbt_build() -> None:
    dbt = dbtRunner()
    for cmd in (["deps"], ["run"], ["docs", "generate"]):
        result = dbt.invoke(cmd)
        if not result.success:
            raise SystemExit(f"dbt {cmd[0]} failed")


def main() -> None:
    WORK_DIR.mkdir(exist_ok=True)

    logger.info("1/7: kaigo (介護サービス事業所)")
    rows = kaigo.download_and_flatten(KAIGO_NDJSON_PATH)
    logger.info(f"  kaigo_establishment.ndjson: {rows} rows")

    logger.info("2/7: shougai (障害福祉サービス等事業所)")
    rows = shougai.download_and_flatten(SHOUGAI_NDJSON_PATH)
    logger.info(f"  shougai_establishment.ndjson: {rows} rows")

    logger.info("3/7: ndb (特定健診 検査値分布)")
    rows = ndb.download_and_flatten(NDB_NDJSON_PATH)
    logger.info(f"  ndb_health_checkup.ndjson: {rows} rows")

    logger.info("4/7: josei (女性活躍推進企業)")
    rows = josei.download_and_flatten(JOSEI_NDJSON_PATH)
    logger.info(f"  josei_katsuyaku_company.ndjson: {rows} rows")

    logger.info("5/7: jisatsu (地域における自殺の基礎資料)")
    rows = jisatsu.download_and_flatten(JISATSU_NDJSON_PATH)
    logger.info(f"  jisatsu_municipality.ndjson: {rows} rows")

    logger.info("6/7: dpc (DPC 退院患者調査)")
    hospitals, mdc = dpc.download_and_flatten(DPC_HOSPITAL_NDJSON_PATH, DPC_MDC_NDJSON_PATH)
    logger.info(f"  dpc_hospital.ndjson: {hospitals} rows, dpc_mdc_patients.ndjson: {mdc} rows")

    logger.info("7/7: dbt build")
    dbt_build()


if __name__ == "__main__":
    main()
