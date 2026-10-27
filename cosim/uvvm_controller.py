from cocotb.triggers import Timer, RisingEdge, with_timeout


class UVVMController:
    UART_TX = 0
    SBI_WRITE = 1

    def __init__(self, dut):
        self.dut = dut

        dut.cmd_valid.value = 0
        dut.cmd_opcode.value = 0
        dut.cmd_addr.value = 0
        dut.cmd_data.value = 0

    async def _execute(self, opcode, address, value):
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
