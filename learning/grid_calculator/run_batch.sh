#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
FEE_RATE="${FEE_RATE:-0.0008}"

COMMON_ARGS=(
  "--trading-pair" "BTC-USDT"
  "--capital" "50000"
  "--min-price" "99662.971305"
  "--max-price" "200000"
  "--grids" "70"
  "--groups" "14"
  "--fee-rate" "${FEE_RATE}"
  "--group-ratio" "1"
)

echo "运行 grid_calculator.py"
"${PYTHON_BIN}" "${SCRIPT_DIR}/grid_calculator.py" "${COMMON_ARGS[@]}"
