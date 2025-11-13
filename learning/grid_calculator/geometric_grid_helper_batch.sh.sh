#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

# 如需新增等比网格配置，可复制下方数组并按需修改参数。
CONFIG_SET_1=(
  "--max-price" "200000"
  "--min-price" "100000"
  "--grids" "40"
)

CONFIG_SET_2=(
  "--max-price" "32000"
  "--min-price" "16000"
  "--grid-return-pct" "0.02"
)

CONFIG_SET_3=(
  "--min-price" "12000"
  "--grids" "15"
  "--grid-return-pct" "0.015"
)

CONFIG_SETS=(
  "CONFIG_SET_1[@]"
  "CONFIG_SET_2[@]"
  "CONFIG_SET_3[@]"
)

for config_ref in "${CONFIG_SETS[@]}"; do
  "${PYTHON_BIN}" "${SCRIPT_DIR}/geometric_grid_helper.py" "${!config_ref}"
done


