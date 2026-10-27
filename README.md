# Python-Controlled UVVM Verification

An experimental framework for controlling UVVM Verification Components
(VVCs) from Python using cocotb and GHDL.

The project evaluates the feasibility and runtime performance of
Python-controlled VHDL verification.

## Architecture

Three approaches are implemented:

1. **Native UVVM:** VHDL directly coordinates UVVM UART and SBI VVCs.
2. **Python-controlled UVVM:** cocotb sends commands through a VHDL
   interface that executes UVVM transactions.
3. **Direct cocotb:** Python drives the UART and SBI interfaces directly,
   without UVVM. Its clock is generated in VHDL.

All three exercise the same UART RTL from UVVM.

## Requirements

- Linux
- GHDL 4.1.0
- Python 3.12
- cocotb 2.1.0
- GNU Make
- Git

These are the versions used during development.

The current scripts assume a configured Python environment and use the
cocotb VPI interface for GHDL. The benchmark runner also assumes that
the VHDL testbenches have already been compiled.

## Installation

Clone the repository with its UVVM submodule:

    git clone --recurse-submodules https://github.com/FinnTheHuman2412/uvvm-verification.git
    cd uvvm-verification

Alternatively, initialize the submodule in an existing checkout:

    git submodule update --init --recursive

Activate a Python environment containing cocotb before running the tests.

## Functional Regression

Run all three verification implementations:

    make regression

Rebuild and verify from a clean state:

    make clean
    make regression

The regression runner compiles UVVM and UART RTL, executes the testbenches,
and checks their completion status.

## Performance Benchmarking

First compile the verification environment:

    make regression

Then run the benchmarks:

    bash benchmarks/run_scaling.sh

Analyze the results:

    python benchmarks/analyze.py

UART workloads contain 5, 50, 500, or 2000 transactions, with five
repetitions per implementation.

Additional experiments measure cocotb timer scheduling and the
Python-to-VHDL command handshake.

## Latest Benchmark Results

Mean wall-clock runtime for 2000 UART transactions:

| Implementation | Runtime |
|---|---:|
| Native UVVM | 5.584 s |
| Python-controlled UVVM | 6.212 s |
| Direct cocotb | 2.752 s |

Python-controlled UVVM was 11.25% slower than native UVVM in this run.

These measurements represent complete simulation runtime, not isolated
Python, cocotb, or UVVM overhead.

The implementations share UART RTL and bit timing, but their SBI
scheduling and verification infrastructure differ.

Results should therefore not be interpreted as a universal performance
ranking of verification frameworks.

## Project Structure

- `cosim/` — Python interface for UVVM control
- `tb/uvvm/` — Python-controlled UVVM harness
- `tb/direct/` — Direct cocotb harness
- `tb/cocotb/` — cocotb verification tests
- `benchmarks/native_uvvm/` — Native UVVM benchmark
- `benchmarks/run_regression.sh` — Automated functional regression
- `benchmarks/run_scaling.sh` — Performance benchmark runner
- `benchmarks/analyze.py` — Benchmark analysis and log validation
- `scripts/` — Build scripts
- `external/UVVM/` — UVVM dependency

## Limitations

- Measurements were collected in one development environment.
- Host-system conditions can affect measured runtime.
- The verification approaches have different SBI scheduling.
- Their diagnostic and protocol-checking coverage is not identical.
- The build scripts currently depend on a configured local toolchain.
