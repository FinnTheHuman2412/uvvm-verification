import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge


CLOCK_NS = 10
BIT_NS = 160
VALUES = [0xA5, 0x55, 0xAA, 0x00, 0xFF]


async def uart_send(dut, value):
    """Transmit one UART frame: start, 8 data bits, stop."""

    dut.rx_a.value = 0
    await Timer(BIT_NS, unit="ns")

    for bit in range(8):
        dut.rx_a.value = (value >> bit) & 1
        await Timer(BIT_NS, unit="ns")

    dut.rx_a.value = 1
    await Timer(BIT_NS, unit="ns")


async def sbi_read(dut, address):
    """Read a DUT register through its SBI interface."""

    await RisingEdge(dut.clk)

    dut.addr.value = address
    dut.cs.value = 1
    dut.rd.value = 1

    await Timer(CLOCK_NS, unit="ns")
    value = int(dut.rdata.value)

    dut.cs.value = 0
    dut.rd.value = 0

    await Timer(CLOCK_NS, unit="ns")

    return value


@cocotb.test()
async def benchmark_direct_uart(dut):
    count = int(os.environ.get("BENCH_N", "5"))
    assert count > 0

    dut.clk.value = 0
    dut.arst.value = 1
    dut.cs.value = 0
    dut.addr.value = 0
    dut.wr.value = 0
    dut.rd.value = 0
    dut.wdata.value = 0
    dut.rx_a.value = 1

    cocotb.start_soon(Clock(dut.clk, CLOCK_NS, unit="ns").start())

    await Timer(50, unit="ns")
    dut.arst.value = 0

    await Timer(50, unit="ns")

    verified = 0

    for i in range(count):
        expected = VALUES[i % len(VALUES)]

        await uart_send(dut, expected)
        await Timer(200, unit="ns")

        received = await sbi_read(dut, 0)

        assert received == expected, (
            f"Transaction {i}: expected 0x{expected:02X}, "
            f"received 0x{received:02X}"
        )
        verified += 1

    assert verified == count
    dut._log.info("DIRECT_COCOTB_VERIFIED_COUNT=%d", verified)

    dut._log.info(
        "DIRECT_COCOTB_BENCHMARK_PASSED N=%d", count
    )
