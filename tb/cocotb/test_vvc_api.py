"""Integration tests for the first typed UART/SBI facade."""
import cocotb
from cocotb.triggers import Timer

from cosim.vvc_api import Operation, VVC, VVCAPI, VVCCommand


@cocotb.test()
async def typed_api_uart_and_sbi(dut):
    api = VVCAPI(dut)
    await Timer(500, unit="ns")
    await api.execute(VVCCommand(VVC.UART, Operation.UART_TRANSMIT_CHECK, data=0xA5))
    await api.execute(VVCCommand(VVC.SBI, Operation.SBI_CHECK, address=3, data=1))
    await api.execute(VVCCommand(VVC.UART, Operation.UART_EXPECT, data=0x55))
    await api.execute(VVCCommand(VVC.SBI, Operation.SBI_WRITE, address=2, data=0x55))
    await api.execute(VVCCommand(VVC.UART, Operation.UART_AWAIT_RX))
    dut._log.info("GENERIC_VVC_API_PASSED")


@cocotb.test()
async def unsupported_instance_rejected(dut):
    api = VVCAPI(dut)
    try:
        await api.execute(VVCCommand(VVC.SBI, Operation.SBI_CHECK, instance=2))
    except ValueError as exc:
        assert "instance 1 only" in str(exc)
    else:
        raise AssertionError("Unsupported instance must be rejected")
    dut._log.info("GENERIC_VVC_INSTANCE_REJECTION_PASSED")
