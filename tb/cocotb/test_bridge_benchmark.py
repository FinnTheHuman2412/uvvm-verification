import os

import cocotb
from cocotb.triggers import Timer

from cosim.uvvm_controller import UVVMController


@cocotb.test()
async def benchmark_bridge_handshake(dut):
    controller = UVVMController(dut)

    await Timer(500, unit="ns")

    count = int(os.environ.get("BENCH_N", "1000"))
    assert count > 0

    for _ in range(count):
        await controller.noop()

    dut._log.info("BRIDGE_BENCHMARK_PASSED N=%d", count)
