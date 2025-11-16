#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
FEE_RATE="${FEE_RATE:-0.0008}"

# 如需新增配置，可复制下方数组并按需修改参数。
CONFIG_SET_1=(
  "--trading-pair" "BTC-USDT"
  "--capital" "3500"
  "--min-price" "92254.113070"
  "--max-price" "96960.000000"
  "--grids" "5"
  "--groups" "1"
  "--fee-rate" "${FEE_RATE}"
  "--group-ratio" "1"
)

CONFIG_SETS=(
  "CONFIG_SET_1[@]"
)

for config_ref in "${CONFIG_SETS[@]}"; do
  "${PYTHON_BIN}" "${SCRIPT_DIR}/grid_calculator.py" "${!config_ref}"
done
