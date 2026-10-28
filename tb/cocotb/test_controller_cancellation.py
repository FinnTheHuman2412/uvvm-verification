import cocotb
from cocotb.triggers import Timer

from cosim.uvvm_controller import UVVMController


@cocotb.test()
async def test_cancel_active_command(dut):
    controller = UVVMController(dut)
    await Timer(500, unit="ns")

    task = cocotb.start_soon(
        controller.uart_transmit(0xA5)
    )

    # Allow the transaction to begin.
    await Timer(100, unit="ns")

    assert not task.done()

    # Cancel while the UVVM transaction is active.
    task.cancel()

    await Timer(1, unit="ns")

    assert controller._faulted, (
        "Controller must be faulted after cancellation"
    )

    try:
        await controller.noop()
    except RuntimeError as exc:
        assert "faulted" in str(exc)
    else:
        raise AssertionError(
            "Controller accepted a command after cancellation"
        )

    dut._log.info("CONTROLLER_CANCELLATION_PASSED")
