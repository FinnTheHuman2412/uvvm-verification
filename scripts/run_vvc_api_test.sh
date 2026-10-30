#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/benchmarks/results/regression"
BUILD="$ROOT/build/ghdl"

# Keep the existing regression as a compatibility gate.
make -C "$ROOT" regression

mkdir -p "$OUT"
cd "$BUILD"

export PYTHONPATH="$ROOT:$ROOT/tb/cocotb:${PYTHONPATH:-}"
export TOPLEVEL_LANG=vhdl
export GPI_USERS="$(cocotb-config --pygpi-entry-point)"
export PYGPI_PYTHON_BIN="$(command -v python)"

# Match the interpreter in the active environment instead of hardcoding 3.12.
if [[ -n "${CONDA_PREFIX:-}" ]]; then
  VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  LIB="$CONDA_PREFIX/lib/libpython$VERSION.so.1.0"
  if [[ -f "$LIB" ]]; then
    export LD_PRELOAD="$LIB"
  else
    echo "Cannot find required Python shared library: $LIB" >&2
    exit 1
  fi
fi

COCOTB_TEST_MODULES=test_vvc_api \
COCOTB_TOPLEVEL=uart_cosim_th \
ghdl -r --std=08 -frelaxed-rules -P. uart_cosim_th \
  --vpi="$(cocotb-config --lib-name-path vpi ghdl)" \
  --assert-level=error --stop-time=1ms \
  > "$OUT/vvc_api.log" 2>&1

grep -Fq "GENERIC_VVC_API_PASSED" "$OUT/vvc_api.log"
grep -Fq "GENERIC_VVC_INSTANCE_REJECTION_PASSED" "$OUT/vvc_api.log"
grep -Eq 'TESTS=2 PASS=2 FAIL=0' "$OUT/vvc_api.log"
echo "PASS: Generic VVC API integration tests"
