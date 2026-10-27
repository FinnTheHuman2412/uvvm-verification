#!/usr/bin/env python3
"""Analyze native UVVM and Python-controlled UVVM benchmark results."""

import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

ROOT = Path(__file__).resolve().parent
CSV = ROOT / "results" / "scaling.csv"

EXPECTED_COUNTS = (5, 50, 500, 2000)
IMPLEMENTATIONS = ("native", "python")


def load_results():
    results = defaultdict(list)

    with CSV.open(newline="") as f:
        for row in csv.DictReader(f):
            implementation = row["implementation"]
            count = int(row["transactions"])
            runtime = float(row["wall_seconds"])

            assert implementation in IMPLEMENTATIONS
            assert count in EXPECTED_COUNTS
            assert runtime > 0

            results[implementation, count].append(runtime)

    return results


def analyze(results):
    print("\nUART VERIFICATION SCALING")
    print("-" * 77)
    print(
        f"{'N':>7} "
        f"{'Native mean':>13} "
        f"{'Native SD':>12} "
        f"{'Python mean':>13} "
        f"{'Python SD':>12} "
        f"{'Overhead':>10}"
    )

    for n in EXPECTED_COUNTS:
        native = results["native", n]
        python = results["python", n]

        assert len(native) >= 2
        assert len(python) >= 2

        n_mean = mean(native)
        p_mean = mean(python)
        overhead = 100 * (p_mean / n_mean - 1)

        print(
            f"{n:7d} "
            f"{n_mean:13.4f} "
            f"{stdev(native):12.4f} "
            f"{p_mean:13.4f} "
            f"{stdev(python):12.4f} "
            f"{overhead:9.2f}%"
        )


def linear_regression(results, implementation):
    """Fit wall-clock runtime T(N) = intercept + slope * N."""
    x = list(EXPECTED_COUNTS)
    y = [mean(results[implementation, n]) for n in x]

    x_mean = mean(x)
    y_mean = mean(y)

    slope = sum(
        (a - x_mean) * (b - y_mean)
        for a, b in zip(x, y)
    ) / sum((a - x_mean) ** 2 for a in x)

    intercept = y_mean - slope * x_mean

    predicted = [intercept + slope * n for n in x]

    ss_res = sum((a - b) ** 2 for a, b in zip(y, predicted))
    ss_tot = sum((a - y_mean) ** 2 for a in y)

    r_squared = 1 - ss_res / ss_tot

    return intercept, slope, r_squared


def analyze_regression(results):
    print("\nLINEAR REGRESSION: T(N) = T0 + N * t")
    print("-" * 65)

    fits = {}

    for implementation in IMPLEMENTATIONS:
        intercept, slope, r_squared = linear_regression(
            results, implementation
        )

        fits[implementation] = (intercept, slope)

        print(
            f"{implementation:>8}: "
            f"fixed={intercept * 1000:.2f} ms, "
            f"incremental={slope * 1000:.3f} ms/transaction, "
            f"R²={r_squared:.6f}"
        )

    native_fixed, native_slope = fits["native"]
    python_fixed, python_slope = fits["python"]

    print("\nADDITIONAL PYTHON-CONTROLLED RUNTIME")
    print(f"Fixed difference: {(python_fixed - native_fixed) * 1000:.2f} ms")
    print(
        f"Incremental difference: "
        f"{(python_slope - native_slope) * 1000:.3f} ms/transaction"
    )


def validate_logs():
    """Verify every recorded run contains exactly N successful readbacks."""

    total = 0

    with CSV.open(newline="") as f:
        for row in csv.DictReader(f):
            implementation = row["implementation"]
            n = int(row["transactions"])
            run = int(row["run"])

            log_path = ROOT / "results" / (
                f"{implementation}_{n}_{run}.log"
            )

            log = log_path.read_text()

            matches = [
                line for line in log.splitlines()
                if "sbi_check(A:" in line
                and "=> OK" in line
            ]
            assert len(matches) == n, (
                f"{log_path}: expected {n} successful "
                f"SBI checks, found {len(matches)}"
            )

            if implementation == "native":
                assert "NATIVE_UVVM_BENCHMARK_COMPLETED" in log
            else:
                assert "TESTS=1 PASS=1 FAIL=0" in log

            assert not any(
                "UVVM:" in line and (
                    "ID_ALERT" in line
                    or "ERROR #" in line
                    or "TB_ERROR" in line
                )
                for line in log.splitlines()
            ), f"UVVM error detected in {log_path}"

            total += 1

    print(f"\nVALIDATED: {total} runs with exact SBI check counts")


def analyze_bridge():
    """Analyze timer-only versus Python-VHDL bridge runtime."""
    bridge_csv = ROOT / "results" / "bridge_scaling.csv"
    results = defaultdict(list)

    with bridge_csv.open(newline="") as f:
        for row in csv.DictReader(f):
            key = (row["implementation"], int(row["iterations"]))
            results[key].append(float(row["wall_seconds"]))

    print("\nBRIDGE HANDSHAKE SCALING")
    print("-" * 70)
    print(
        f"{'N':>9} {'Timer (s)':>12} "
        f"{'Bridge (s)':>12} {'Extra (us/op)':>16}"
    )

    for n in (1000, 10000, 100000):
        timer = results["timer", n]
        bridge = results["bridge", n]

        assert len(timer) == 5
        assert len(bridge) == 5

        t_mean = mean(timer)
        b_mean = mean(bridge)

        extra_us = (b_mean - t_mean) * 1e6 / n

        print(
            f"{n:9d} {t_mean:12.4f} "
            f"{b_mean:12.4f} {extra_us:16.2f}"
        )

    print("\nNote: Values include simulator and scheduling overhead.")


def validate_bridge_logs():
    """Validate all bridge and timer benchmark executions."""
    total = 0
    csv_path = ROOT / "results" / "bridge_scaling.csv"

    with csv_path.open(newline="") as f:
        for row in csv.DictReader(f):
            implementation = row["implementation"]
            n = int(row["iterations"])
            run = int(row["run"])

            assert implementation in ("timer", "bridge")
            assert n in (1000, 10000, 100000)
            assert float(row["wall_seconds"]) > 0

            log_path = ROOT / "results" / (
                f"{implementation}_{n}_{run}.log"
            )

            log = log_path.read_text()

            marker = (
                f"TIMER_BENCHMARK_PASSED N={n}"
                if implementation == "timer"
                else f"BRIDGE_BENCHMARK_PASSED N={n}"
            )

            assert marker in log, log_path
            assert "TESTS=1 PASS=1 FAIL=0" in log, log_path

            assert not any(
                "UVVM:" in line and (
                    "ID_ALERT" in line or "ERROR #" in line
                )
                for line in log.splitlines()
            ), log_path

            total += 1

    assert total == 30, f"Expected 30 runs, found {total}"
    print(f"\\nVALIDATED: {total} bridge/timer benchmark runs")


if __name__ == "__main__":
    results = load_results()
    analyze(results)
    analyze_regression(results)
    validate_logs()
    analyze_bridge()
    validate_bridge_logs()
