import cocotb
from cocotb.triggers import Timer

from cosim.command_transport import CommandTransport


@cocotb.test()
async def test_independent_transport(dut):
    transport = CommandTransport(
        dut,
        signals={
            "valid": "req_valid",
            "opcode": "req_op",
            "address": "req_addr",
            "data": "req_data",
            "busy": "rsp_busy",
            "done": "rsp_done",
        },
    )

    await Timer(1, unit="ns")

    assert len(transport.signals["opcode"]) == 4
    assert len(transport.signals["address"]) == 5
    assert len(transport.signals["data"]) == 16

    await transport._execute(15, 31, 65535)

    assert not transport._faulted

    dut._log.info("INDEPENDENT_TRANSPORT_PASSED")
