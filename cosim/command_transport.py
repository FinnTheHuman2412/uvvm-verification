from cocotb.triggers import Timer, RisingEdge, with_timeout, Lock


class CommandTransport:
    def __init__(self, dut, timeout_us=20):
        self.dut = dut
        self._lock = Lock()
        self._faulted = False
        self._timeout_us = timeout_us

        dut.cmd_valid.value = 0
        dut.cmd_opcode.value = 0
        dut.cmd_addr.value = 0
        dut.cmd_data.value = 0

    async def _execute(self, opcode, address, value):
        async with self._lock:
            if self._faulted:
                raise RuntimeError(
                    "UVVM controller is faulted; restart the simulation"
                )

            if not 0 <= value <= 255:
                raise ValueError("Data must be an 8-bit unsigned value")

            if not 0 <= address <= 7:
                raise ValueError("SBI address must be between 0 and 7")

            dut = self.dut

            try:
                assert int(dut.cmd_valid.value) == 0

                dut.cmd_opcode.value = opcode
                dut.cmd_addr.value = address
                dut.cmd_data.value = value
                dut.cmd_valid.value = 1

                await with_timeout(
                    RisingEdge(dut.cmd_done),
                    self._timeout_us,
                    "us"
                )

                await Timer(1, unit="ns")
                assert int(dut.cmd_busy.value) == 0

                dut.cmd_valid.value = 0

                await Timer(1, unit="ns")
                assert int(dut.cmd_done.value) == 0

            except BaseException:
                self._faulted = True
                raise

