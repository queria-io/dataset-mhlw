#!/usr/bin/env bash
# 日本国内から回す Sync。CI の Sync ワークフローの代わり。
#
# josei.py の取得元（女性の活躍推進企業データベース）は日本国外からのアクセスを
# 403 で弾くため、GitHub ホストランナー（US）ではビルドが通らない。このリポだけ
# CI で Sync せず、日本国内の環境からこのスクリプトで公開する。
#
# 公開には `queria login` 済みであること（fdl がそこからトークンを取る）。
# ログインしていない環境では FDL_TOKEN に書き込めるトークンを渡す。
#
# uv.lock は fdl と queria を最新に上げてから同期する。差分が出たらコミットする。
set -euo pipefail

cd "$(dirname "$0")/.."

# scripts/build.sh は submodule の shared/ を呼ぶ。clone 直後は空なので取得する
git submodule update --init

uv lock --upgrade-package fdl-cli --upgrade-package queria
uv sync
bash scripts/build.sh

echo "published. uv.lock に差分があればコミットすること"
