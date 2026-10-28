import cocotb
from cocotb.triggers import Timer

from cosim.uvvm_controller import UVVMController


@cocotb.test()
async def test_controller_timeout(dut):
    controller = UVVMController(dut, timeout_us=0.1)
    await Timer(500, unit="ns")

    try:
        await controller.uart_transmit(0xA5)
    except TimeoutError:
        pass
    else:
        raise AssertionError("Expected timeout")

    assert controller._faulted

    try:
        await controller.noop()
    except RuntimeError as exc:
        assert "faulted" in str(exc)
    else:
        raise AssertionError("Faulted controller accepted a command")

    dut._log.info("CONTROLLER_TIMEOUT_PASSED")
