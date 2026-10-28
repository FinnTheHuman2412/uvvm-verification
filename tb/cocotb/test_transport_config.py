import cocotb
from cocotb.triggers import Timer

from cosim.command_transport import CommandTransport


@cocotb.test()
async def test_transport_configuration(dut):
    transport = CommandTransport(
        dut,
        signals={
            "valid": "cmd_valid",
            "opcode": "cmd_opcode",
            "address": "cmd_addr",
            "data": "cmd_data",
            "busy": "cmd_busy",
            "done": "cmd_done",
        },
    )

    await Timer(500, unit="ns")

    # Verify signal widths are discovered correctly.
    assert len(transport.signals["opcode"]) == 3
    assert len(transport.signals["address"]) == 3
    assert len(transport.signals["data"]) == 8

    # Exercise the configured interface.
    await transport._execute(6, 0, 0)

    # Invalid data must be rejected.
    try:
        await transport._execute(6, 0, 256)
    except ValueError:
        pass
    else:
        raise AssertionError("Accepted 9-bit data")

    # Invalid opcode must be rejected.
    try:
        await transport._execute(8, 0, 0)
    except ValueError:
        pass
    else:
        raise AssertionError("Accepted 4-bit opcode")

    assert not transport._faulted

    dut._log.info("TRANSPORT_CONFIG_PASSED")
