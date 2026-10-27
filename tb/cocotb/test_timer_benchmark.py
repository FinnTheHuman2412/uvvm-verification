import os

import cocotb
from cocotb.triggers import Timer


@cocotb.test()
async def benchmark_timer_only(dut):
    count = int(os.environ.get("BENCH_N", "1000"))

    await Timer(500, unit="ns")

    for _ in range(count):
        await Timer(1, unit="ns")
        await Timer(1, unit="ns")

    dut._log.info("TIMER_BENCHMARK_PASSED N=%d", count)
