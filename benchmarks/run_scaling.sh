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
  for implementation in native python; do
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
      else
        BENCH_N="$n" /usr/bin/time -f '%e' -o "$timing" \
          ghdl -r --std=08 -frelaxed-rules -P. uart_cosim_th \
          --vpi="$(cocotb-config --lib-name-path vpi ghdl)" \
          --assert-level=error --stop-time=10ms \
          > "$log" 2>&1

        grep -q "TESTS=1 PASS=1 FAIL=0" "$log"
      fi

      seconds="$(cat "$timing")"
      echo "$implementation,$n,$run,$seconds" >> "$CSV"
      echo "$implementation | N=$n | run=$run | ${seconds}s"
    done
  done
done

rm -f "$OUT/time.tmp"
echo "Results saved to: $CSV"
