import cocotb

from cocotb.triggers import Timer
from cosim.uvvm_controller import UVVMController


@cocotb.test()
async def test_concurrent_commands(dut):
    controller = UVVMController(dut)
    await Timer(500, unit='ns')

    # Launch 20 commands concurrently through one controller.
    tasks = [
        cocotb.start_soon(controller.noop())
        for _ in range(20)
    ]

    for task in tasks:
        await task

    assert int(dut.cmd_valid.value) == 0
    assert int(dut.cmd_done.value) == 0

    dut._log.info("CONCURRENT_COMMANDS_PASSED N=20")


@cocotb.test()
async def test_concurrent_uart(dut):
    controller = UVVMController(dut)
    await Timer(500, unit="ns")

    values = [0xA5, 0x55, 0xAA, 0x00, 0xFF]

    tasks = [
        cocotb.start_soon(controller.uart_transmit(value))
        for value in values
    ]

    for task in tasks:
        await task

    assert int(dut.cmd_valid.value) == 0
    assert int(dut.cmd_done.value) == 0

    dut._log.info("CONCURRENT_UART_PASSED N=5")
