import cocotb

from cosim.uvvm_controller import UVVMController


@cocotb.test()
async def test_command_without_startup_delay(dut):
    controller = UVVMController(dut)

    # Deliberately omit the existing 500 ns startup delay.
    await controller.noop()

    dut._log.info("STARTUP_HANDSHAKE_PASSED")
