"""Synchronous Python–UVVM protocol v1 controller."""
from enum import IntEnum

from cocotb.triggers import RisingEdge, with_timeout
from cosim.command_transport import CommandTransport, UVVMVerificationError


class VVCType(IntEnum):
    SBI = 1


class Operation(IntEnum):
    WRITE = 1
    CHECK = 2


class Status(IntEnum):
    SUCCESS = 0
    VERIFICATION_FAILURE = 1
    UNSUPPORTED = 2
    INTERNAL_ERROR = 3


class UnsupportedCommandError(UVVMVerificationError):
    """The bridge rejected a target or operation without dispatching it."""


class ProtocolError(RuntimeError):
    """The bridge reported an internal error; restart the simulation."""


class GenericController(CommandTransport):
    """Serialize v1 commands using CommandTransport's phase timeout budgets.

    ``timeout_us`` bounds readiness and completion waits independently. Lock
    queueing is unbounded; handshake cleanup takes a further 2 ns.
    """

    def __init__(self, dut, timeout_us=20):
        super().__init__(
            dut, timeout_us=timeout_us, require_status=True,
            signals={"opcode": "cmd_operation"},
            extra_signals={"vvc_type": "cmd_vvc_type", "instance": "cmd_instance"},
        )
        self.signals["vvc_type"].value = 0
        self.signals["instance"].value = 0

    async def execute(self, vvc_type, instance, operation, address=0, data=0):
        try:
            if self.dut.cmd_ready.value != 1:
                await with_timeout(RisingEdge(self.dut.cmd_ready), self._timeout_us, "us")
        except BaseException:
            self._faulted = True
            raise
        await self._execute(operation, address, data, vvc_type=vvc_type, instance=instance)

    def _check_status(self, status, opcode):
        if status == Status.UNSUPPORTED:
            raise UnsupportedCommandError("Unsupported VVC target or operation")
        if status == Status.INTERNAL_ERROR:
            raise ProtocolError("UVVM bridge internal protocol error")
        super()._check_status(status, opcode)

    async def sbi_write(self, instance, address, data):
        await self.execute(VVCType.SBI, instance, Operation.WRITE, address, data)

    async def sbi_check(self, instance, address, expected):
        await self.execute(VVCType.SBI, instance, Operation.CHECK, address, expected)
