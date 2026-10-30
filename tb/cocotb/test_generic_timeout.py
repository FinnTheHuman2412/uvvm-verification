import cocotb
from cosim.generic_controller import GenericController, ProtocolError


@cocotb.test()
async def bridge_timeout(dut):
    controller = GenericController(dut)
    try:
        await controller.sbi_write(1, 0, 123)
    except ProtocolError:
        assert int(dut.cmd_status.value) == 3
    else:
        assert False, "VVC completion timeout was not reported"
    assert controller._faulted
    # Even a new controller cannot dispatch through the faulted bridge.
    replacement = GenericController(dut)
    try:
        await replacement.sbi_write(2, 0, 456)
    except ProtocolError:
        pass
    else:
        assert False, "Bridge accepted a command after timeout"
