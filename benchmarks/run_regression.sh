#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build/ghdl"
OUT="$ROOT/benchmarks/results/regression"

mkdir -p "$OUT"

echo "=== UVVM REGRESSION ==="

# 1. Compile UVVM and UART RTL using existing build script.
echo "[1/4] Building UVVM and UART..."
bash "$ROOT/scripts/run_uart_demo.sh" \
  > "$OUT/build.log" 2>&1

# 2. Compile additional testbenches.
echo "[2/4] Compiling regression testbenches..."
cd "$BUILD"

ghdl -a --std=08 -frelaxed-rules -P. \
  "$ROOT/tb/uvvm/uart_cosim_th.vhd"

ghdl -a --std=08 -frelaxed-rules -P. \
  "$ROOT/tb/direct/uart_direct_th.vhd"

ghdl -a --std=08 -frelaxed-rules -P. \
  "$ROOT/benchmarks/native_uvvm/uart_native_tb.vhd"

for top in uart_cosim_th uart_direct_th uart_native_tb; do
  ghdl -e --std=08 -frelaxed-rules -P. "$top"
done

# 3. Configure cocotb.
export PYTHONPATH="$ROOT:$ROOT/tb/cocotb:${PYTHONPATH:-}"
export TOPLEVEL_LANG=vhdl
export GPI_USERS="$(cocotb-config --pygpi-entry-point)"
export PYGPI_PYTHON_BIN="$(which python)"

if [[ -n "${CONDA_PREFIX:-}" ]]; then
  export LD_PRELOAD="$CONDA_PREFIX/lib/libpython3.12.so.1.0"
fi

VPI="$(cocotb-config --lib-name-path vpi ghdl)"

# 4. Execute functional verification.
echo "[3/4] Running functional tests..."

echo "  Native UVVM..."
ghdl -r --std=08 -frelaxed-rules -P. uart_native_tb \
  -gG_N=5 \
  --assert-level=error --stop-time=1ms \
  > "$OUT/native.log" 2>&1

grep -Fq "NATIVE_UVVM_BENCHMARK_COMPLETED" "$OUT/native.log"
echo "  PASS: Native UVVM"

echo "  Python-controlled UVVM..."
COCOTB_TEST_MODULES=test_uart_cosim \
COCOTB_TOPLEVEL=uart_cosim_th \
ghdl -r --std=08 -frelaxed-rules -P. uart_cosim_th \
  --vpi="$VPI" \
  --assert-level=error --stop-time=1ms \
  > "$OUT/python_uvvm.log" 2>&1

grep -Eq 'TESTS=4 PASS=4 FAIL=0' "$OUT/python_uvvm.log"
echo "  PASS: Python-controlled UVVM"

echo "  Direct cocotb..."
COCOTB_TEST_MODULES=test_uart_direct \
COCOTB_TOPLEVEL=uart_direct_th \
BENCH_N=5 \
ghdl -r --std=08 -frelaxed-rules -P. uart_direct_th \
  --vpi="$VPI" \
  --assert-level=error --stop-time=1ms \
  > "$OUT/direct.log" 2>&1

grep -Fq "DIRECT_COCOTB_VERIFIED_COUNT=5" "$OUT/direct.log"
grep -Fq "TESTS=1 PASS=1 FAIL=0" "$OUT/direct.log"
echo "  PASS: Direct cocotb"

echo "[4/4] Regression complete."
echo "================================"
echo "ALL REGRESSION TESTS PASSED"
echo "================================"
