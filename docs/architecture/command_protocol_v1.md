# Python–UVVM Command Protocol v1

Status: Implemented for synchronous SBI WRITE and CHECK.

## Objective

Provide a reusable command interface between Python/cocotb
and multiple UVVM Verification Components (VVCs).

## Command interface

| Signal | Width | Description |
|---|---:|---|
| cmd_valid | 1 | Python presents a command |
| cmd_ready | 1 | Bridge initialization complete |
| cmd_vvc_type | 4 | Target VVC type |
| cmd_instance | 8 | Target VVC instance |
| cmd_operation | 8 | Requested VVC operation |
| cmd_addr | 16 | Address argument |
| cmd_data | 32 | Data argument |
| cmd_busy | 1 | Command being processed |
| cmd_done | 1 | Command response available |
| cmd_status | 2 | Command result |

## Initial VVC support

- SBI VVC, instance 1
- SBI VVC, instance 2

## Completion semantics

A command is held valid until the bridge acknowledges
completion through cmd_done.

For synchronous operations, cmd_done indicates that
the requested VVC operation has completed.

Asynchronous operations are outside the initial v1 scope.

## Result status

- 00: Success
- 01: Verification failure
- 10: Unsupported command or target
- 11: Internal protocol error

## Initial requirements

R1: Support two independently addressable SBI VVC instances.
R2: Preserve command ordering.
R3: Return a response for every accepted command.
R4: Detect unsupported targets and operations.
R5: Propagate UVVM verification failures.
R6: Preserve compatibility with the existing regression suite.

## Limitations

- Fixed-width command arguments.
- One outstanding Python command at a time.
- No variable-length payloads.
- No asynchronous result retrieval.
- No generic VVC support beyond the implemented adapters.

## v1 encodings and implementation contract

- `cmd_vvc_type = 1`: SBI. All other types are unsupported.
- `cmd_instance = 1` or `2`: independent SBI target interfaces.
- `cmd_operation = 1`: WRITE; `2`: CHECK. Other operations are unsupported.
- Addresses and data use the full 16-bit and 32-bit unsigned ranges.
  The generic test harness provides two independent zero-initialized register
  banks, each containing 65536 words. No read-result signal exists in v1.
- Python waits for `cmd_ready` before presenting commands. Ready stays high
  after UVVM initialization and target setup; it is not per-command backpressure.
- Only one controller may own a bridge. Concurrent calls through that controller
  serialize under the transport lock. Payload and valid stay stable until done.
- Busy rises on acceptance. Done rises with busy low and stable status only after
  VVC completion (or an error response). Done remains high until valid falls;
  the sender waits for done to clear before issuing another command. If valid
  was withdrawn early, the error response pulses done for 1 ns.
- Unsupported routing returns `10` without VVC dispatch. UVVM ERROR/FAILURE
  counter increases return `01`; subsequent successful checks can return `00`.
- Unknown payload bits, observed payload changes/early valid withdrawal, and
  UVVM TB_ERROR/TB_FAILURE (including completion timeout) return `11`.
  Contract violations and internal VVC errors fault the bridge until simulation
  restart. Payload stability is checked at completion, not continuously monitored.
- The harness uses `G_CHECK_ALERT_LEVEL` (default ERROR) for SBI check
  mismatches; the severity tests override it to FAILURE or TB_FAILURE.
- The VVC completion timeout is `G_COMMAND_TIMEOUT_NS` (default 1000 ns).
  A timeout does not cancel an already queued VVC operation; the bridge rejects
  further dispatch to prevent unsafe reuse. Python's `timeout_us` (default 20 us)
  applies separately to readiness waiting and to the wait for done after dispatch.
  Time queued on the controller lock is excluded. Successful handshake cleanup
  adds 2 ns. This preserves the existing CommandTransport timing contract; it is
  not a total call deadline. Timeout or cancellation while waiting for readiness
  or executing a command faults the controller and requires simulation restart.
  Cancellation while only queued for the transport lock does not fault it.

```python
from cosim.generic_controller import GenericController
controller = GenericController(dut)
await controller.sbi_write(2, 0x1234, 0xDEADBEEF)
await controller.sbi_check(2, 0x1234, 0xDEADBEEF)
```

Run `make test-generic` in the `uvvm` Conda environment. This runs functional tests and isolated
malformed-command, alert-severity, and timeout tests. Logs are written to
`build/generic_*.log`.
The legacy UART/SBI harness and schema-v0 API remain separate and unchanged.
