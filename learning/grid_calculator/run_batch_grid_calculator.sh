#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
FEE_RATE="${FEE_RATE:-0.0008}"

# 如需新增配置，可复制下方数组并按需修改参数。
CONFIG_SET_1=(
  "--trading-pair" "BTC-USDT"
  "--capital" "50000"
  "--min-price" "99662.971305"
  "--max-price" "200000"
  "--grids" "70"
  "--groups" "14"
  "--fee-rate" "${FEE_RATE}"
  "--group-ratio" "1"
)

CONFIG_SET_2=(
  "--trading-pair" "BTC-USDT"
  "--capital" "50000"
  "--min-price" "100005.52"
  "--max-price" "200000"
  "--grids" "35"
  "--groups" "7"
  "--fee-rate" "${FEE_RATE}"
  "--group-ratio" "1"
)

CONFIG_SETS=(
  "CONFIG_SET_1[@]"
  "CONFIG_SET_2[@]"
)

for config_ref in "${CONFIG_SETS[@]}"; do
  "${PYTHON_BIN}" "${SCRIPT_DIR}/grid_calculator.py" "${!config_ref}"
done
