import cocotb
from cocotb.triggers import Timer, RisingEdge, with_timeout


async def send_uvvm_uart(dut, value):
    assert int(dut.cmd_valid.value) == 0

    dut.cmd_data.value = value
    dut.cmd_valid.value = 1

    await with_timeout(
        RisingEdge(dut.cmd_done),
        20,
        "us"
    )

    await Timer(1, unit="ns")

    assert int(dut.cmd_busy.value) == 0

    dut._log.info(
        "UVVM transmission completed: 0x%02X",
        value
    )

    dut.cmd_valid.value = 0

    await Timer(1, unit="ns")

    assert int(dut.cmd_done.value) == 0


@cocotb.test()
async def test_multiple_python_uvvm_commands(dut):
    dut.cmd_valid.value = 0
    dut.cmd_data.value = 0

    await Timer(500, unit="ns")

    test_values = [0xA5, 0x55, 0xAA, 0x00, 0xFF]

    for value in test_values:
        await send_uvvm_uart(dut, value)

    dut._log.info(
        "All %d UVVM commands completed",
        len(test_values)
    )
