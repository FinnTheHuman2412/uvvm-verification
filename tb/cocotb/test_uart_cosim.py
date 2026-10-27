import cocotb
from cocotb.triggers import Timer

from cosim.uvvm_controller import UVVMController


@cocotb.test()
async def test_multiple_python_uvvm_commands(dut):
    uvvm = UVVMController(dut)

    await Timer(500, unit="ns")

    test_values = [0xA5, 0x55, 0xAA, 0x00, 0xFF]

    for value in test_values:
        await uvvm.uart_transmit(value)

    dut._log.info(
        "All %d UART transactions verified",
        len(test_values)
    )


@cocotb.test()
async def test_python_sbi_write(dut):
    uvvm = UVVMController(dut)

    await Timer(500, unit="ns")

    await uvvm.sbi_write(address=2, value=0x55)

    dut._log.info("SBI-to-UART verification completed")
