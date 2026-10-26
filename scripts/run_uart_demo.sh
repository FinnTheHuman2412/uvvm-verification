#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

ROOT="$PWD"
UVVM="$ROOT/external/UVVM"
BUILD="$ROOT/build/ghdl"
RTL="$UVVM/bitvis_uart/src"
TB="$UVVM/bitvis_uart/tb"

mkdir -p "$BUILD"

# Compile UVVM
bash "$UVVM/script/compile_all.sh" ghdl "$ROOT/build"

cd "$BUILD"

# Compile UART design into WORK
for file in \
    uart_pkg.vhd \
    uart_pif_pkg.vhd \
    uart_core.vhd \
    uart_pif.vhd \
    uart.vhd
do
    ghdl -a --std=08 -frelaxed-rules -P. "$RTL/$file"
done

# Compile testbench
ghdl -a --std=08 -frelaxed-rules -P. "$TB/uart_vvc_demo_th.vhd"
ghdl -a --std=08 -frelaxed-rules -P. "$TB/uart_vvc_demo_tb.vhd"

# Elaborate and simulate
ghdl -e --std=08 -frelaxed-rules -P. uart_vvc_demo_tb

ghdl -r --std=08 -frelaxed-rules -P. uart_vvc_demo_tb \
    --assert-level=error \
    --stop-time=1ms
