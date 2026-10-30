#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"
BUILD="$ROOT/build/ghdl"
mkdir -p "$BUILD"
if [ ! -f "$BUILD/uvvm_util-obj08.cf" ]; then
    bash external/UVVM/script/compile_all.sh ghdl "$ROOT/build"
fi
cd "$BUILD"
ghdl -a --std=08 -frelaxed-rules -P. "$ROOT/tb/generic/generic_vvc_th.vhd"
ghdl -e --std=08 -frelaxed-rules -P. generic_vvc_th
export PYTHONPATH="$ROOT:$ROOT/tb/cocotb:${PYTHONPATH:-}"
export COCOTB_TEST_MODULES=test_generic_vvc
export COCOTB_TOPLEVEL=generic_vvc_th
export TOPLEVEL_LANG=vhdl
export GPI_USERS="$(cocotb-config --pygpi-entry-point)"
export PYGPI_PYTHON_BIN="$(which python)"
export LD_PRELOAD="$CONDA_PREFIX/lib/libpython3.12.so.1.0"
ghdl -r --std=08 -frelaxed-rules -P. generic_vvc_th \
    --vpi="$(cocotb-config --lib-name-path vpi ghdl)" \
    --assert-level=error --stop-time=100us > "$ROOT/build/generic_cosim.log" 2>&1
cat "$ROOT/build/generic_cosim.log"
grep -Eq 'TESTS=7 PASS=7 FAIL=0' "$ROOT/build/generic_cosim.log"

COCOTB_TEST_MODULES=test_generic_timeout ghdl -r --std=08 -frelaxed-rules -P. generic_vvc_th \
    -gG_COMMAND_TIMEOUT_NS=1 \
    --vpi="$(cocotb-config --lib-name-path vpi ghdl)" \
    --assert-level=error --stop-time=100us > "$ROOT/build/generic_timeout.log" 2>&1
cat "$ROOT/build/generic_timeout.log"
grep -Eq 'TESTS=1 PASS=1 FAIL=0' "$ROOT/build/generic_timeout.log"

# Faulting tests must not share the permanently faulted bridge state.
export COCOTB_TEST_MODULES=test_generic_defects
for case_name in early_withdrawal changed_payload readiness_timeout separate_timeout_budgets lock_wait_excluded; do
    COCOTB_TEST_FILTER="^test_generic_defects\\.${case_name}$" \
    ghdl -r --std=08 -frelaxed-rules -P. generic_vvc_th \
        --vpi="$(cocotb-config --lib-name-path vpi ghdl)" \
        --assert-level=error --stop-time=100us > "$ROOT/build/generic_${case_name}.log" 2>&1
    cat "$ROOT/build/generic_${case_name}.log"
    grep -Eq 'TESTS=1 PASS=1 FAIL=0' "$ROOT/build/generic_${case_name}.log"
done
for field in cmd_vvc_type cmd_instance cmd_operation cmd_addr cmd_data; do
    MALFORMED_FIELD="$field" COCOTB_TEST_FILTER='unknown_payload$' \
    ghdl -r --std=08 -frelaxed-rules -P. generic_vvc_th \
        --vpi="$(cocotb-config --lib-name-path vpi ghdl)" \
        --assert-level=error --stop-time=100us > "$ROOT/build/generic_unknown_${field}.log" 2>&1
    cat "$ROOT/build/generic_unknown_${field}.log"
    grep -Eq 'TESTS=1 PASS=1 FAIL=0' "$ROOT/build/generic_unknown_${field}.log"
done
for severity in FAILURE TB_FAILURE; do
    CHECK_SEVERITY="$severity" COCOTB_TEST_FILTER='alert_severity$' \
    ghdl -r --std=08 -frelaxed-rules -P. generic_vvc_th \
        -gG_CHECK_ALERT_LEVEL="$severity" \
        --vpi="$(cocotb-config --lib-name-path vpi ghdl)" \
        --assert-level=error --stop-time=100us > "$ROOT/build/generic_${severity}.log" 2>&1
    cat "$ROOT/build/generic_${severity}.log"
    grep -Eq 'TESTS=1 PASS=1 FAIL=0' "$ROOT/build/generic_${severity}.log"
done
