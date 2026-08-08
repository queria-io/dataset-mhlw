#!/usr/bin/env bash
# 日本国内から回す Sync。CI の Sync ワークフローの代わり。
#
# josei.py の取得元（女性の活躍推進企業データベース）は日本国外からのアクセスを
# 403 で弾くため、GitHub ホストランナー（US）ではビルドが通らない。このリポだけ
# CI で Sync せず、日本国内の環境からこのスクリプトで公開する。
#
# 必要なもの:
#   QUERIA_TOKEN  公開先アカウントのトークン
#
# uv.lock は CI と同じく queria を最新に上げてから同期する。差分が出たらコミットする。
set -euo pipefail

cd "$(dirname "$0")/.."

: "${QUERIA_TOKEN:?QUERIA_TOKEN が設定されていない}"

uv lock --upgrade-package queria
uv sync
bash scripts/build.sh

echo "published. uv.lock に差分があればコミットすること"
