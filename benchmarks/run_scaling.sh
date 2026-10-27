#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/build/ghdl"

export PYTHONPATH="$ROOT:$ROOT/tb/cocotb:${PYTHONPATH:-}"
export COCOTB_TEST_MODULES=test_uart_benchmark
export COCOTB_TOPLEVEL=uart_cosim_th
export TOPLEVEL_LANG=vhdl
export GPI_USERS="$(cocotb-config --pygpi-entry-point)"
export PYGPI_PYTHON_BIN="$(which python)"
export LD_PRELOAD="$CONDA_PREFIX/lib/libpython3.12.so.1.0"

OUT="$ROOT/benchmarks/results"
CSV="$OUT/scaling.csv"
mkdir -p "$OUT"

echo "implementation,transactions,run,wall_seconds" > "$CSV"

for n in 5 50 500 2000; do
  for implementation in native python direct; do
    for run in 1 2 3 4 5; do
      log="$OUT/${implementation}_${n}_${run}.log"
      timing="$OUT/time.tmp"

      if [[ "$implementation" == native ]]; then
        /usr/bin/time -f '%e' -o "$timing" \
          ghdl -r --std=08 -frelaxed-rules -P. uart_native_tb \
          -gG_N="$n" \
          --assert-level=error --stop-time=10ms \
          > "$log" 2>&1

        grep -q "NATIVE_UVVM_BENCHMARK_COMPLETED" "$log"
      elif [[ "$implementation" == python ]]; then
        BENCH_N="$n" /usr/bin/time -f '%e' -o "$timing" \
          ghdl -r --std=08 -frelaxed-rules -P. uart_cosim_th \
          --vpi="$(cocotb-config --lib-name-path vpi ghdl)" \
          --assert-level=error --stop-time=10ms \
          > "$log" 2>&1

        grep -q "TESTS=1 PASS=1 FAIL=0" "$log"
      else
        COCOTB_TEST_MODULES=test_uart_direct \
        COCOTB_TOPLEVEL=uart_direct_th BENCH_N="$n" \
          /usr/bin/time -f '%e' -o "$timing" \
          ghdl -r --std=08 -frelaxed-rules -P. uart_direct_th \
          --vpi="$(cocotb-config --lib-name-path vpi ghdl)" \
          --assert-level=error --stop-time=10ms \
          > "$log" 2>&1

        grep -Fq "DIRECT_COCOTB_BENCHMARK_PASSED N=$n" "$log"
        grep -Fq "TESTS=1 PASS=1 FAIL=0" "$log"
      fi

      seconds="$(cat "$timing")"
      echo "$implementation,$n,$run,$seconds" >> "$CSV"
      echo "$implementation | N=$n | run=$run | ${seconds}s"
    done
  done
done

rm -f "$OUT/time.tmp"
echo "Results saved to: $CSV"

# ------------------------------------------------------------
# Python-VHDL bridge vs cocotb timer-only benchmark
# ------------------------------------------------------------

BRIDGE_CSV="$OUT/bridge_scaling.csv"
echo "implementation,iterations,run,wall_seconds" > "$BRIDGE_CSV"

for n in 1000 10000 100000; do
  for implementation in timer bridge; do

    if [[ "$implementation" == timer ]]; then
      module="test_timer_benchmark"
      marker="TIMER_BENCHMARK_PASSED N=$n"
    else
      module="test_bridge_benchmark"
      marker="BRIDGE_BENCHMARK_PASSED N=$n"
    fi

    for run in 1 2 3 4 5; do
      log="$OUT/${implementation}_${n}_${run}.log"
      timing="$OUT/time.tmp"

      COCOTB_TEST_MODULES="$module" BENCH_N="$n" \
        /usr/bin/time -f '%e' -o "$timing" \
        ghdl -r --std=08 -frelaxed-rules -P. uart_cosim_th \
        --vpi="$(cocotb-config --lib-name-path vpi ghdl)" \
        --assert-level=error --stop-time=1ms \
        > "$log" 2>&1

      grep -Fq "$marker" "$log"
      grep -Fq "TESTS=1 PASS=1 FAIL=0" "$log"

      seconds="$(cat "$timing")"

      echo "$implementation,$n,$run,$seconds" >> "$BRIDGE_CSV"
      echo "$implementation | N=$n | run=$run | ${seconds}s"
    done
  done
done

rm -f "$OUT/time.tmp"
echo "Bridge results saved to: $BRIDGE_CSV"
