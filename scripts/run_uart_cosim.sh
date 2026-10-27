#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

ROOT="$PWD"
BUILD="$ROOT/build/ghdl"
UVVM="$ROOT/external/UVVM"

mkdir -p "$BUILD"

# Compile UVVM only if the compiled libraries are missing.
if [ ! -f "$BUILD/uvvm_util-obj08.cf" ]; then
    bash "$UVVM/script/compile_all.sh" ghdl "$ROOT/build"
fi

cd "$BUILD"

# Compile UART DUT and custom test harness.
RTL="$UVVM/bitvis_uart/src"

for file in uart_pkg.vhd uart_pif_pkg.vhd uart_core.vhd uart_pif.vhd uart.vhd; do
    ghdl -a --std=08 -frelaxed-rules -P. "$RTL/$file"
done

ghdl -a --std=08 -frelaxed-rules -P. \
    "$ROOT/tb/uvvm/uart_cosim_th.vhd"

ghdl -e --std=08 -frelaxed-rules -P. uart_cosim_th

# Initialize cocotb.
export PYTHONPATH="$ROOT:$ROOT/tb/cocotb:${PYTHONPATH:-}"
export COCOTB_TEST_MODULES=test_uart_cosim
export COCOTB_TOPLEVEL=uart_cosim_th
export TOPLEVEL_LANG=vhdl
export GPI_USERS="$(cocotb-config --pygpi-entry-point)"
export PYGPI_PYTHON_BIN="$(which python)"
export LD_PRELOAD="$CONDA_PREFIX/lib/libpython3.12.so.1.0"

# Execute co-simulation.
ghdl -r --std=08 -frelaxed-rules -P. uart_cosim_th \
    --vpi="$(cocotb-config --lib-name-path vpi ghdl)" \
    --assert-level=error \
    --stop-time=20us
