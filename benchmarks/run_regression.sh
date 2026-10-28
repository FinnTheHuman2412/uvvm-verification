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

echo "  Concurrent Python commands..."
COCOTB_TEST_MODULES=test_concurrent_commands \
COCOTB_TOPLEVEL=uart_cosim_th \
ghdl -r --std=08 -frelaxed-rules -P. uart_cosim_th \
  --vpi="$VPI" \
  --assert-level=error --stop-time=100us \
  > "$OUT/concurrent.log" 2>&1

grep -Fq "CONCURRENT_COMMANDS_PASSED N=20" "$OUT/concurrent.log"
grep -Fq "CONCURRENT_UART_PASSED N=5" "$OUT/concurrent.log"
grep -Fq "TESTS=2 PASS=2 FAIL=0" "$OUT/concurrent.log"
echo "  PASS: Concurrent Python commands"

echo "  Controller timeout handling..."
COCOTB_TEST_MODULES=test_controller_timeout \
COCOTB_TOPLEVEL=uart_cosim_th \
ghdl -r --std=08 -frelaxed-rules -P. uart_cosim_th \
  --vpi="$VPI" \
  --assert-level=error --stop-time=100us \
  > "$OUT/controller_timeout.log" 2>&1

grep -Fq "CONTROLLER_TIMEOUT_PASSED" "$OUT/controller_timeout.log"
grep -Fq "TESTS=1 PASS=1 FAIL=0" "$OUT/controller_timeout.log"
echo "  PASS: Controller timeout handling"

echo "  Controller cancellation handling..."
COCOTB_TEST_MODULES=test_controller_cancellation \
COCOTB_TOPLEVEL=uart_cosim_th \
ghdl -r --std=08 -frelaxed-rules -P. uart_cosim_th \
  --vpi="$VPI" \
  --assert-level=error --stop-time=100us \
  > "$OUT/controller_cancellation.log" 2>&1

grep -Fq "CONTROLLER_CANCELLATION_PASSED" "$OUT/controller_cancellation.log"
grep -Fq "TESTS=1 PASS=1 FAIL=0" "$OUT/controller_cancellation.log"
echo "  PASS: Controller cancellation handling"

echo "  Transport configuration..."
COCOTB_TEST_MODULES=test_transport_config \
COCOTB_TOPLEVEL=uart_cosim_th \
ghdl -r --std=08 -frelaxed-rules -P. uart_cosim_th \
  --vpi="$VPI" \
  --assert-level=error --stop-time=100us \
  > "$OUT/transport_config.log" 2>&1

grep -Fq "TRANSPORT_CONFIG_PASSED" "$OUT/transport_config.log"
grep -Fq "TESTS=1 PASS=1 FAIL=0" "$OUT/transport_config.log"
echo "  PASS: Transport configuration"

echo "  Independent transport..."
ghdl -a --std=08 ../../tb/transport/transport_test_th.vhd
ghdl -e --std=08 transport_test_th

COCOTB_TEST_MODULES=test_transport_independent \
COCOTB_TOPLEVEL=transport_test_th \
ghdl -r --std=08 transport_test_th \
  --vpi="$VPI" \
  --assert-level=error --stop-time=10us \
  > "$OUT/independent_transport.log" 2>&1

grep -Fq "INDEPENDENT_TRANSPORT_PASSED" "$OUT/independent_transport.log"
grep -Fq "TESTS=1 PASS=1 FAIL=0" "$OUT/independent_transport.log"
echo "  PASS: Independent transport"

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
