import cocotb
from cocotb.triggers import Timer, RisingEdge, with_timeout


@cocotb.test()
async def test_python_controls_uvvm(dut):
    dut.cmd_valid.value = 0
    dut.cmd_data.value = 0

    # Allow UVVM initialization and UART reset
    await Timer(500, unit="ns")

    # Request UART transmission of 0xA5
    dut.cmd_data.value = 0xA5
    dut.cmd_valid.value = 1

    # Wait for UVVM transaction completion
    await with_timeout(
        RisingEdge(dut.cmd_done),
        20,
        "us"
    )

    await Timer(1, unit="ns")
    assert int(dut.cmd_busy.value) == 0

    # Acknowledge completion
    dut.cmd_valid.value = 0
    await Timer(1, unit="ns")
    assert int(dut.cmd_done.value) == 0

    dut._log.info("Python-to-UVVM command completed")
