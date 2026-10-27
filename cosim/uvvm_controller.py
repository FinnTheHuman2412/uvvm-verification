from cocotb.triggers import Timer, RisingEdge, with_timeout


class UVVMController:
    def __init__(self, dut):
        self.dut = dut
        self.dut.cmd_valid.value = 0
        self.dut.cmd_data.value = 0

    async def uart_transmit(self, value):
        if not 0 <= value <= 255:
            raise ValueError("UART data must be an 8-bit unsigned value")

        dut = self.dut

        assert int(dut.cmd_valid.value) == 0

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

        dut._log.info("UVVM UART verified: 0x%02X", value)
