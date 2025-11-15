#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

# 如需新增等比网格配置，可复制下方数组并按需修改参数。
# 示例 1：已知最高价、最低价与网格数量，求单网格收益率
# CONFIG_SET_1=(
#   "--max-price" "200000"
#   "--min-price" "100000"
#   "--grids" "40"
# )

# 示例 2：已知最高价、最低价与单网格收益率，推导网格数量
# CONFIG_SET_2=(
#   "--max-price" "32000"
#   "--min-price" "16000"
#   "--grid-return-pct" "0.02"
# )

# 示例 3：已知最低价、网格数量与单网格收益率，推导最高价
# CONFIG_SET_3=(
#   "--min-price" "12000"
#   "--grids" "15"
#   "--grid-return-pct" "0.015"
# )

# 示例 4：已知最高价、网格数量与单网格收益率，推导最低价
# CONFIG_SET_4=(
#   "--max-price" "28000"
#   "--grids" "8"
#   "--grid-return-pct" "0.012"
# )

CONFIG_SET_1=(
  "--max-price" "96000"
  "--grids" "5"
  "--grid-return-pct" "0.01"
)

CONFIG_SETS=(
  "CONFIG_SET_1[@]"
)

separator_line="----------------------------------------"
first_run=true

for config_ref in "${CONFIG_SETS[@]}"; do
  if [ "${first_run}" = false ]; then
    printf '\n%s\n\n' "${separator_line}"
  fi
  first_run=false
  "${PYTHON_BIN}" "${SCRIPT_DIR}/geometric_grid_helper.py" "${!config_ref}"
done


