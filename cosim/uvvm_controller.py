from cocotb.triggers import Timer, RisingEdge, with_timeout, Lock


class UVVMController:
    UART_TX = 0
    SBI_WRITE = 1
    SBI_CHECK = 2
    UART_EXPECT = 3
    SBI_WRITE_RAW = 4
    AWAIT_UART_RX = 5
    NOOP = 6

    def __init__(self, dut):
        self.dut = dut
        self._lock = Lock()

        dut.cmd_valid.value = 0
        dut.cmd_opcode.value = 0
        dut.cmd_addr.value = 0
        dut.cmd_data.value = 0

    async def _execute(self, opcode, address, value):
        async with self._lock:
            if not 0 <= value <= 255:
                raise ValueError("Data must be an 8-bit unsigned value")

            if not 0 <= address <= 7:
                raise ValueError("SBI address must be between 0 and 7")

            dut = self.dut

            assert int(dut.cmd_valid.value) == 0

            dut.cmd_opcode.value = opcode
            dut.cmd_addr.value = address
            dut.cmd_data.value = value
            dut.cmd_valid.value = 1

            await with_timeout(
                RisingEdge(dut.cmd_done),
                20,
                "us"
            )

            await Timer(1, unit="ns")
            assert int(dut.cmd_busy.value) == 0

            dut.cmd_valid.value = 0

            await Timer(1, unit="ns")
            assert int(dut.cmd_done.value) == 0

    async def uart_transmit(self, value):
        await self._execute(self.UART_TX, 0, value)
        self.dut._log.info("UVVM UART verified: 0x%02X", value)

    async def sbi_write(self, address, value):
        await self._execute(self.SBI_WRITE, address, value)
        self.dut._log.info(
            "UVVM SBI write completed: address=%d, value=0x%02X",
            address, value
        )

    async def sbi_check(self, address, expected):
        await self._execute(self.SBI_CHECK, address, expected)
        self.dut._log.info(
            "UVVM SBI check completed: address=%d, expected=0x%02X",
            address, expected
        )

    async def uart_expect(self, value):
        """Queue a UART receive expectation; do not wait for reception."""
        await self._execute(self.UART_EXPECT, 0, value)
        self.dut._log.info(
            "UVVM UART expectation queued: 0x%02X", value
        )

    async def sbi_write_raw(self, address, value):
        """Perform an SBI write without additional UART verification."""
        await self._execute(self.SBI_WRITE_RAW, address, value)

    async def await_uart_rx(self):
        """Wait until queued UVVM UART RX operations finish."""
        await self._execute(self.AWAIT_UART_RX, 0, 0)

    async def noop(self):
        """Execute an empty Python-to-VHDL command handshake."""
        await self._execute(self.NOOP, 0, 0)
