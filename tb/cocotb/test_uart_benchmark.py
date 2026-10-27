import os
import cocotb
from cocotb.triggers import Timer

from cosim.uvvm_controller import UVVMController


@cocotb.test()
async def benchmark_five_uart_transactions(dut):
    uvvm = UVVMController(dut)

    await Timer(500, unit="ns")

    values = [0xA5, 0x55, 0xAA, 0x00, 0xFF]
    count = int(os.environ.get("BENCH_N", "5"))

    assert count > 0

    for i in range(count):
        value = values[i % len(values)]
        await uvvm.uart_transmit(value)

    dut._log.info("BENCHMARK_5_UART_TRANSACTIONS_PASSED")
