#!/usr/bin/env bash

set -euo pipefail

# 修改此数组即可自定义 group ratio 列表。
GROUP_RATIOS=(
  "1"
)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
FEE_RATE="${FEE_RATE:-0.0008}"

COMMON_ARGS=(
  "--trading-pair" "BTC-USDT"
  "--capital" "3500"
  "--min-price" "97049.500136"
  "--max-price" "102000.000000"
  "--grids" "5"
  "--groups" "1"
  "--fee-rate" "${FEE_RATE}"
)

for ratio in "${GROUP_RATIOS[@]}"; do
  echo "运行 grid_calculator.py，group ratio 为 ${ratio}"
  "${PYTHON_BIN}" "${SCRIPT_DIR}/grid_calculator.py" "${COMMON_ARGS[@]}" "--group-ratio" "${ratio}"
done
