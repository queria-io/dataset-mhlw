"""厚生労働省オープンデータの取得 + dbt ビルド。

1. kaigo:   介護サービス情報公表システムから全サービス種類の事業所 CSV を取得し、
            英語列にそろえた NDJSON へ統合する。
2. shougai: 障害福祉サービス等情報公表システムから全サービス種類の事業所 CSV を取得し、
            英語列にそろえた NDJSON へ統合する。
3. ndb:     NDB オープンデータの特定健診 検査値 Excel を取得し、long 形式の NDJSON へ統合する。
4. jisatsu: 地域における自殺の基礎資料の年計と月次の Excel を取得し、市区町村別の自殺者数を
            long 形式の NDJSON へ統合する。
5. dpc:     DPC 退院患者調査の施設概要表と MDC 別医療機関別件数の Excel を年度ごとに取得し、
            2 本の NDJSON へ統合する。
6. kouseikyoku:   地方厚生局のコード内容別医療機関一覧表（8 局）を取得し、1 機関 1 行の NDJSON へ整形する。
7. iryo_joho_net: 医療情報ネットの施設票と診療科・診療時間票を取得し、2 本の NDJSON へ整形する。
8. hellowork: 都道府県労働局所在地一覧から公共職業安定所の所在地と管轄区域を取得し、2 本の NDJSON へ整形する。
9. dbt:    dbt ビルド。
"""

import logging
from pathlib import Path

from dbt.cli.main import dbtRunner

import dpc
import hellowork
import iryo_joho_net
import jisatsu
import kaigo
import kouseikyoku
import ndb
import plans
import shougai

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("pipelines")

WORK_DIR = Path(".queria")
KAIGO_NDJSON_PATH = WORK_DIR / "kaigo_establishment.ndjson"
SHOUGAI_NDJSON_PATH = WORK_DIR / "shougai_establishment.ndjson"
NDB_NDJSON_PATH = WORK_DIR / "ndb_health_checkup.ndjson"
JISATSU_NDJSON_PATH = WORK_DIR / "jisatsu_municipality.ndjson"
JISATSU_MONTHLY_NDJSON_PATH = WORK_DIR / "jisatsu_municipality_monthly.ndjson"
DPC_HOSPITAL_NDJSON_PATH = WORK_DIR / "dpc_hospital.ndjson"
DPC_MDC_NDJSON_PATH = WORK_DIR / "dpc_mdc_patients.ndjson"
KOUSEIKYOKU_NDJSON_PATH = WORK_DIR / "kouseikyoku_insured_institution.ndjson"
IRYO_JOHO_NET_FACILITY_NDJSON_PATH = WORK_DIR / "iryo_joho_net_facility.ndjson"
IRYO_JOHO_NET_SPECIALITY_NDJSON_PATH = WORK_DIR / "iryo_joho_net_speciality.ndjson"
HELLOWORK_OFFICE_NDJSON_PATH = WORK_DIR / "hellowork_office.ndjson"
HELLOWORK_JURISDICTION_NDJSON_PATH = WORK_DIR / "hellowork_jurisdiction.ndjson"


def dbt_build() -> None:
    dbt = dbtRunner()
    for cmd in (["deps"], ["run"], ["docs", "generate"]):
        result = dbt.invoke(cmd)
        if not result.success:
            raise SystemExit(f"dbt {cmd[0]} failed")


def main() -> None:
    WORK_DIR.mkdir(exist_ok=True)

    logger.info("1/10: kaigo (介護サービス事業所)")
    rows = kaigo.download_and_flatten(KAIGO_NDJSON_PATH)
    logger.info(f"  kaigo_establishment.ndjson: {rows} rows")

    logger.info("2/10: shougai (障害福祉サービス等事業所)")
    rows = shougai.download_and_flatten(SHOUGAI_NDJSON_PATH)
    logger.info(f"  shougai_establishment.ndjson: {rows} rows")

    logger.info("3/10: ndb (特定健診 検査値分布)")
    rows = ndb.download_and_flatten(NDB_NDJSON_PATH)
    logger.info(f"  ndb_health_checkup.ndjson: {rows} rows")

    logger.info("4/10: jisatsu (地域における自殺の基礎資料)")
    rows = jisatsu.download_and_flatten(JISATSU_NDJSON_PATH)
    logger.info(f"  jisatsu_municipality.ndjson: {rows} rows")
    rows = jisatsu.download_and_flatten_monthly(JISATSU_MONTHLY_NDJSON_PATH)
    logger.info(f"  jisatsu_municipality_monthly.ndjson: {rows} rows")

    logger.info("5/10: dpc (DPC 退院患者調査)")
    hospitals, mdc = dpc.download_and_flatten(DPC_HOSPITAL_NDJSON_PATH, DPC_MDC_NDJSON_PATH)
    logger.info(f"  dpc_hospital.ndjson: {hospitals} rows, dpc_mdc_patients.ndjson: {mdc} rows")

    logger.info("6/10: kouseikyoku (コード内容別医療機関一覧表)")
    rows = kouseikyoku.download_and_flatten(KOUSEIKYOKU_NDJSON_PATH)
    logger.info(f"  kouseikyoku_insured_institution.ndjson: {rows} rows")

    logger.info("7/10: iryo_joho_net (医療情報ネット)")
    facilities, specialities = iryo_joho_net.download_and_flatten(
        IRYO_JOHO_NET_FACILITY_NDJSON_PATH, IRYO_JOHO_NET_SPECIALITY_NDJSON_PATH
    )
    logger.info(f"  iryo_joho_net_facility.ndjson: {facilities} rows, iryo_joho_net_speciality.ndjson: {specialities} rows")

    logger.info("8/10: hellowork (公共職業安定所の所在地と管轄区域)")
    offices, areas = hellowork.download_and_flatten(HELLOWORK_OFFICE_NDJSON_PATH, HELLOWORK_JURISDICTION_NDJSON_PATH)
    logger.info(f"  hellowork_office.ndjson: {offices} rows, hellowork_jurisdiction.ndjson: {areas} rows")

    logger.info("9/10: plans (行政事業レビューが挙げる計画・通知等)")
    plans.download_plans()
    plans.build_plans_parquet()

    logger.info("10/10: dbt build")
    dbt_build()


if __name__ == "__main__":
    main()
