"""Each test runs in a fresh simulator because protocol faults are permanent."""
import os

import cocotb
from cocotb.triggers import ReadOnly, RisingEdge, Timer, with_timeout
from cocotb.utils import get_sim_time

from cosim.command_transport import UVVMVerificationError
from cosim.generic_controller import GenericController, ProtocolError
from test_generic_vvc import physical_writes


async def ready(dut):
    # Initialize the request before the bridge starts accepting commands.
    dut.cmd_valid.value = 0
    if dut.cmd_ready.value != 1:
        await with_timeout(RisingEdge(dut.cmd_ready), 2, "us")
    await Timer(1, unit="ns")


def request(dut, data=123):
    dut.cmd_vvc_type.value = 1
    dut.cmd_instance.value = 1
    dut.cmd_operation.value = 1
    dut.cmd_addr.value = 900
    dut.cmd_data.value = data
    dut.cmd_valid.value = 1


async def response(dut, expected):
    await with_timeout(RisingEdge(dut.cmd_done), 2, "us")
    await ReadOnly()
    assert int(dut.cmd_status.value) == expected
    assert int(dut.cmd_busy.value) == 0
    await Timer(1, unit="ps")


async def assert_fault_latched(dut):
    dut.cmd_valid.value = 0
    await Timer(2, unit="ns")
    before = physical_writes(dut)
    request(dut, 456)
    await response(dut, 3)
    dut.cmd_valid.value = 0
    await Timer(20, unit="ns")
    assert physical_writes(dut) == before


@cocotb.test()
async def early_withdrawal(dut):
    await ready(dut)
    request(dut)
    await RisingEdge(dut.cmd_busy)
    await Timer(1, unit="ns")
    dut.cmd_valid.value = 0
    await response(dut, 3)
    # The error response remains observable even though valid is already low.
    assert int(dut.cmd_done.value) == 1
    await Timer(2, unit="ns")
    assert int(dut.cmd_done.value) == 0
    await assert_fault_latched(dut)


@cocotb.test()
async def unknown_payload(dut):
    await ready(dut)
    before = physical_writes(dut)
    field = os.environ.get("MALFORMED_FIELD", "cmd_data")
    request(dut)
    signal = getattr(dut, field)
    signal.value = "X" * len(signal)
    await response(dut, 3)
    assert physical_writes(dut) == before
    await assert_fault_latched(dut)


@cocotb.test()
async def changed_payload(dut):
    await ready(dut)
    request(dut)
    await RisingEdge(dut.cmd_busy)
    await Timer(1, unit="ns")
    dut.cmd_data.value = 456
    await response(dut, 3)
    await assert_fault_latched(dut)


@cocotb.test()
async def alert_severity(dut):
    controller = GenericController(dut)
    await controller.sbi_write(1, 5, 55)
    severity = os.environ["CHECK_SEVERITY"]
    error_type = ProtocolError if severity == "TB_FAILURE" else UVVMVerificationError
    try:
        await controller.sbi_check(1, 5, 66)
    except error_type:
        assert int(dut.cmd_status.value) == (3 if severity == "TB_FAILURE" else 1)
    else:
        assert False, f"{severity} was not propagated"
    if severity == "TB_FAILURE":
        assert controller._faulted
        await assert_fault_latched(dut)
    else:
        assert not controller._faulted
        await controller.sbi_check(1, 5, 55)


@cocotb.test()
async def readiness_timeout(dut):
    controller = GenericController(dut, timeout_us=0.001)
    started = get_sim_time(unit="ns")
    try:
        await controller.sbi_write(1, 0, 0)
    except TimeoutError:
        assert get_sim_time(unit="ns") - started == 1
    else:
        assert False, "Initialization should exceed the readiness budget"
    assert controller._faulted
    assert int(dut.cmd_valid.value) == 0


@cocotb.test()
async def separate_timeout_budgets(dut):
    # Wait 15 ns for initialization, then a write plus cleanup.
    # The total exceeds 20 ns, but each documented phase fits its own budget.
    controller = GenericController(dut, timeout_us=0.020)
    await Timer(85, unit="ns")
    started = get_sim_time(unit="ns")
    await controller.sbi_write(1, 901, 123)
    assert get_sim_time(unit="ns") - started > 20
    assert not controller._faulted


@cocotb.test()
async def lock_wait_excluded(dut):
    controller = GenericController(dut, timeout_us=0.020)
    await ready(dut)
    await controller._lock.acquire()
    started = get_sim_time(unit="ns")
    task = cocotb.start_soon(controller.sbi_write(1, 902, 123))
    await Timer(30, unit="ns")
    assert not task.done()
    assert int(dut.cmd_valid.value) == 0
    controller._lock.release()
    await task
    assert get_sim_time(unit="ns") - started > 30
    assert not controller._faulted
