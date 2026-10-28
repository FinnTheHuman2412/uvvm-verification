import cocotb
from cocotb.triggers import Timer

from cosim.uvvm_controller import UVVMController
from cosim.command_transport import UVVMVerificationError


@cocotb.test()
async def test_verification_failure(dut):
    controller = UVVMController(dut)
    await Timer(500, unit="ns")

    # Establish a known register value.
    await controller.sbi_write_raw(0, 0x55)

    # Deliberately request an incorrect value.
    try:
        await controller.sbi_check(0, 0xAA)
    except UVVMVerificationError:
        pass
    else:
        raise AssertionError(
            "Expected UVVMVerificationError"
        )

    assert not controller._faulted

    # The verification failed, but transport remains operational.
    await controller.noop()

    dut._log.info("VERIFICATION_FAILURE_PASSED")
