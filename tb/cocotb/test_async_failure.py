import cocotb
from cocotb.triggers import Timer

from cosim.uvvm_controller import UVVMController
from cosim.command_transport import UVVMVerificationError


@cocotb.test()
async def test_async_failure_attribution(dut):
    uvvm = UVVMController(dut)
    await Timer(500, unit="ns")

    # Queue an expectation that will deliberately fail.
    await uvvm.uart_expect(0xAA)

    # Transmit a different byte through the UART DUT.
    await uvvm.sbi_write_raw(address=2, value=0x55)

    # Allow the asynchronous UART verification to finish.
    await Timer(5, unit="us")

    # This command is unrelated to the UART expectation.
    try:
        await uvvm.noop()
    except UVVMVerificationError:
        dut._log.info("ASYNC_FAILURE_ATTRIBUTED_TO_NOOP")
    else:
        raise AssertionError("Asynchronous UVVM error was lost")

    # Previously reported errors must not be reported again.
    await uvvm.noop()
    await uvvm.await_uart_rx()

    dut._log.info("ASYNC_FAILURE_RECOVERY_PASSED")
