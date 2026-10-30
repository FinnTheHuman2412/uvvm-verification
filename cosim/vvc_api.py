"""Typed Python facade for operations supported by the current UART/SBI bridge.

This is an adapter, not a generic VHDL command protocol.
"""
from dataclasses import dataclass
from enum import Enum

from cosim.uvvm_controller import UVVMController


class VVC(str, Enum):
    UART = "UART"
    SBI = "SBI"


class Operation(str, Enum):
    UART_TRANSMIT_CHECK = "TRANSMIT_CHECK"
    UART_EXPECT = "EXPECT"
    UART_AWAIT_RX = "AWAIT_RX"
    SBI_WRITE_CHECK_UART = "WRITE_CHECK_UART"
    SBI_WRITE = "WRITE"
    SBI_CHECK = "CHECK"


@dataclass(frozen=True)
class VVCCommand:
    vvc: VVC
    operation: Operation
    instance: int = 1
    address: int = 0
    data: int = 0


class VVCAPI:
    """Map typed VVC commands onto the verified legacy controller."""

    def __init__(self, dut, timeout_us=20, signals=None):
        self.controller = UVVMController(
            dut, timeout_us=timeout_us, signals=signals
        )

    async def execute(self, command: VVCCommand):
        if not isinstance(command, VVCCommand):
            raise TypeError("command must be VVCCommand")
        if command.instance != 1:
            raise ValueError("Current VHDL bridge supports VVC instance 1 only")
        if not isinstance(command.vvc, VVC) or not isinstance(command.operation, Operation):
            raise ValueError("Unknown VVC or operation")
        if not isinstance(command.address, int) or not 0 <= command.address <= 7:
            raise ValueError("address must be an integer in [0, 7]")
        if not isinstance(command.data, int) or not 0 <= command.data <= 255:
            raise ValueError("data must be an integer in [0, 255]")

        dispatch = {
            (VVC.UART, Operation.UART_TRANSMIT_CHECK):
                lambda: self.controller.uart_transmit(command.data),
            (VVC.UART, Operation.UART_EXPECT):
                lambda: self.controller.uart_expect(command.data),
            (VVC.UART, Operation.UART_AWAIT_RX):
                lambda: self.controller.await_uart_rx(),
            (VVC.SBI, Operation.SBI_WRITE_CHECK_UART):
                lambda: self.controller.sbi_write(command.address, command.data),
            (VVC.SBI, Operation.SBI_WRITE):
                lambda: self.controller.sbi_write_raw(command.address, command.data),
            (VVC.SBI, Operation.SBI_CHECK):
                lambda: self.controller.sbi_check(command.address, command.data),
        }
        action = dispatch.get((command.vvc, command.operation))
        if action is None:
            raise ValueError(
                f"Unsupported VVC operation: {command.vvc}/{command.operation}"
            )
        return await action()
