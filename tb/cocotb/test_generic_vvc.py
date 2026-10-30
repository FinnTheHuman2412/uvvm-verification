import cocotb
from cocotb.triggers import Timer, RisingEdge, ReadOnly, with_timeout
from cosim.generic_controller import GenericController, UnsupportedCommandError
from cosim.command_transport import UVVMVerificationError


@cocotb.test()
async def startup(dut):
    controller = GenericController(dut)
    await controller.sbi_write(1, 0xFFFF, 0xDEADBEEF)
    await controller.sbi_check(1, 0xFFFF, 0xDEADBEEF)
    assert int(dut.cmd_ready.value) == 1


def physical_writes(dut):
    return tuple((int(getattr(dut, f"target{i}_write_count").value),
                  int(getattr(dut, f"target{i}_last_addr").value),
                  int(getattr(dut, f"target{i}_last_data").value)) for i in (1, 2))


async def assert_write_at_done(dut, instance, address, data, before):
    await with_timeout(RisingEdge(dut.cmd_done), 2, "us")
    await ReadOnly()
    assert int(dut.cmd_busy.value) == 0
    assert int(dut.cmd_status.value) == 0
    assert int(dut.target1_active.value) == 0
    assert int(dut.target2_active.value) == 0
    actual = physical_writes(dut)
    assert actual[instance - 1] == (before[instance - 1][0] + 1, address, data)
    assert actual[2 - instance] == before[2 - instance]
    # Return outside the read-only phase so callers may drive the next request.
    await Timer(1, unit="ps")


async def assert_check_at_done(dut, before, status=0):
    await with_timeout(RisingEdge(dut.cmd_done), 2, "us")
    await ReadOnly()
    assert int(dut.cmd_busy.value) == 0
    assert int(dut.cmd_status.value) == status
    assert int(dut.target1_active.value) == 0
    assert int(dut.target2_active.value) == 0
    assert physical_writes(dut) == before
    await Timer(1, unit="ps")


@cocotb.test()
async def independent_instances(dut):
    controller = GenericController(dut)
    await Timer(1, unit="ns")
    for instance, value in [(1, 0x12345678), (2, 0x87654321)]:
        observed = cocotb.start_soon(assert_write_at_done(
            dut, instance, 1234, value, physical_writes(dut)))
        await controller.sbi_write(instance, 1234, value)
        await observed
    for instance, value in [(1, 0x12345678), (2, 0x87654321)]:
        observed = cocotb.start_soon(assert_check_at_done(dut, physical_writes(dut)))
        await controller.sbi_check(instance, 1234, value)
        await observed


@cocotb.test()
async def invalid_commands(dut):
    controller = GenericController(dut)
    await controller.sbi_write(1, 42, 99)
    before = physical_writes(dut)
    for target, instance, operation in [(0, 1, 1), (15, 1, 1), (1, 0, 1),
                                        (1, 3, 1), (1, 255, 1), (1, 1, 0), (1, 2, 255)]:
        try:
            await controller.execute(target, instance, operation, 42, 123)
        except UnsupportedCommandError:
            assert int(dut.cmd_status.value) == 2
        else:
            assert False, "Unsupported command accepted"
        assert not controller._faulted
        # Allow a wrongly queued physical write time to become observable.
        await Timer(20, unit="ns")
        assert physical_writes(dut) == before
    await controller.sbi_check(1, 42, 99)
    for args in [(16, 1, 1, 0, 0), (1, 256, 1, 0, 0), (1, 1, 256, 0, 0),
                 (1, 1, 1, 65536, 0), (1, 1, 1, 0, 2**32)]:
        try:
            await controller.execute(*args)
        except ValueError:
            pass
        else:
            assert False, "Out-of-range field accepted"


@cocotb.test()
async def ordering(dut):
    controller = GenericController(dut)
    await controller.sbi_write(1, 77, 0)
    await controller.sbi_write(2, 77, 0)
    expected = [(i % 2 + 1, 77, i + 100) for i in range(20)]
    actual = []

    async def monitor():
        previous = physical_writes(dut)
        while len(actual) < len(expected):
            await RisingEdge(dut.clk)
            await ReadOnly()
            current = physical_writes(dut)
            for i in (0, 1):
                if current[i][0] != previous[i][0]:
                    assert current[i][0] == previous[i][0] + 1
                    actual.append((i + 1, current[i][1], current[i][2]))
            previous = current

    observer = cocotb.start_soon(monitor())
    tasks = []
    # Establish invocation order explicitly while calls overlap on the lock.
    for instance, address, data in expected:
        tasks.append(cocotb.start_soon(controller.sbi_write(instance, address, data)))
        await Timer(1, unit="ps")
    for task in tasks:
        await task
    await with_timeout(observer, 2, "us")
    assert actual == expected, (actual, expected)
    await controller.sbi_check(1, 77, 118)
    await controller.sbi_check(2, 77, 119)


@cocotb.test()
async def verification_failure(dut):
    controller = GenericController(dut)
    for instance in (1, 2):
        await controller.sbi_write(instance, 5, 55)
        observed = cocotb.start_soon(assert_check_at_done(dut, physical_writes(dut), 1))
        try:
            await controller.sbi_check(instance, 5, 66)
        except UVVMVerificationError:
            assert int(dut.cmd_status.value) == 1
        else:
            assert False, "Mismatch did not reach Python"
        await observed
        assert not controller._faulted
        observed = cocotb.start_soon(assert_check_at_done(dut, physical_writes(dut)))
        await controller.sbi_check(instance, 5, 55)
        await observed
        assert int(dut.cmd_status.value) == 0


@cocotb.test()
async def held_completion(dut):
    controller = GenericController(dut)
    await controller.sbi_write(1, 8, 8)
    before = physical_writes(dut)
    observed = cocotb.start_soon(assert_write_at_done(dut, 2, 8, 88, before))
    dut.cmd_vvc_type.value = 1
    dut.cmd_instance.value = 2
    dut.cmd_operation.value = 1
    dut.cmd_addr.value = 8
    dut.cmd_data.value = 88
    dut.cmd_valid.value = 1
    await with_timeout(RisingEdge(dut.cmd_done), 2, "us")
    await observed
    await Timer(100, unit="ns")
    assert int(dut.cmd_done.value) == 1
    assert int(dut.cmd_busy.value) == 0
    assert int(dut.cmd_status.value) == 0
    dut.cmd_valid.value = 0
    await Timer(1, unit="ns")
    await controller.sbi_check(2, 8, 88)


@cocotb.test()
async def timeout_and_internal_error(dut):
    controller = GenericController(dut, timeout_us=0.001)
    try:
        await controller.sbi_write(1, 0, 0)
    except TimeoutError:
        pass
    else:
        assert False, "Expected Python timeout"
    assert controller._faulted
    # Violate the held-payload contract while the accepted command runs.
    dut.cmd_data.value = 1
    await with_timeout(RisingEdge(dut.cmd_done), 2, "us")
    await Timer(1, unit="ns")
    assert int(dut.cmd_status.value) == 3
    dut.cmd_valid.value = 0
    await Timer(1, unit="ns")
    try:
        await controller.sbi_write(1, 0, 0)
    except RuntimeError as exc:
        assert "faulted" in str(exc)
    else:
        assert False, "Faulted controller accepted a command"
